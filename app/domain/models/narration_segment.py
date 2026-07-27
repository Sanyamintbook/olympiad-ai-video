from typing import Literal
from pydantic import BaseModel, Field

class NarrationSegment(BaseModel):
    unit_id: str = Field(description="Foreign key to TeachingUnit")
    narration_text: str = Field(min_length=40, description="Narration script text")
    estimated_duration_sec: float = Field(description="Word-count based duration estimate")
    validation_status: Literal["PENDING", "PASS", "FAIL"] = Field(default="PENDING")
    validation_notes: list[str] = Field(default_factory=list)
