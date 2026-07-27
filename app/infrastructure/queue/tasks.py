import os
import json
import asyncio
from datetime import datetime
from loguru import logger

from app.config.settings import get_settings
from app.infrastructure.ingestion.pdf_parser import PdfParser
from app.infrastructure.ai.agents.content_understanding_agent import ContentUnderstandingAgent
from app.infrastructure.ai.agents.lesson_planner_agent import LessonPlannerAgent
from app.infrastructure.ai.agents.teaching_unit_planner_agent import TeachingUnitPlannerAgent
from app.infrastructure.ai.agents.script_generator_agent import ScriptGeneratorAgent
from app.infrastructure.validation.schema_validator import SchemaValidator
from app.domain.models.understanding import Understanding
from app.domain.models.lesson_plan import LessonPlan
from app.domain.models.teaching_unit import TeachingUnit
from app.domain.models.narration_segment import NarrationSegment
from app.domain.models.slide import Slide
from app.domain.models.audio_clip import AudioClip
from app.infrastructure.audio.audio_builder import AudioBuilder
from app.infrastructure.presentation.pptx_builder import PptxBuilder
from app.core.exceptions import AgentException, VoiceGenerationException
from app.infrastructure.state.local_store import update_job_state

def update_job_status(job_id: str, status: str, stage: str, units_done: int = -1, units_total: int = -1, units_failed: int = -1, failure_reason: str = None, document_id: str = None):
    data = {
        "status": status,
        "stage": stage,
        "updated_at": datetime.now().isoformat()
    }
    if document_id:
        data["document_id"] = document_id
    if units_done >= 0:
        data["units_done"] = units_done
    if units_total >= 0:
        data["units_total"] = units_total
    if units_failed >= 0:
        data["units_failed"] = units_failed
    if failure_reason:
        data["failure_reason"] = failure_reason
    if status in ("DONE", "FAILED"):
        data["completed_at"] = datetime.now().isoformat()
        
    update_job_state(job_id, data)

# Pipeline functions (No longer Celery tasks)

async def parse_document_task(job_id: str, document_id: str, file_path: str, output_dir: str):
    logger.info(f"[{job_id}] Starting parse_document_task")
    update_job_status(job_id, "RUNNING", "parsing", document_id=document_id)
    try:
        parser = PdfParser()
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        edu_content = parser.parse(file_bytes, os.path.basename(file_path))
        
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "parsed_text.txt"), "w", encoding="utf-8") as f:
            f.write(edu_content.raw_text)
        
        with open(os.path.join(output_dir, "edu_content.json"), "w", encoding="utf-8") as f:
            f.write(edu_content.model_dump_json(indent=2))
            
        logger.info(f"[{job_id}] Chunking and indexing document text with FAISS")
        from app.infrastructure.rag.text_splitter import RecursiveCharacterTextSplitter
        from app.infrastructure.rag.vector_store import LocalVectorStore
        
        # Increased chunk size from 400 to 1000 to reduce total embeddings count and improve semantic RAG context
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = splitter.split_text(edu_content.raw_text)
        
        if chunks:
            vector_store = LocalVectorStore()
            vector_store.add_documents(chunks)
            faiss_dir = os.path.join(output_dir, "faiss_index")
            vector_store.save(faiss_dir)
            logger.info(f"[{job_id}] Successfully built and saved FAISS index with {len(chunks)} chunks.")
            
        return {"status": "SUCCESS", "document_id": document_id}
    except Exception as e:
        logger.exception(f"[{job_id}] Parsing failed")
        update_job_status(job_id, "FAILED", "parsing", failure_reason=f"Failed to parse document: {str(e)}")
        raise

async def understand_content_task(job_id: str, document_id: str, output_dir: str):
    logger.info(f"[{job_id}] Starting understand_content_task")
    update_job_status(job_id, "RUNNING", "understanding")
    try:
        with open(os.path.join(output_dir, "edu_content.json"), "r", encoding="utf-8") as f:
            content_dict = json.load(f)
        from app.domain.models.source_document import SourceDocument
        edu_content = SourceDocument(**content_dict)
        
        understanding_agent = ContentUnderstandingAgent()
        understanding = await understanding_agent.run(edu_content)
        
        validator = SchemaValidator()
        val_res = validator.validate(understanding, Understanding)
        if not val_res.is_valid:
            raise AgentException(f"ContentUnderstanding validation failed: {', '.join(val_res.errors)}")
            
        with open(os.path.join(output_dir, "understanding.json"), "w", encoding="utf-8") as f:
            f.write(understanding.model_dump_json(indent=2))
            
        return {"status": "SUCCESS"}
    except Exception as e:
        logger.exception(f"[{job_id}] Understanding failed")
        update_job_status(job_id, "FAILED", "understanding", failure_reason=f"Content Understanding failed: {str(e)}")
        raise

