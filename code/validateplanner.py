from typing import Annotated

from pydantic import BaseModel, field_validator
from annotated_types import MinLen, MaxLen

class PlannerOutput(BaseModel):
    # Exactly 3 string tags, each 3-30 characters
    tags: Annotated[list[Annotated[str, MinLen(3), MaxLen(30)]], MinLen(3), MaxLen(3)]
    summary: str

    # Summary of at most 25 words
    @field_validator("summary")
    def summary_word_count(cls, summary):
        if len(summary.split()) > 25:
            raise ValueError(f"Summary exceeds 25 words: {len(summary.split())} words")
        return summary