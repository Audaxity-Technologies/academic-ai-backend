from uuid import UUID

from pydantic import BaseModel, Field


class RAGSource(BaseModel):
    id: int
    chunk_id: UUID
    title: str
    source_type: str
    lecture_id: UUID | None = None
    score: float


class RAGResponse(BaseModel):
    answer: str
    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )
    sources: list[RAGSource]


class IndexResponse(BaseModel):
    course_id: UUID
    chunks_indexed: int