import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class SyllabusTopic(Base):
    __tablename__ = "syllabus_topics"

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

    syllabus_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("syllabus_documents.id", ondelete="CASCADE"), index=True
    )
    syllabus_unit_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("syllabus_units.id", ondelete="CASCADE"), index=True
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("syllabus_topics.id", ondelete="CASCADE"), index=True
    )
    unit = relationship("SyllabusUnit")
    parent = relationship("SyllabusTopic", remote_side=[id])
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

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Embedding for semantic retrieval (384-dimensional for bge-small-en-v1.5)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(384),
        nullable=True,
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
        back_populates="syllabus_topics",
    )
