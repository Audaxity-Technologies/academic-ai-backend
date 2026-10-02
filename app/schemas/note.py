from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.constants import NoteStatus


class Example(BaseModel):
    description: str
    illustration: str


class Definition(BaseModel):
    term: str
    definition: str


class Diagram(BaseModel):
    type: str
    mermaid_code: str | None = None


class NoteSection(BaseModel):
    heading: str
    explanation: str
    examples: list[Example] = []
    definitions: list[Definition] = []
    formulas: list[str] = []
    diagram: Diagram
    instructor_emphasis: list[str] = []
    common_misconceptions: list[str] = []


class QuestionAnswer(BaseModel):
    question: str
    answer: str


class NoteContent(BaseModel):
    title: str
    summary: str
    learning_objectives: list[str]
    sections: list[NoteSection]
    questions_and_answers: list[QuestionAnswer]
    revision_summary: str | None = None


class NoteCreate(BaseModel):
    lecture_id: UUID
    title: str
    content: NoteContent


class NoteUpdate(BaseModel):
    title: str | None = None
    content: NoteContent | None = None
    status: NoteStatus | None = None


class NoteResponse(BaseModel):
    id: UUID
    lecture_id: UUID
    title: str
    content: NoteContent
    pdf_path: str | None
    html_path: str | None
    status: NoteStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)