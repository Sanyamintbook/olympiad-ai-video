import asyncio
from app.domain.models.teaching_unit import TeachingUnit
from app.infrastructure.ai.agents.script.script_writer_agent import ScriptWriterAgent
from app.infrastructure.ai.agents.script.tone_refiner_agent import ToneRefinerAgent

async def test_script_generation():
    print("=== Testing Script Generation Micro-Agents ===")
    
    unit = TeachingUnit(
        unit_id="u1",
        lesson_id="l1",
        order=1,
        learning_goal="Minerals - Introduction",
        bullet_sentences=["Minerals are naturally occurring.", "They have a crystalline structure.", "They are solid."],
        source_refs=["Page 1"]
    )
    
    # 1. Test Writer
    writer_agent = ScriptWriterAgent()
    print("\n1. Testing ScriptWriterAgent...")
    draft = await writer_agent.write_script(unit, "Some textbook context.")
    print(f"Result:\n{draft}")
    
    # 2. Test Refiner
    refiner_agent = ToneRefinerAgent()
    print("\n2. Testing ToneRefinerAgent...")
    refined = await refiner_agent.refine_tone(draft, unit)
    print(f"Result:\n{refined}")

if __name__ == "__main__":
    asyncio.run(test_script_generation())
