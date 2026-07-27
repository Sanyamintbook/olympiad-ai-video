import uuid
from typing import Any
from app.domain.models.understanding import Understanding
from app.domain.models.lesson_plan import LessonPlan
from app.domain.models.teaching_unit import TeachingUnit
from app.infrastructure.ai.agents.base_agent import BaseAgent
from app.infrastructure.ai.providers.base import LLMProvider
from app.infrastructure.ai.prompts.loader import PromptLoader

class TeachingUnitPlannerAgent(BaseAgent):
    """Generates granular teaching units."""

    def __init__(self, provider: LLMProvider | None = None, prompt_loader: PromptLoader | None = None) -> None:
        super().__init__(provider=provider, prompt_loader=prompt_loader)

    async def run(self, understanding: Understanding, faiss_dir: str) -> list[TeachingUnit]:
        from app.infrastructure.rag.vector_store import LocalVectorStore
        
        # INFINITE SCALING: Instead of parsing raw_text, we load the FAISS vector store.
        # This allows us to query the exact paragraphs needed for each slide batch, 
        # completely preventing GPU OOM regardless of document size.
        vector_store = LocalVectorStore()
        try:
            vector_store.load(faiss_dir)
            has_faiss = True
        except Exception as e:
            self.logger.warning(f"Failed to load FAISS index from {faiss_dir}: {e}. Slide generation will lack source context.")
            has_faiss = False
            
        units = []
        
        # Define the strict schema for a BATCH of units
        schema = {
            "type": "object",
            "properties": {
                "units": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "learning_goal": {"type": "string"},
                            "bullet_sentences": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "source_refs": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["learning_goal", "bullet_sentences"]
                    }
                }
            },
            "required": ["units"]
        }
        
        def extract_fuzzy_key(data_dict, possible_keys, default_val=None):
            if not isinstance(data_dict, dict): return default_val
            for k in data_dict.keys():
                for pk in possible_keys:
                    if pk.lower() in k.lower().replace("_", "").replace(" ", ""):
                        return data_dict[k]
            return default_val
            
        def validate_batch(res):
            # ADVANCED AI REPAIR: If the AI hallucinates and returns a raw list of strings,
            # or a list of lists, we will manually reconstruct it into the required JSON object
            if isinstance(res, list):
                if len(res) > 0 and isinstance(res[0], dict):
                    res = {"units": res}
                else:
                    raise ValueError("Output is an array but not an array of objects.")
            if not isinstance(res, dict):
                raise ValueError(f"Expected dict but got {type(res)}")
                
            if "units" in res and isinstance(res["units"], list) and len(res["units"]) == 0:
                raise ValueError("The AI returned an empty 'units' array. It must return exactly the requested number of units.")
                
            if "units" not in res:
                # Fallback 1: The AI returned a single slide object directly
                if extract_fuzzy_key(res, ["learninggoal", "title"]) and extract_fuzzy_key(res, ["bulletsentences", "bullet", "points"]):
                    res = {"units": [res]}
                else:
                    # Fallback 2: The AI returned a list of slides under a different key name
                    extracted_list = []
                    for val in res.values():
                        if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict) and extract_fuzzy_key(val[0], ["learninggoal", "title"]):
                            extracted_list = val
                            break
                    if extracted_list:
                        res = {"units": extracted_list}
                    else:
                        # Fallback 3: The AI returned a dictionary of dictionaries (e.g. {"unit1": {...}})
                        dict_list = [v for v in res.values() if isinstance(v, dict) and extract_fuzzy_key(v, ["learninggoal", "title"])]
                        if dict_list:
                            res = {"units": dict_list}
                        else:
                            if "error" in res:
                                self.logger.warning(f"AI generation format mismatch, automatically retrying...")
                                raise ValueError(f"AI hallucinated an error: {res['error']}")
                            else:
                                raise ValueError("Missing 'units' array in the generated JSON.")
            return res
                
        self.logger.info(f"Generating slides in BATCHES for {len(understanding.subtopics)} extracted subtopics...")
        
        import asyncio
        import json
        
        # We process batches sequentially to protect local GPU VRAM from thrashing
        semaphore = asyncio.Semaphore(1)
        batch_size = 5
        
        # Slice subtopics into batches of 5
        subtopic_batches = [understanding.subtopics[i:i + batch_size] for i in range(0, len(understanding.subtopics), batch_size)]
        
        async def generate_batch(batch_idx, subtopics_batch):
            async with semaphore:
                # INFINITE SCALING: Dynamic Context Retrieval (RAG)
                # Instead of dumping the entire book into the prompt, we ask FAISS to find
                # the 8 most relevant paragraphs for this specific batch of slides.
                batch_query = f"{understanding.main_topic} " + " ".join(subtopics_batch)
                retrieved_context = ""
                if has_faiss:
                    try:
                        chunks = vector_store.similarity_search(batch_query, top_k=8)
                        retrieved_context = "\n\n".join(chunks)
                    except Exception as e:
                        self.logger.warning(f"FAISS retrieval failed for batch {batch_idx+1}: {e}")
                
                context = {
                    "subtopics_json": json.dumps(subtopics_batch),
                    "batch_size": len(subtopics_batch),
                    "main_topic": understanding.main_topic,
                    "definitions": understanding.definitions,
                    "examples": understanding.examples,
                    "raw_text": retrieved_context
                }
                
                try:
                    self.logger.info(f"Generating slide BATCH {batch_idx+1}/{len(subtopic_batches)} (Contains {len(subtopics_batch)} slides)...")
                    result_dict = await self.generate_structured(
                        "teaching_unit_planner", 
                        schema=schema, 
                        context=context, 
                        validator=validate_batch
                    )
                    
                    if result_dict.get("FORCE_FALLBACK"):
                        self.logger.warning(f"Instant fallback triggered for slide batch {batch_idx+1}.")
                        fallback_units = []
                        for j, sub_title in enumerate(subtopics_batch):
                            unit = TeachingUnit(
                                unit_id=str(uuid.uuid4()),
                                lesson_id=understanding.main_topic,
                                order=(batch_idx * batch_size) + j + 1,
                                learning_goal=f"{understanding.main_topic} - {sub_title}",
                                bullet_sentences=[
                                    f"Detailed analysis of {sub_title}.",
                                    f"Key concepts regarding {sub_title}.",
                                    "Refer to the source text for detailed information."
                                ],
                                source_refs=["Programmatic Fallback Synthesis"]
                            )
                            fallback_units.append(unit)
                        return fallback_units
                        
                    batch_units = []
                    generated_units = result_dict.get("units", [])
                    
                    for j, u_data in enumerate(generated_units):
                        bullets = extract_fuzzy_key(u_data, ["bulletsentences", "bullet", "points", "sentences"], [])
                        if len(bullets) > 6:
                            bullets = bullets[:6]
                        while len(bullets) < 3:
                            if bullets:
                                bullets.append(bullets[-1])
                            else:
                                bullets.append("Detailed analysis of this topic.")
                                
                        refs = extract_fuzzy_key(u_data, ["sourcerefs", "source", "refs", "references"], [])
                        if not refs:
                            refs = ["Raw Textbook Text"]
                                
                        unit = TeachingUnit(
                            unit_id=str(uuid.uuid4()),
                            lesson_id=understanding.main_topic,
                            order=(batch_idx * batch_size) + j + 1,
                            learning_goal=extract_fuzzy_key(u_data, ["learninggoal", "title", "heading", "goal"], "Goal"),
                            bullet_sentences=bullets,
                            source_refs=refs
                        )
                        batch_units.append(unit)
                        
                    return batch_units
                except Exception as e:
                    self.logger.warning(f"Failed to generate slide batch {batch_idx+1} after all retries: {e}. Falling back to programmatic synthesis.")
                    fallback_units = []
                    for j, sub_title in enumerate(subtopics_batch):
                        unit = TeachingUnit(
                            unit_id=str(uuid.uuid4()),
                            lesson_id=understanding.main_topic,
                            order=(batch_idx * batch_size) + j + 1,
                            learning_goal=f"{understanding.main_topic} - {sub_title}",
                            bullet_sentences=[
                                f"Detailed analysis of {sub_title}.",
                                f"Key concepts regarding {sub_title}.",
                                "Refer to the source text for detailed information."
                            ],
                            source_refs=["Programmatic Fallback Synthesis"]
                        )
                        fallback_units.append(unit)
                    return fallback_units
                    
        tasks = [generate_batch(i, batch) for i, batch in enumerate(subtopic_batches)]
        results = await asyncio.gather(*tasks)
        
        for res in results:
            if res is not None and isinstance(res, list):
                units.extend(res)
                
        # Re-order just in case asyncio gather returns them out of intended slide order
        units.sort(key=lambda x: x.order)
        
        # --- INJECT GUARANTEED OUTRO SLIDE ---
        outro_unit = TeachingUnit(
            unit_id=str(uuid.uuid4()),
            lesson_id=understanding.main_topic,
            order=len(units) + 1,
            learning_goal="Thank You for Learning!",
            bullet_sentences=[
                f"This concludes our chapter on {understanding.main_topic}.",
                "Please review the material to reinforce your understanding.",
                "Keep up the great work and see you next time!"
            ],
            source_refs=["System Generated Outro"]
        )
        
        final_units = units + [outro_unit]
                
        return final_units
