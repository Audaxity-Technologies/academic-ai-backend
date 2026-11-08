"""Add private flashcards and review events."""

import sqlalchemy as sa
from alembic import op

revision = "469ad0c648b1"
down_revision = "8ac42f607d91"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "flashcards",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", sa.Uuid(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic_id", sa.Uuid(), sa.ForeignKey("syllabus_topics.id", ondelete="SET NULL")),
        sa.Column("lecture_id", sa.Uuid(), sa.ForeignKey("lectures.id", ondelete="SET NULL")),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("origin", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("front", sa.Text(), nullable=False),
        sa.Column("back", sa.Text(), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("ease", sa.Integer(), nullable=False, server_default="250"),
        sa.Column("repetitions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("interval_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("review_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_flashcards_user_id", "flashcards", ["user_id"])
    op.create_index("ix_flashcards_course_id", "flashcards", ["course_id"])
    op.create_index("ix_flashcards_owner_course_due", "flashcards", ["user_id", "course_id", "due_at"])
    op.create_table(
        "flashcard_reviews",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("card_id", sa.Uuid(), sa.ForeignKey("flashcards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.CheckConstraint("rating BETWEEN 0 AND 5", name="ck_flashcard_review_rating"),
        sa.UniqueConstraint("card_id", "sequence", name="uq_flashcard_review_sequence"),
    )
    op.create_index("ix_flashcard_reviews_card_id", "flashcard_reviews", ["card_id"])


def downgrade():
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM flashcards) THEN
                RAISE EXCEPTION 'Export saved flashcards before removing these tables.';
            END IF;
        END $$
    """)
    op.drop_table("flashcard_reviews")
    op.drop_table("flashcards")

