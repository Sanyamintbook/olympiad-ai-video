import asyncio
from app.domain.models.understanding import Understanding
from app.infrastructure.ai.agents.lesson.audience_profiler_agent import AudienceProfilerAgent
from app.infrastructure.ai.agents.lesson.lesson_plan_compiler_agent import LessonPlanCompilerAgent

async def test_lesson_planner():
    print("=== Testing Lesson Planner Micro-Agents ===")
    
    understanding = Understanding(
        document_id="doc1",
        chapter_title="Minerals",
        main_topic="Minerals",
        major_topics=["Coal"],
        subtopics=["Formation of Coal"],
        learning_objectives=["Understand Coal"],
        definitions=[],
        summary="A chapter on minerals."
    )
    
    # 1. Test Audience
    audience_agent = AudienceProfilerAgent()
    print("\n1. Testing AudienceProfilerAgent...")
    profile = await audience_agent.profile_audience(understanding)
    print(f"Result: {profile}")
    
    # 2. Test Compiler
    compiler_agent = LessonPlanCompilerAgent()
    print("\n2. Testing LessonPlanCompilerAgent...")
    lessons = await compiler_agent.compile_plan(understanding, profile)
    print(f"Result: {lessons}")

if __name__ == "__main__":
    asyncio.run(test_lesson_planner())
