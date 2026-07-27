import asyncio
from app.domain.models.teaching_unit import TeachingUnit
from app.domain.models.narration_segment import NarrationSegment
from app.infrastructure.ai.agents.validator.fact_checker_agent import FactCheckerAgent
from app.infrastructure.ai.agents.validator.constraint_validator_agent import ConstraintValidatorAgent

async def test_validator():
    print("=== Testing Validator Micro-Agents ===")
    
    unit = TeachingUnit(
        unit_id="u1",
        lesson_id="l1",
        order=1,
        learning_goal="Minerals - Introduction",
        bullet_sentences=["Minerals are solid.", "They are inorganic."],
        source_refs=[]
    )
    
    segment = NarrationSegment(
        unit_id="u1",
        narration_text="Minerals are liquid and organic.", # Hallucination to trigger failure
        estimated_duration_sec=10.0,
        validation_status="PENDING",
        validation_notes=[]
    )
    
    # 1. Test Fact Checker
    fact_agent = FactCheckerAgent()
    print("\n1. Testing FactCheckerAgent...")
    fact_res = await fact_agent.check_facts(segment, unit)
    print(f"Result: {fact_res}")
    
    # 2. Test Constraint Validator
    constraint_agent = ConstraintValidatorAgent()
    print("\n2. Testing ConstraintValidatorAgent...")
    segment.narration_text = "Okay students, minerals are solid and inorganic!" # Passing text
    const_res = await constraint_agent.validate_constraints(segment, unit)
    print(f"Result: {const_res}")

if __name__ == "__main__":
    asyncio.run(test_validator())
