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

    async def run(self, understanding: Understanding, source_text: str) -> list[TeachingUnit]:
        if len(source_text) > 15000:
            self.logger.info(f"Raw text is very large ({len(source_text)} chars). Truncating for local Ollama/LLM efficiency.")
            source_text = source_text[:10000] + "\n\n... [TRUNCATED FOR TOKEN EFFICIENCY] ...\n\n" + source_text[-5000:]
            
        units = []
        
        # Define the strict schema for a SINGLE unit
        schema = {
            "type": "object",
            "properties": {
                "learning_goal": {
                    "type": "string",
                    "description": "Hierarchical slide title (e.g. Major Topic - Subtopic), strictly under 60 characters."
                },
                "bullet_sentences": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of 3 to 6 complete sentences summarizing this exact subtopic. Each sentence MUST be strictly under 90 characters. Absolutely no single words."
                },
                "source_refs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Short quotes or references from the text validating the summary."
                }
            },
            "required": ["learning_goal", "bullet_sentences", "source_refs"]
        }
        
        def validate_unit(res):
            # The AI might occasionally wrap the single object in a list array
            if isinstance(res, list):
                if len(res) == 0:
                    raise ValueError("Output is an empty list")
                res = res[0]
            if not isinstance(res, dict):
                raise ValueError(f"Expected dict but got {type(res)}")
            if not res.get("learning_goal") or not res.get("bullet_sentences"):
                raise ValueError("Missing learning_goal or bullet_sentences in output")
            return res
                
        self.logger.info(f"Generating slides deterministically for {len(understanding.subtopics)} extracted subtopics...")
        
        # Loop through every single subtopic one by one
        for i, subtopic in enumerate(understanding.subtopics):
            context = {
                "subtopic": subtopic,
                "main_topic": understanding.main_topic,
                "definitions": understanding.definitions,
                "raw_text": source_text
            }
            
            try:
                self.logger.info(f"Generating slide {i+1}/{len(understanding.subtopics)} for subtopic: {subtopic[:50]}...")
                result_dict = await self.generate_structured(
                    "teaching_unit_planner", 
                    schema=schema, 
                    context=context, 
                    validator=validate_unit
                )
                
                # If the validation parsed it as a list and returned the dict, grab it
                if isinstance(result_dict, list):
                    if len(result_dict) > 0:
                        result_dict = result_dict[0]
                    else:
                        result_dict = {}
                
                bullets = result_dict.get("bullet_sentences", [])
                
                # Safety enforcement: Pydantic requires exactly 3 to 6 bullets.
                # If the AI ignores instructions and writes 10 bullets, slice it to 6.
                if len(bullets) > 6:
                    bullets = bullets[:6]
                # If the AI writes less than 3 bullets, duplicate the last one to satisfy Pydantic.
                while len(bullets) < 3:
                    if bullets:
                        bullets.append(bullets[-1])
                    else:
                        bullets.append("Detailed analysis of this topic.")
                
                unit = TeachingUnit(
                    unit_id=str(uuid.uuid4()),
                    lesson_id=understanding.main_topic,
                    order=i + 1,
                    learning_goal=result_dict.get("learning_goal", "Goal"),
                    bullet_sentences=bullets,
                    source_refs=result_dict.get("source_refs", [])
                )
                units.append(unit)
            except Exception as e:
                self.logger.warning(f"Failed to generate slide for subtopic {subtopic[:50]}: {e}")
                
        return units
