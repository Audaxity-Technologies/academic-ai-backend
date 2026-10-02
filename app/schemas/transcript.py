from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TranscriptCreate(BaseModel):
    lecture_id: UUID
    content: str
    language: str | None = None


class TranscriptResponse(BaseModel):
    id: UUID
    lecture_id: UUID
    content: str
    language: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)