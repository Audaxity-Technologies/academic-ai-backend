"""Store private past papers and source-grounded questions."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "8ac42f607d91"
down_revision = "e704d20c5293"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "question_papers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", sa.Uuid(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.UniqueConstraint("user_id", "course_id", "sha256", name="uq_question_papers_owner_digest"),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("storage_path", sa.String(1000), nullable=False),
        sa.Column("exam_year", sa.Integer()),
        sa.Column("syllabus_document_id", sa.Uuid(),
                  sa.ForeignKey("syllabus_documents.id", ondelete="SET NULL")),
        sa.Column("questions", JSONB(), nullable=False),
        sa.Column("warnings", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_question_papers_user_id", "question_papers", ["user_id"])
    op.create_index("ix_question_papers_course_id", "question_papers", ["course_id"])


def downgrade():
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM question_papers) THEN
                RAISE EXCEPTION 'Export saved past papers before removing this table.';
            END IF;
        END $$
    """)
    op.drop_table("question_papers")