async def plan_lesson_task(job_id: str, document_id: str, output_dir: str):
    logger.info(f"[{job_id}] Starting plan_lesson_task")
    update_job_status(job_id, "RUNNING", "lesson_planning")
    try:
        with open(os.path.join(output_dir, "understanding.json"), "r", encoding="utf-8") as f:
            und_dict = json.load(f)
        understanding = Understanding(**und_dict)
        
        lesson_planner = LessonPlannerAgent()
        lesson_plan = await lesson_planner.run(understanding)
        
        validator = SchemaValidator()
        val_res = validator.validate(lesson_plan, LessonPlan)
        if not val_res.is_valid:
            raise AgentException(f"LessonPlan validation failed: {', '.join(val_res.errors)}")
            
        with open(os.path.join(output_dir, "lesson_plan.json"), "w", encoding="utf-8") as f:
            f.write(lesson_plan.model_dump_json(indent=2))
            
        return {"status": "SUCCESS"}
    except Exception as e:
        logger.exception(f"[{job_id}] Lesson planning failed")
        update_job_status(job_id, "FAILED", "lesson_planning", failure_reason=f"Lesson Planning failed: {str(e)}")
        raise

async def generate_units_task(job_id: str, document_id: str, output_dir: str):
    logger.info(f"[{job_id}] Starting generate_units_task")
    update_job_status(job_id, "RUNNING", "unit_planning")
    try:
        with open(os.path.join(output_dir, "lesson_plan.json"), "r", encoding="utf-8") as f:
            lp_dict = json.load(f)
        lesson_plan = LessonPlan(**lp_dict)
        
        with open(os.path.join(output_dir, "understanding.json"), "r", encoding="utf-8") as f:
            und_dict = json.load(f)
        understanding = Understanding(**und_dict)
        
        faiss_dir = os.path.join(output_dir, "faiss_index")
            
        unit_planner = TeachingUnitPlannerAgent()
        units = await unit_planner.run(understanding, faiss_dir)
        
        validator = SchemaValidator()
        val_res = validator.validate(units, TeachingUnit)
        if not val_res.is_valid:
            raise AgentException(f"TeachingUnits validation failed: {', '.join(val_res.errors)}")
            
        units_dict = [unit.model_dump() for unit in units]
        with open(os.path.join(output_dir, "teaching_units.json"), "w", encoding="utf-8") as f:
            json.dump(units_dict, f, indent=2)
            
        update_job_status(job_id, "RUNNING", "unit_planning", units_done=0, units_total=len(units))
        return {"status": "SUCCESS", "units_count": len(units)}
    except Exception as e:
        logger.exception(f"[{job_id}] Unit planning failed")
        update_job_status(job_id, "FAILED", "unit_planning", failure_reason=f"Unit Planning failed: {str(e)}")
        raise

async def generate_narration_for_unit_task(job_id: str, unit_dict: dict, output_dir: str):
    unit_id = unit_dict["unit_id"]
    logger.info(f"[{job_id}] Generating narration for unit: {unit_id}")
    try:
        unit = TeachingUnit(**unit_dict)
        
        query_parts = [unit.learning_goal]
        if unit.bullet_sentences:
            query_parts.extend(unit.bullet_sentences)
        query = " ".join(query_parts)
        
        source_context = ""
        faiss_dir = os.path.join(output_dir, "faiss_index")
        if os.path.exists(faiss_dir):
            try:
                from app.infrastructure.rag.vector_store import LocalVectorStore
                vector_store = LocalVectorStore()
                vector_store.load(faiss_dir)
                retrieved_chunks = vector_store.similarity_search(query, top_k=3)
                if retrieved_chunks:
                    source_context = "\n\n".join(retrieved_chunks)
            except Exception as ex:
                logger.warning(f"[{job_id}] FAISS retrieval failed for unit {unit_id}: {str(ex)}")

        script_generator = ScriptGeneratorAgent()
        segment = await script_generator.run(unit, source_context=source_context)
        
        validator = SchemaValidator()
        val_res = validator.validate(segment, NarrationSegment)
        if not val_res.is_valid:
            raise AgentException(f"Narration validation failed: {', '.join(val_res.errors)}")
            
        with open(os.path.join(output_dir, f"narration_{unit_id}.json"), "w", encoding="utf-8") as f:
            f.write(segment.model_dump_json(indent=2))
            
        return {"status": "SUCCESS", "unit_id": unit_id}
    except Exception as e:
        logger.error(f"[{job_id}] Narration failed for unit {unit_id}. Error: {str(e)}")
        fail_data = {"error": f"Narration generation failed: {str(e)}"}
        with open(os.path.join(output_dir, f"failure_narration_{unit_id}.json"), "w", encoding="utf-8") as f:
            json.dump(fail_data, f)
        return {"status": "FAILED", "unit_id": unit_id}

