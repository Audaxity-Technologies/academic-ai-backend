from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.schemas.search import RAGSource

ExplanationLevel = Literal["beginner", "detailed", "exam_oriented", "example_based"]


class ConversationThreadCreate(BaseModel):
    course_id: UUID | None = None
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)] | None = None


class ConversationThreadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    course_id: UUID | None
    title: str | None
    created_at: datetime
    updated_at: datetime


class ConversationMessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["user"] = "user"
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=1000)]
    thread_id: UUID | None = None


class ConversationMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    thread_id: UUID
    role: Literal["user", "assistant"]
    content: str
    citations: list[RAGSource] | None
    created_at: datetime


class ConversationWithMessages(ConversationThreadResponse):
    messages: list[ConversationMessageResponse]

