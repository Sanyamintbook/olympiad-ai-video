import asyncio
from app.infrastructure.ai.agents.unit.unit_goal_agent import UnitGoalAgent
from app.infrastructure.ai.agents.unit.unit_content_agent import UnitContentAgent

async def test_unit_planner():
    print("=== Testing Teaching Unit Micro-Agents ===")
    
    # 1. Test Goal
    goal_agent = UnitGoalAgent()
    print("\n1. Testing UnitGoalAgent...")
    goal = await goal_agent.generate_goal("Formation of Coal", "Minerals")
    print(f"Result: {goal}")
    
    # 2. Test Content
    content_agent = UnitContentAgent()
    print("\n2. Testing UnitContentAgent...")
    raw_text = "Coal is formed over millions of years from dead plant matter."
    content = await content_agent.generate_content(goal, "Formation of Coal", raw_text, [])
    print(f"Result: {content}")

if __name__ == "__main__":
    asyncio.run(test_unit_planner())