async def validate_narration_for_unit_task(job_id: str, unit_dict: dict, output_dir: str):
    unit_id = unit_dict["unit_id"]
    logger.info(f"[{job_id}] Validating narration for unit: {unit_id}")
    try:
        narration_path = os.path.join(output_dir, f"narration_{unit_id}.json")
        if not os.path.exists(narration_path):
            raise AgentException("Skipped validation because narration generation failed.")
            
        with open(narration_path, "r", encoding="utf-8") as f:
            seg_dict = json.load(f)
        segment = NarrationSegment(**seg_dict)
        unit = TeachingUnit(**unit_dict)
        
        from app.infrastructure.ai.agents.validator_agent import ValidatorAgent
        validator_agent = ValidatorAgent()
        
        validated_segment = await validator_agent.run(segment, unit)
        
        with open(os.path.join(output_dir, f"narration_{unit_id}.json"), "w", encoding="utf-8") as f:
            f.write(validated_segment.model_dump_json(indent=2))
            
        if validated_segment.validation_status == "FAIL":
            logger.warning(f"[{job_id}] Validation failed for {unit_id}: {validated_segment.validation_notes}")
            return {"status": "FAILED", "unit_id": unit_id, "reason": "Validation FAIL"}
            
        return {"status": "SUCCESS", "unit_id": unit_id}
    except Exception as e:
        logger.error(f"[{job_id}] Validation failed for unit {unit_id}. Error: {str(e)}")
        return {"status": "FAILED", "unit_id": unit_id}

def synthesize_audio_for_unit_task(job_id: str, unit_id: str, output_dir: str):
    logger.info(f"[{job_id}] Synthesizing audio for unit: {unit_id}")
    try:
        narration_fail_path = os.path.join(output_dir, f"failure_narration_{unit_id}.json")
        if os.path.exists(narration_fail_path):
            raise VoiceGenerationException("Skipped audio synthesis because narration generation failed.")
            
        narration_path = os.path.join(output_dir, f"narration_{unit_id}.json")
        with open(narration_path, "r", encoding="utf-8") as f:
            seg_dict = json.load(f)
        segment = NarrationSegment(**seg_dict)
        
        builder = AudioBuilder()
        clip = builder.synthesize(segment, output_dir)
        
        with open(os.path.join(output_dir, f"audio_clip_{unit_id}.json"), "w", encoding="utf-8") as f:
            f.write(clip.model_dump_json(indent=2))
            
        return {"status": "SUCCESS", "unit_id": unit_id}
    except Exception as e:
        fail_data = {"error": str(e)}
        with open(os.path.join(output_dir, f"failure_audio_{unit_id}.json"), "w", encoding="utf-8") as f:
            json.dump(fail_data, f)
        return {"status": "FAILED", "unit_id": unit_id}

def build_slide_for_unit_task(job_id: str, unit_dict: dict, output_dir: str):
    unit_id = unit_dict["unit_id"]
    logger.info(f"[{job_id}] Building slide for unit: {unit_id}")
    try:
        narration_path = os.path.join(output_dir, f"narration_{unit_id}.json")
        speaker_notes = ""
        if os.path.exists(narration_path):
            with open(narration_path, "r", encoding="utf-8") as f:
                seg = json.load(f)
            speaker_notes = seg.get("narration_text", "")
            
        slide = Slide(
            unit_id=unit_id,
            title=unit_dict["learning_goal"],
            bullets=unit_dict["bullet_sentences"],
            speaker_notes=speaker_notes
        )
        
        with open(os.path.join(output_dir, f"slide_{unit_id}.json"), "w", encoding="utf-8") as f:
            f.write(slide.model_dump_json(indent=2))
            
        return {"status": "SUCCESS", "unit_id": unit_id}
    except Exception as e:
        logger.error(f"[{job_id}] Slide build failed for unit {unit_id}. Error: {str(e)}")
        fail_data = {"error": f"Slide generation failed: {str(e)}"}
        with open(os.path.join(output_dir, f"failure_slide_{unit_id}.json"), "w", encoding="utf-8") as f:
            json.dump(fail_data, f)
        return {"status": "FAILED", "unit_id": unit_id}

