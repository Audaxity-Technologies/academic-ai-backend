import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class SyllabusSubtopic(Base):
    """
    Represents a subtopic within a syllabus unit.
    Part of: Subject → Units → Topics → Subtopics
    """
    __tablename__ = "syllabus_subtopics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    syllabus_unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("syllabus_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    topic_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    page_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
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

    unit = relationship(
        "SyllabusUnit",
        back_populates="syllabus_subtopics",
    )
