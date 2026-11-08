from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

QuestionText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=4, max_length=4000)]
Label = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class QuestionCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: QuestionText
    number: Label | None = None
    section: Label | None = None
    marks_label: Label | None = None


class ExtractedPage(BaseModel):
    questions: list[QuestionCandidate] = Field(max_length=80)


class PaperQuestion(BaseModel):
    text: str
    page: int
    number: str | None = None
    section: str | None = None
    marks: int | None = None
    topic_id: UUID | None = None
    topic_title: str | None = None
    similarity: float | None = None


class PaperSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    course_id: UUID
    filename: str
    exam_year: int | None
    syllabus_document_id: UUID | None
    created_at: datetime


class PaperDetail(PaperSummary):
    questions: list[PaperQuestion]
    warnings: list[str]


class RepeatQuestion(BaseModel):
    text: str
    paper_ids: list[UUID]


class TopicFrequency(BaseModel):
    topic_id: UUID
    topic_title: str
    paper_count: int
    question_count: int


class PaperAnalysis(BaseModel):
    paper_count: int
    earliest_year: int | None
    latest_year: int | None
    papers_with_year: int
    question_count: int
    questions_with_marks: int
    marks_distribution: dict[int, int]
    repeated_questions: list[RepeatQuestion]
    suggested_topic_frequency: list[TopicFrequency]

