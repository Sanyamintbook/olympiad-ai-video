from typing import Any
from app.domain.models.understanding import Understanding
from app.domain.models.lesson_plan import LessonPlan, Lesson
from app.infrastructure.ai.agents.base_agent import BaseAgent
from app.infrastructure.ai.providers.base import LLMProvider
from app.infrastructure.ai.prompts.loader import PromptLoader

class LessonPlannerAgent(BaseAgent):
    """Generates a structured lesson plan."""

    def __init__(self, provider: LLMProvider | None = None, prompt_loader: PromptLoader | None = None) -> None:
        super().__init__(provider=provider, prompt_loader=prompt_loader)

    async def run(self, understanding: Understanding) -> LessonPlan:
        context = {
            "chapter_title": understanding.chapter_title,
            "main_topic": understanding.main_topic,
            "major_topics": understanding.major_topics,
            "learning_objectives": understanding.learning_objectives,
            "understanding_json": understanding.model_dump_json()
        }
        
        schema = LessonPlan.model_json_schema()
        
        def validate_result(res: dict):
            if not res.get("lessons"):
                raise ValueError("LLM failed to generate any lessons from the provided understanding data.")
                
        result_dict = await self.generate_structured("lesson_planner", schema=schema, context=context, validator=validate_result)
        
        lessons_data = result_dict.get("lessons", [])
        lessons = []
        for i, l in enumerate(lessons_data):
            lessons.append(Lesson(
                sequence=i+1,
                title=l.get("title", f"Lesson {i+1}"),
                objective=l.get("objective", "Objective"),
                estimated_minutes=l.get("estimated_minutes", 10)
            ))
            
        return LessonPlan(
            document_id=understanding.document_id,
            lessons=lessons
        )
