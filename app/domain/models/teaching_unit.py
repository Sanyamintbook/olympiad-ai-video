from pydantic import BaseModel, Field

class TeachingUnit(BaseModel):
    unit_id: str
    lesson_id: str
    order: int
    learning_goal: str
    bullet_sentences: list[str] = Field(min_length=3, max_length=6)
    source_refs: list[str] = Field(min_length=1)
