from __future__ import annotations
import json
from typing import Any

from pydantic import BaseModel, Field

from app.infrastructure.ai.agents.base_agent import BaseAgent
from app.infrastructure.ai.providers.base import LLMProvider
from app.infrastructure.ai.prompts.loader import PromptLoader
from app.domain.models.narration_segment import NarrationSegment
from app.domain.models.teaching_unit import TeachingUnit

class ValidatorAgent(BaseAgent):
    """Validates that generated scripts align with source content."""

    def __init__(self, provider: LLMProvider | None = None, prompt_loader: PromptLoader | None = None) -> None:
        super().__init__(provider=provider, prompt_loader=prompt_loader)

    async def run(self, segment: NarrationSegment, unit: TeachingUnit) -> NarrationSegment:
        payload = {
            "learning_goal": unit.learning_goal,
            "bullet_sentences": unit.bullet_sentences,
            "source_refs": unit.source_refs,
            "generated_narration": segment.narration_text
        }
        
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "passed or failed"},
                "issues": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["status", "issues"]
        }
        
        result_dict = await self.generate_structured(
            prompt_name="validator",
            context=payload,
            schema=schema,
        )
        
        status = result_dict.get("status", "failed").lower()
        
        if status == "passed":
            segment.validation_status = "PASS"
        else:
            segment.validation_status = "FAIL"
            
        segment.validation_notes = result_dict.get("issues", [])
        
        return segment
