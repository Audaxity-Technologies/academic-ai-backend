"""Store private syllabus-aware practice exams and results."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "e704d20c5293"
down_revision = "d61f5278885a"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "practice_exams",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", sa.Uuid(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("duration_minutes", sa.Integer()),
        sa.Column("questions", JSONB(), nullable=False),
        sa.Column("result", JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_practice_exams_user_id", "practice_exams", ["user_id"])
    op.create_index("ix_practice_exams_course_id", "practice_exams", ["course_id"])


def downgrade():
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM practice_exams) THEN
                RAISE EXCEPTION 'Export saved practice exams before removing this table.';
            END IF;
        END $$
    """)
    op.drop_table("practice_exams")

