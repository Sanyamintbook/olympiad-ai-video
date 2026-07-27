from typing import Any
from app.domain.models.source_document import SourceDocument
from app.domain.models.understanding import Understanding
from app.infrastructure.ai.agents.base_agent import BaseAgent
from app.infrastructure.ai.providers.base import LLMProvider
from app.infrastructure.ai.prompts.loader import PromptLoader

from typing import Any
from app.domain.models.source_document import SourceDocument
from app.domain.models.understanding import Understanding
from app.infrastructure.ai.agents.base_agent import BaseAgent
from app.infrastructure.ai.providers.base import LLMProvider
from app.infrastructure.ai.prompts.loader import PromptLoader

class ContentUnderstandingAgent(BaseAgent):
    """Extracts structured understanding from educational content."""

    def __init__(self, provider: LLMProvider | None = None, prompt_loader: PromptLoader | None = None) -> None:
        super().__init__(provider=provider, prompt_loader=prompt_loader)

    async def run(self, content: SourceDocument) -> Understanding:
        source_text = content.raw_text
        
        # 1. High-level extraction (Use first 6000 chars to save tokens)
        context = {
            "title": content.filename,
            "content": source_text[:6000],
        }
        
        schema = Understanding.model_json_schema()
        
        def validate_result(res: dict):
            if not res.get("chapter_title") or not res.get("main_topic"):
                raise ValueError(f"LLM returned incomplete JSON. Got: {res}")
                
        self.logger.info(f"Extracting high-level metadata for {content.filename}...")
        result_dict = await self.generate_structured("content_understanding", schema=schema, context=context, validator=validate_result)
        
        # 2. Scatter-Gather Chunking for Exhaustive Subtopic Extraction
        import textwrap
        # Chunk text into ~3000 character pieces
        chunks = textwrap.wrap(source_text, width=3000, break_long_words=False, replace_whitespace=False)
        
        raw_subtopics = []
        import re
        for i, chunk in enumerate(chunks):
            self.logger.info(f"Extracting granular topics from chunk {i+1}/{len(chunks)}...")
            chunk_context = {"text_chunk": chunk}
            try:
                chunk_res = await self.generate_text(
                    "content_extraction_chunk", 
                    context=chunk_context,
                    num_predict=400
                )
                self.logger.info(f"Raw chunk {i+1} output: {chunk_res.strip()}")
                
                topics = []
                # Fallback: if it outputted JSON array despite instructions
                import json
                if chunk_res.strip().startswith('['):
                    try:
                        parsed = json.loads(chunk_res[chunk_res.find('['):chunk_res.rfind(']')+1])
                        if isinstance(parsed, list):
                            topics.extend([str(t) for t in parsed])
                    except:
                        pass
                        
                # Parse as numbered list or bullets
                if not topics:
                    for line in chunk_res.split('\n'):
                        line = line.strip()
                        # Matches "1. Topic", "1) Topic", "1 Topic", "* Topic", "- Topic"
                        match = re.match(r'^(\d+[\.\)]?|-|\*)\s*(.*)', line)
                        if match:
                            topic = match.group(2).strip()
                            # Remove trailing periods or quotes if hallucinated
                            topic = re.sub(r'[\."\']+$', '', topic)
                            if topic:
                                topics.append(topic)
                                
                for topic in topics:
                    if len(topic.split()) <= 7:
                        raw_subtopics.append(topic)
                        
                self.logger.info(f"Extracted {len(topics)} topics from chunk {i+1}")
            except Exception as e:
                self.logger.warning(f"Failed to extract from chunk {i+1}: {e}")
                
        # Deduplicate while preserving order
        raw_subtopics = list(dict.fromkeys(raw_subtopics))
        
        # Hard programmatic safety net to prevent 8B LLMs from returning full sentences or exercises
        cleaned_subtopics = []
        banned_words = ["questions", "activity", "project", "exercise", "task", "terms:"]
        for st in raw_subtopics:
            st_lower = str(st).lower()
            if len(st.split()) > 7 or any(banned in st_lower for banned in banned_words):
                continue
            cleaned_subtopics.append(st)
            
        if not cleaned_subtopics:
            cleaned_subtopics = ["General Topic"]
            
        return Understanding(
            document_id=content.document_id,
            chapter_title=result_dict.get("chapter_title"),
            main_topic=result_dict.get("main_topic"),
            major_topics=result_dict.get("major_topics", ["General Topic"]),
            subtopics=cleaned_subtopics,
            learning_objectives=result_dict.get("learning_objectives", ["Understand the material"]),
            definitions=result_dict.get("definitions", []),
            summary=result_dict.get("summary", "Summary not available.")
        )
