import asyncio
from app.infrastructure.ai.agents.teaching_unit_planner_agent import TeachingUnitPlannerAgent
from app.domain.models.understanding import Understanding

async def main():
    agent = TeachingUnitPlannerAgent()
    
    # Mock understanding
    understanding = Understanding(
        document_id="doc1",
        chapter_title="Chapter 1",
        main_topic="Main",
        major_topics=["Major"],
        subtopics=["Sub1", "Sub2"],
        learning_objectives=["Obj1"],
        definitions=[],
        examples=[],
        summary="Sum"
    )
    
    try:
        units = await agent.run(understanding, "Some text")
        print(f"Units: {units}")
    except Exception as e:
        print(f"CRASH: {repr(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
