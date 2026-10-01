import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import LectureSourceType, LectureStatus
from app.database.base import Base


class Lecture(Base):
    __tablename__ = "lectures"

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

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    source_type: Mapped[LectureSourceType] = mapped_column(
        Enum(LectureSourceType, name="lecture_source_type"),
        nullable=False,
    )

    source_path: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    transcript_path: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    pdf_path: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    html_path: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    debug_path: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    language: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    status: Mapped[LectureStatus] = mapped_column(
        Enum(LectureStatus, name="lecture_status"),
        nullable=False,
        default=LectureStatus.PROCESSING,
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
        back_populates="lectures",
    )

    transcript = relationship(
        "Transcript",
        back_populates="lecture",
        uselist=False,
        cascade="all, delete-orphan",
    )

    note = relationship(
        "Note",
        back_populates="lecture",
        uselist=False,
        cascade="all, delete-orphan",
    )