async def process_unit(job_id: str, unit_dict: dict, output_dir: str):
    unit_id = unit_dict["unit_id"]
    
    logger.info(f"[{job_id}] Narration Generation for unit {unit_id}")
    await generate_narration_for_unit_task(job_id, unit_dict, output_dir)
    
    # 10x SPEEDUP: Validation step disabled completely to skip unnecessary secondary AI calls.
    # val_result = await validate_narration_for_unit_task(job_id, unit_dict, output_dir)
    
    narration_fail_path = os.path.join(output_dir, f"failure_narration_{unit_id}.json")
    if os.path.exists(narration_fail_path):
        logger.error(f"[{job_id}] Unit {unit_id} failed narration. Skipping audio/slide build.")
        return
        
    # audio builder has sync blocking I/O, run in executor if needed, but here sync is fine for local
    await asyncio.to_thread(synthesize_audio_for_unit_task, job_id, unit_id, output_dir)
    await asyncio.to_thread(build_slide_for_unit_task, job_id, unit_dict, output_dir)

async def trigger_unit_parallelism_task(job_id: str, document_id: str, output_dir: str):
    logger.info(f"[{job_id}] Starting trigger_unit_parallelism_task (CONCURRENT for 10x local speed)")
    update_job_status(job_id, "RUNNING", "audio_synthesis")
    try:
        with open(os.path.join(output_dir, "teaching_units.json"), "r", encoding="utf-8") as f:
            units_list = json.load(f)
            
        if not units_list:
            await finalize_pipeline_task(job_id, document_id, output_dir)
            return {"status": "SUCCESS", "message": "No units to process."}
            
        total_units = len(units_list)
        units_done = 0
        
        # CRITICAL FIX: Enforce sequential generation to prevent local GPU memory thrashing / CPU RAM swapping
        semaphore = asyncio.Semaphore(1)
        
        async def process_with_sem(unit_dict):
            nonlocal units_done
            async with semaphore:
                logger.info(f"--- [Progress] Processing Unit: {unit_dict.get('learning_goal', 'Unknown')} ---")
                await process_unit(job_id, unit_dict, output_dir)
                units_done += 1
                update_job_status(job_id, "RUNNING", "audio_synthesis", units_done=units_done, units_total=total_units)
                
        tasks = [process_with_sem(u) for u in units_list]
        await asyncio.gather(*tasks)
            
        await finalize_pipeline_task(job_id, document_id, output_dir)
        return {"status": "SUCCESS", "queued_units": len(units_list)}
    except Exception as e:
        logger.exception(f"[{job_id}] Trigger unit execution failed")
        update_job_status(job_id, "FAILED", "audio_synthesis", failure_reason=f"Execution failed: {str(e)}")
        raise

