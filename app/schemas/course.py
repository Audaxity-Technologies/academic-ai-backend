from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CourseCreate(BaseModel):
    name: str
    code: str
    description: str | None = None


class CourseUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    is_active: bool | None = None


class CourseResponse(BaseModel):
    id: UUID
    name: str
    code: str
    description: str | None
    teacher_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)