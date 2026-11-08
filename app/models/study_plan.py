from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class StudyGoal(Base):
    __tablename__ = "study_goals"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    kind: Mapped[str] = mapped_column(String(20))
    deadline: Mapped[date] = mapped_column(Date)
    minutes_per_item: Mapped[int] = mapped_column(Integer)
    daily_minutes: Mapped[int] = mapped_column(Integer)
    targets: Mapped[list] = mapped_column(JSONB)
    unscheduled_minutes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sessions: Mapped[list["StudySession"]] = relationship(
        back_populates="goal", cascade="all, delete-orphan", passive_deletes=True,
        order_by="(StudySession.study_date, StudySession.created_at, StudySession.id)",
    )


class StudySession(Base):
    __tablename__ = "study_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    goal_id: Mapped[UUID] = mapped_column(ForeignKey("study_goals.id", ondelete="CASCADE"), index=True)
    topic_id: Mapped[UUID | None]
    title: Mapped[str] = mapped_column(String(255))
    study_date: Mapped[date] = mapped_column(Date)
    minutes: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="planned")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    goal: Mapped[StudyGoal] = relationship(back_populates="sessions")

