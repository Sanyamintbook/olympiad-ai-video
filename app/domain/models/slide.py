from pydantic import BaseModel, Field

class Slide(BaseModel):
    unit_id: str
    title: str
    bullets: list[str] = Field(min_length=3, max_length=6)
    image_ref: str | None = None
    speaker_notes: str = ""
