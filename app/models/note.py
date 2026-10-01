import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import NoteStatus
from app.database.base import Base


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    lecture_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lectures.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    content: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )

    pdf_path: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    html_path: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    status: Mapped[NoteStatus] = mapped_column(
        Enum(NoteStatus, name="note_status"),
        nullable=False,
        default=NoteStatus.DRAFT,
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

    lecture = relationship(
        "Lecture",
        back_populates="note",
    )