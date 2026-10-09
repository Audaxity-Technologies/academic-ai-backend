"""add rag chunks

Revision ID: a91f42c7d831
Revises: 53787c837466
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "a91f42c7d831"
down_revision: Union[str, Sequence[str], None] = "53787c837466"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # RAG chunks table
    op.create_table(
        "rag_chunks",

        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),

        sa.Column(
            "course_id",
            sa.UUID(),
            nullable=False,
        ),

        sa.Column(
            "lecture_id",
            sa.UUID(),
            nullable=True,
        ),

        sa.Column(
            "note_id",
            sa.UUID(),
            nullable=True,
        ),

        sa.Column(
            "source_type",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "title",
            sa.String(length=500),
            nullable=False,
        ),

        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "chunk_index",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "metadata",
            postgresql.JSONB(),
            nullable=False,
        ),

        sa.Column(
            "embedding",
            Vector(384),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["course_id"],
            ["courses.id"],
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            ["lecture_id"],
            ["lectures.id"],
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            ["note_id"],
            ["notes.id"],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    # Normal indexes
    op.create_index(
        "ix_rag_chunks_course_id",
        "rag_chunks",
        ["course_id"],
    )

    op.create_index(
        "ix_rag_chunks_lecture_id",
        "rag_chunks",
        ["lecture_id"],
    )

    op.create_index(
        "ix_rag_chunks_note_id",
        "rag_chunks",
        ["note_id"],
    )

    # Vector similarity index
    op.execute(
        """
        CREATE INDEX ix_rag_chunks_embedding
        ON rag_chunks
        USING hnsw (embedding vector_cosine_ops)
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP INDEX IF EXISTS ix_rag_chunks_embedding"
    )

    op.drop_index(
        "ix_rag_chunks_note_id",
        table_name="rag_chunks",
    )

    op.drop_index(
        "ix_rag_chunks_lecture_id",
        table_name="rag_chunks",
    )

    op.drop_index(
        "ix_rag_chunks_course_id",
        table_name="rag_chunks",
    )

    op.drop_table("rag_chunks")