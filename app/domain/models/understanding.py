from pydantic import BaseModel, Field

class Understanding(BaseModel):
    document_id: str
    chapter_title: str
    main_topic: str
    major_topics: list[str] = Field(min_length=1)
    subtopics: list[str] = Field(
        description="Strictly a list of single nouns or short entities representing distinct syllabus topics (e.g., 'Iron', 'Solar Energy'). MUST NOT contain full sentences, facts, or descriptions."
    )
    learning_objectives: list[str] = Field(min_length=1)
    definitions: list[dict]
    examples: list[str]
    summary: str
