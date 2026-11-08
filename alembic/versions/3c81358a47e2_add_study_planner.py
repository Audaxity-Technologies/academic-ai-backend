"""Add private study goals and scheduled sessions."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "3c81358a47e2"
down_revision = "469ad0c648b1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "study_goals",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", sa.Uuid(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("deadline", sa.Date(), nullable=False),
        sa.Column("minutes_per_item", sa.Integer(), nullable=False),
        sa.Column("daily_minutes", sa.Integer(), nullable=False),
        sa.Column("targets", JSONB(), nullable=False),
        sa.Column("unscheduled_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_study_goals_user_id", "study_goals", ["user_id"])
    op.create_index("ix_study_goals_course_id", "study_goals", ["course_id"])
    op.create_table(
        "study_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("goal_id", sa.Uuid(), sa.ForeignKey("study_goals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic_id", sa.Uuid()),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("study_date", sa.Date(), nullable=False),
        sa.Column("minutes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="planned"),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_study_sessions_goal_id", "study_sessions", ["goal_id"])


def downgrade():
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM study_goals) THEN
                RAISE EXCEPTION 'Export saved study plans before removing these tables.';
            END IF;
        END $$
    """)
    op.drop_table("study_sessions")
    op.drop_table("study_goals")

