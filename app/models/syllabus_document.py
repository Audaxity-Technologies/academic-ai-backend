import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Index, UniqueConstraint, text, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class SyllabusDocument(Base):
    """
    Represents an uploaded syllabus document (PDF, DOCX, TXT).
    Stores the original file and parsing metadata.
    """
    __tablename__ = "syllabus_documents"

    __table_args__ = (
        CheckConstraint("NOT is_active OR confirmed_at IS NOT NULL", name="ck_syllabus_active_confirmed"),
        UniqueConstraint("course_id", "version", name="uq_syllabus_course_version"),
        Index("uq_syllabus_active_course", "course_id", unique=True,
              postgresql_where=text("is_active")),
    )

    parsing_attempt: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    hierarchy: Mapped[dict | None] = mapped_column(JSONB)
    parsing_report: Mapped[dict | None] = mapped_column(JSONB)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    file_path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    file_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    parsing_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
    )

    parsing_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    parsed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    course = relationship(
        "Course",
        back_populates="syllabus_documents",
    )

    syllabus_units = relationship(
        "SyllabusUnit",
        back_populates="document",
        cascade="all, delete-orphan",
    )
