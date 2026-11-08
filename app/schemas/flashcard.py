from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints, model_validator

UtcTimestamp = Annotated[datetime, AfterValidator(lambda value: value.astimezone(UTC))]
CardKind = Literal["question_answer", "definition", "formula", "concept", "cloze"]
FrontText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
BackText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=3000)]


class CardContent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: CardKind
    front: FrontText
    back: BackText

    @model_validator(mode="after")
    def check_cloze(self):
        if self.kind == "cloze" and "___" not in self.front:
            raise ValueError("A cloze prompt needs a blank written as ___")
        return self


class CardCreate(CardContent):
    course_id: UUID
    topic_id: UUID | None = None


class GeneratedCard(CardContent):
    evidence: Annotated[str, StringConstraints(strip_whitespace=True, min_length=8, max_length=1000)]


class GeneratedCards(BaseModel):
    cards: list[GeneratedCard] = Field(min_length=1, max_length=10)


class GenerateCards(BaseModel):
    course_id: UUID
    topic_id: UUID | None = None
    lecture_id: UUID | None = None
    kind: CardKind = "question_answer"
    count: int = Field(default=5, ge=1, le=10)

    @model_validator(mode="after")
    def check_source(self):
        if self.topic_id is None and self.lecture_id is None:
            raise ValueError("Choose a syllabus topic or an approved lecture")
        return self


class FlashcardResponse(CardContent):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    course_id: UUID
    topic_id: UUID | None
    lecture_id: UUID | None
    origin: Literal["manual", "lecture", "syllabus"]
    due_at: UtcTimestamp
    interval_days: int
    repetitions: int
    review_count: int


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rating: int = Field(ge=0, le=5, strict=True)
    review_count: int = Field(ge=0, strict=True)


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    sequence: int
    rating: int
    reviewed_at: UtcTimestamp
    due_at: UtcTimestamp
    interval_days: int


class CardDeck(BaseModel):
    cards: list[FlashcardResponse]
    total: int
    due_count: int
    priority_topic_ids: list[UUID]

