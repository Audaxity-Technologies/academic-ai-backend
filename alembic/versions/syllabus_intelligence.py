"""Persist reviewed versions, transcript segments, and alignment state.

Revision ID: syllabus_intelligence
Revises: add_syllabus_document_tables
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "syllabus_intelligence"
down_revision = "add_syllabus_document_tables"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("syllabus_documents", sa.Column("parsing_attempt", sa.Uuid()))
    op.add_column("syllabus_documents", sa.Column("hierarchy", JSONB))
    op.add_column("syllabus_documents", sa.Column("parsing_report", JSONB))
    op.add_column("syllabus_documents", sa.Column("confirmed_at", sa.DateTime(timezone=True)))
    op.alter_column("syllabus_documents", "is_active", server_default=sa.false())
    op.execute("UPDATE syllabus_documents SET is_active = false WHERE is_active")
    op.create_check_constraint("ck_syllabus_active_confirmed", "syllabus_documents",
                               "NOT is_active OR confirmed_at IS NOT NULL")
    op.create_unique_constraint("uq_syllabus_course_version", "syllabus_documents", ["course_id", "version"])
    op.create_index("uq_syllabus_active_course", "syllabus_documents", ["course_id"],
                    unique=True, postgresql_where=sa.text("is_active"))
    for name, target in (
        ("syllabus_document_id", "syllabus_documents"),
        ("syllabus_unit_id", "syllabus_units"),
        ("parent_id", "syllabus_topics"),
    ):
        op.add_column("syllabus_topics", sa.Column(name, sa.Uuid()))
        op.create_foreign_key(f"fk_syllabus_topics_{name}", "syllabus_topics", target,
                              [name], ["id"], ondelete="CASCADE")
        op.create_index(f"ix_syllabus_topics_{name}", "syllabus_topics", [name])
    op.add_column("syllabus_units", sa.Column("number", sa.String(80)))
    op.add_column("syllabus_units", sa.Column("pages", JSONB))
    op.add_column("syllabus_topics", sa.Column("number", sa.String(80)))
    op.add_column("syllabus_topics", sa.Column("pages", JSONB))
    op.add_column("transcripts", sa.Column("segments", JSONB))
    op.add_column("lectures", sa.Column("alignment_status", sa.String(30)))
    op.add_column("lectures", sa.Column("alignment_error", sa.String(255)))
    op.add_column("syllabus_mappings", sa.Column("explanation", sa.Text()))
    op.add_column("syllabus_mappings", sa.Column("needs_review", sa.Boolean(), nullable=False,
                                                 server_default=sa.false()))


def downgrade():
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM syllabus_documents WHERE hierarchy IS NOT NULL)
                OR EXISTS (SELECT 1 FROM transcripts WHERE segments IS NOT NULL)
                OR EXISTS (SELECT 1 FROM lectures WHERE alignment_status IS NOT NULL) THEN
                RAISE EXCEPTION 'Downgrade would discard syllabus or transcript data. Back up and migrate it first.';
            END IF;
        END $$
    """)
    for table, columns in (
        ("syllabus_mappings", ("explanation", "needs_review")),
        ("lectures", ("alignment_error", "alignment_status")),
        ("transcripts", ("segments",)),
        ("syllabus_topics", ("pages", "number")),
        ("syllabus_units", ("pages", "number")),
    ):
        for name in columns:
            op.drop_column(table, name)
    for name in ("parent_id", "syllabus_unit_id", "syllabus_document_id"):
        op.drop_index(f"ix_syllabus_topics_{name}", table_name="syllabus_topics")
        op.drop_constraint(f"fk_syllabus_topics_{name}", "syllabus_topics", type_="foreignkey")
        op.drop_column("syllabus_topics", name)
    op.drop_index("uq_syllabus_active_course", table_name="syllabus_documents")
    op.drop_constraint("uq_syllabus_course_version", "syllabus_documents", type_="unique")
    op.drop_constraint("ck_syllabus_active_confirmed", "syllabus_documents", type_="check")
    op.alter_column("syllabus_documents", "is_active", server_default=sa.true())
    for name in ("confirmed_at", "parsing_report", "hierarchy", "parsing_attempt"):
        op.drop_column("syllabus_documents", name)

