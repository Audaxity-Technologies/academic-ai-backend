from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
Number = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


class AcademicNode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Title
    number: Number | None = None
    description: str | None = Field(default=None, max_length=4000)
    pages: list[Annotated[int, Field(ge=1, strict=True)]] = Field(default_factory=list, max_length=250)


class TopicNode(AcademicNode):
    subtopics: list["TopicNode"] = Field(default_factory=list, max_length=300)


class UnitNode(AcademicNode):
    topics: list[TopicNode] = Field(max_length=500)


class SyllabusHierarchy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject_name: Title | None = None
    course_code: Number | None = None
    references: list[str] = Field(default_factory=list, max_length=100)
    learning_outcomes: list[str] = Field(default_factory=list, max_length=100)
    assessment: list[str] = Field(default_factory=list, max_length=100)
    units: list[UnitNode] = Field(max_length=100)
    needs_review: bool = False
    review_reason: str | None = Field(default=None, max_length=2000)


class ParsingReport(BaseModel):
    pages_processed: int
    units: int
    topics: int
    subtopics: int
    empty_pages: list[int]
    ocr_pages: list[int]
    warnings: list[str]
    needs_review: bool


class SyllabusDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    course_id: UUID
    original_filename: str
    file_type: str
    version: int
    is_active: bool
    confirmed_at: datetime | None
    parsing_status: str
    parsing_error: str | None
    parsed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    parsing_report: ParsingReport | None


class ParsedSyllabusResponse(BaseModel):
    document: SyllabusDocumentResponse
    hierarchy: SyllabusHierarchy
    total_topics: int


class SyllabusUnitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    syllabus_document_id: UUID
    unit_number: int
    number: str | None
    pages: list[int] | None
    title: str
    description: str | None
    page_reference: str | None
    position: int


class SyllabusTopicNodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    description: str | None
    parent_id: UUID | None
    number: str | None
    pages: list[int] | None
    position: int

