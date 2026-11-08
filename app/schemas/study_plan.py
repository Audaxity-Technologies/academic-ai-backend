from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StringConstraints, model_validator

GoalKind = Literal["exam", "assignment", "study_goal"]


class GoalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    course_id: UUID
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    kind: GoalKind
    topic_ids: list[UUID] = Field(default_factory=list, max_length=20)
    start_date: date
    deadline: date
    minutes_per_item: int = Field(ge=5, le=180)
    daily_minutes: int = Field(ge=5, le=360)

    @model_validator(mode="after")
    def check_schedule(self):
        if not 0 <= (self.deadline - self.start_date).days <= 180:
            raise ValueError("The deadline must be on or within 180 days of the start date")
        if len(self.topic_ids) != len(set(self.topic_ids)):
            raise ValueError("Select each topic once")
        return self


class GoalReplan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start_date: date
    deadline: date
    daily_minutes: int = Field(ge=5, le=360)

    @model_validator(mode="after")
    def check_schedule(self):
        if not 0 <= (self.deadline - self.start_date).days <= 180:
            raise ValueError("The deadline must be on or within 180 days of the start date")
        return self


class SessionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    completed: StrictBool


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    topic_id: UUID | None
    title: str
    study_date: date
    minutes: int
    status: Literal["planned", "completed"]
    completed_at: datetime | None


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    course_id: UUID
    title: str
    kind: GoalKind
    deadline: date
    minutes_per_item: int
    daily_minutes: int
    unscheduled_minutes: int
    sessions: list[SessionResponse]

