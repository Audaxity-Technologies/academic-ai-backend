from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.constants import LectureSourceType, LectureStatus


class LectureCreate(BaseModel):
    course_id: UUID
    title: str


class LectureResponse(BaseModel):
    id: UUID
    course_id: UUID
    title: str
    source_type: LectureSourceType
    source_path: str | None
    transcript_path: str | None
    pdf_path: str | None
    html_path: str | None
    debug_path: str | None
    language: str | None
    status: LectureStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)