from typing import Literal

from pydantic import BaseModel, Field


class TopicMapping(BaseModel):
    syllabus_topic: str

    status: Literal[
        "covered",
        "partially_covered",
        "mentioned",
        "not_covered"
    ]

    confidence: float = Field(
        ge=0.0,
        le=1.0
    )

    evidence: list[str]


class SyllabusMappingResult(BaseModel):
    mappings: list[TopicMapping]