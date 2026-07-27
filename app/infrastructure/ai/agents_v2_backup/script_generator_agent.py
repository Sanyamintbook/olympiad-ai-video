from app.domain.models.teaching_unit import TeachingUnit
from app.domain.models.narration_segment import NarrationSegment
from app.infrastructure.ai.agents.base_agent import BaseAgent

class ScriptGeneratorAgent(BaseAgent):
    """
    Generates narration for a single TeachingUnit and estimates its duration.
    """

    async def run(self, unit: TeachingUnit, source_context: str = "") -> NarrationSegment:
        schema = {
            "type": "object",
            "properties": {
                "narration_text": {
                    "type": "string",
                    "description": "Engaging classroom narration script covering all unit keywords"
                }
            },
            "required": ["narration_text"]
        }

        context = {
            "learning_goal": unit.learning_goal,
            "keywords": ", ".join(unit.bullet_sentences),
            "source_context": source_context
        }

        # Prompt the LLM using the script_generator template
        result = await self.generate_structured(
            prompt_name="script_generator",
            schema=schema,
            context=context
        )

        narration_text = result.get("narration_text", "").strip()

        # Word count based heuristic for estimated duration (150 WPM / 2.5 words per second)
        word_count = len(narration_text.split())
        estimated_duration = round(word_count / 2.5, 1)

        return NarrationSegment(
            unit_id=unit.unit_id,
            narration_text=narration_text,
            estimated_duration_sec=estimated_duration,
            validation_status="PENDING",
            validation_notes=[]
        )
