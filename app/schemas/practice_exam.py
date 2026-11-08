from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints, model_validator

Difficulty = Literal["easy", "medium", "hard"]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class ExamCreate(BaseModel):
    course_id: UUID
    topic_ids: list[UUID] = Field(min_length=1, max_length=12)
    difficulty: Difficulty = "medium"
    count: int = Field(default=5, ge=1, le=15)
    duration_minutes: int | None = Field(default=None, ge=1, le=180)


class ExamQuestion(BaseModel):
    topic_id: UUID
    prompt: LongText
    options: list[ShortText] = Field(min_length=4, max_length=4)

    @model_validator(mode="after")
    def distinct_choices(self):
        if len({option.casefold() for option in self.options}) != 4:
            raise ValueError("Question options must be distinct")
        return self


class GeneratedQuestion(ExamQuestion):
    correct_index: int = Field(ge=0, le=3)
    explanation: LongText
    source_numbers: list[int] = Field(default_factory=list, max_length=5)


class GeneratedExam(BaseModel):
    questions: list[GeneratedQuestion] = Field(min_length=1, max_length=15)


class ExamAnswer(BaseModel):
    choice: int | None = Field(default=None, ge=0, le=3)
    seconds: int = Field(default=0, ge=0, le=86400)


class ExamSubmission(BaseModel):
    answers: list[ExamAnswer] = Field(min_length=1, max_length=15)


class ExamFeedback(ExamAnswer):
    correct_index: int
    correct: bool
    explanation: str
    lecture_ids: list[UUID]


class ExamResult(BaseModel):
    score: int
    total: int
    submitted_at: datetime
    late: bool
    feedback: list[ExamFeedback]


class ExamSummary(BaseModel):
    id: UUID
    course_id: UUID
    difficulty: Difficulty
    duration_minutes: int | None
    created_at: datetime
    score: int | None
    total: int


class ExamDetail(ExamSummary):
    questions: list[ExamQuestion]
    result: ExamResult | None


class ExamTopic(BaseModel):
    id: UUID
    title: str
    unit: str | None