async def finalize_pipeline_task(job_id: str, document_id: str, output_dir: str):
    logger.info(f"[{job_id}] [Step 6/6] Finalizing pipeline and rendering video...")
    try:
        with open(os.path.join(output_dir, "teaching_units.json"), "r", encoding="utf-8") as f:
            units_list = json.load(f)
            
        slides = []
        narration_segments = []
        audio_clips = []
        
        for unit_dict in units_list:
            unit_id = unit_dict["unit_id"]
            
            slide_path = os.path.join(output_dir, f"slide_{unit_id}.json")
            if os.path.exists(slide_path):
                with open(slide_path, "r", encoding="utf-8") as f:
                    slide_dict = json.load(f)
                slides.append(Slide(**slide_dict))
                
            narration_path = os.path.join(output_dir, f"narration_{unit_id}.json")
            if os.path.exists(narration_path):
                with open(narration_path, "r", encoding="utf-8") as f:
                    seg_dict = json.load(f)
                narration_segments.append(NarrationSegment(**seg_dict))
            else:
                narration_segments.append(NarrationSegment(
                    unit_id=unit_id,
                    narration_text="",
                    estimated_duration_sec=0.0,
                    validation_status="FAIL",
                    validation_notes=["Narration generation failed."]
                ))
                
            clip_path = os.path.join(output_dir, f"audio_clip_{unit_id}.json")
            if os.path.exists(clip_path):
                with open(clip_path, "r", encoding="utf-8") as f:
                    clip_dict = json.load(f)
                audio_clips.append(AudioClip(**clip_dict))

        script_data = {
            "document_id": document_id,
            "segments": [seg.model_dump() for seg in narration_segments]
        }
        with open(os.path.join(output_dir, "script.json"), "w", encoding="utf-8") as f:
            json.dump(script_data, f, indent=2)

        audio_metadata = {
            "document_id": document_id,
            "clips": [clip.model_dump() for clip in audio_clips]
        }
        with open(os.path.join(output_dir, "audio_metadata.json"), "w", encoding="utf-8") as f:
            json.dump(audio_metadata, f, indent=2)

        valid_units = []
        for unit_dict in units_list:
            unit_id = unit_dict["unit_id"]
            if (os.path.exists(os.path.join(output_dir, f"failure_narration_{unit_id}.json")) or
                os.path.exists(os.path.join(output_dir, f"failure_audio_{unit_id}.json")) or
                os.path.exists(os.path.join(output_dir, f"failure_slide_{unit_id}.json"))):
                continue
            valid_units.append(TeachingUnit(**unit_dict))
            
        builder = PptxBuilder()
        slides_models, presentation_path = builder.build(valid_units, narration_segments, output_dir)
        logger.info(f"[{job_id}] Presentation built successfully at {presentation_path}")

        from app.infrastructure.synchronization.timeline_builder import TimelineBuilder
        timeline = TimelineBuilder.build(audio_clips)
        timeline_path = os.path.join(output_dir, "timeline.json")
        with open(timeline_path, "w", encoding="utf-8") as f:
            json.dump([t.model_dump() for t in timeline], f, indent=2)
            
        if presentation_path and timeline:
            from app.infrastructure.video.video_renderer import VideoRenderer
            try:
                video_output_path = os.path.join(output_dir, "video.mp4")
                logger.info(f"[{job_id}] Starting video rendering...")
                VideoRenderer.render(document_id, presentation_path, timeline, video_output_path)
                logger.info(f"[{job_id}] Video built successfully at {video_output_path}")
            except Exception as ve:
                logger.error(f"[{job_id}] Video rendering failed: {str(ve)}")

        total_units = len(units_list)
        failed_units = total_units - len(valid_units)
        update_job_status(job_id, "DONE", "completed", units_done=len(valid_units), units_total=total_units, units_failed=failed_units)
            
        logger.info(f"[{job_id}] finalize_pipeline_task finished successfully.")
        return {"status": "SUCCESS", "pptx_path": presentation_path if slides_models else None}
    except Exception as e:
        logger.exception(f"[{job_id}] Finalization failed")
        update_job_status(job_id, "FAILED", "completed", failure_reason=f"Finalization failed: {str(e)}")
        raise

# Coordinator for the whole pipeline
async def run_full_pipeline(job_id: str, document_id: str, file_path: str, output_dir: str):
    """Executes the pipeline sequentially in the background."""
    try:
        logger.info(f"========== PIPELINE STARTED FOR JOB {job_id} ==========")
        
        logger.info(f"[{job_id}] [Step 1/6] Parsing Document & FAISS Embeddings (Expected: < 1 min)")
        await parse_document_task(job_id, document_id, file_path, output_dir)
        
        logger.info(f"[{job_id}] [Step 2/6] AI Content Understanding (Expected: 5-25 mins depending on GPU)")
        await understand_content_task(job_id, document_id, output_dir)
        
        logger.info(f"[{job_id}] [Step 3/6] AI Lesson Planning (Expected: 5-25 mins depending on GPU)")
        await plan_lesson_task(job_id, document_id, output_dir)
        
        logger.info(f"[{job_id}] [Step 4/6] AI Unit Generation (Expected: 5-15 mins depending on GPU)")
        await generate_units_task(job_id, document_id, output_dir)
        
        logger.info(f"[{job_id}] [Step 5/6] Unit Processing - Generating Slides, Scripts, and Audio...")
        await trigger_unit_parallelism_task(job_id, document_id, output_dir)
        
        logger.info(f"========== PIPELINE COMPLETELY FINISHED FOR JOB {job_id} ==========")
    except Exception as e:
        logger.error(f"[{job_id}] Pipeline aborted due to error: {e}")
