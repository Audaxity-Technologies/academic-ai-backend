import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class SyllabusUnit(Base):
    """
    Represents a unit/module in a syllabus hierarchy.
    Part of: Subject → Units → Topics → Subtopics
    """
    __tablename__ = "syllabus_units"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    syllabus_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("syllabus_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    unit_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    number: Mapped[str | None] = mapped_column(String(80))
    pages: Mapped[list | None] = mapped_column(JSONB)

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

    document = relationship(
        "SyllabusDocument",
        back_populates="syllabus_units",
    )

    syllabus_subtopics = relationship(
        "SyllabusSubtopic",
        back_populates="unit",
        cascade="all, delete-orphan",
    )
