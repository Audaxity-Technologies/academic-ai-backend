from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.ai.syllabus.alignment import CoverageStatus


class CoverageStats(BaseModel):
    total_topics: int
    covered: int
    partially_covered: int
    mentioned: int
    not_covered: int
    coverage_percentage: float


class Evidence(BaseModel):
    text: str
    start_time: float | None = None
    end_time: float | None = None


class Mapping(BaseModel):
    syllabus_topic_id: UUID
    syllabus_topic: str
    status: CoverageStatus
    confidence: float
    evidence: list[Evidence]
    explanation: str | None = None
    needs_review: bool = False


class LectureEvidence(Mapping):
    lecture_id: UUID
    lecture_title: str


class TopicProgress(BaseModel):
    id: UUID
    title: str
    parent_id: UUID | None
    unit_id: UUID | None
    number: str | None
    status: CoverageStatus
    history: list[LectureEvidence]


class UnitProgress(CoverageStats):
    id: UUID | None
    title: str
    topics: list[TopicProgress]


class LectureProgress(CoverageStats):
    lecture_id: UUID
    lecture_title: str
    created_at: datetime


class CourseProgress(CoverageStats):
    syllabus_document_id: UUID | None
    units: list[UnitProgress]
    lectures: list[LectureProgress]


class LectureSummary(CoverageStats):
    lecture_id: UUID
    syllabus_document_id: UUID | None
    status: str | None
    message: str | None = None
    available_versions: list[UUID | None]


class LectureCoverage(LectureSummary):
    mappings: list[Mapping]


class AlignmentQueued(BaseModel):
    status: str

