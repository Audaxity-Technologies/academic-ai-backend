from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SyllabusTopicCreate(BaseModel):
    title: str
    description: str | None = None
    position: int


class SyllabusTopicUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    position: int | None = None


class SyllabusTopicResponse(BaseModel):
    id: UUID
    course_id: UUID
    title: str
    description: str | None
    position: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)