"""add syllabus document tables and embedding column

Revision ID: add_syllabus_document_tables
Revises: c4a8e7d2f091
Create Date: 2026-11-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = 'add_syllabus_document_tables'
down_revision: Union[str, Sequence[str], None] = 'c4a8e7d2f091'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add embedding column to syllabus_topics using pgvector VECTOR
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.add_column(
        'syllabus_topics',
        sa.Column('embedding', Vector(384), nullable=True)
    )

    # Create syllabus_documents table
    op.create_table(
        'syllabus_documents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('course_id', sa.UUID(), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=1000), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('parsing_status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('parsing_error', sa.Text(), nullable=True),
        sa.Column('parsed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_syllabus_documents_course_id'), 'syllabus_documents', ['course_id'], unique=False)

    # Create syllabus_units table
    op.create_table(
        'syllabus_units',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('syllabus_document_id', sa.UUID(), nullable=False),
        sa.Column('unit_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('page_reference', sa.String(length=100), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['syllabus_document_id'], ['syllabus_documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_syllabus_units_syllabus_document_id'), 'syllabus_units', ['syllabus_document_id'], unique=False)

    # Create syllabus_subtopics table
    op.create_table(
        'syllabus_subtopics',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('syllabus_unit_id', sa.UUID(), nullable=False),
        sa.Column('topic_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('page_reference', sa.String(length=100), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['syllabus_unit_id'], ['syllabus_units.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_syllabus_subtopics_syllabus_unit_id'), 'syllabus_subtopics', ['syllabus_unit_id'], unique=False)

    # Add version column to syllabus_documents for versioning
    op.add_column(
        'syllabus_documents',
        sa.Column('version', sa.Integer(), nullable=False, server_default='1')
    )
    op.add_column(
        'syllabus_documents',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true')
    )
    op.create_index('ix_syllabus_documents_course_version', 'syllabus_documents', ['course_id', 'version'], unique=False)

    # Add unique constraint to syllabus_mappings to prevent duplicates
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM syllabus_mappings GROUP BY lecture_id, syllabus_topic_id
                       HAVING count(*) > 1) THEN
                RAISE EXCEPTION 'Duplicate syllabus mappings found. Review and reconcile them before upgrading.';
            END IF;
        END $$
    """)
    op.create_unique_constraint('uq_syllabus_mappings_lecture_topic', 'syllabus_mappings', ['lecture_id', 'syllabus_topic_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM syllabus_documents) THEN
                RAISE EXCEPTION 'Downgrade would remove syllabus documents. Back up and migrate them first.';
            END IF;
        END $$
    """)
    # Drop unique constraint from syllabus_mappings
    op.drop_constraint('uq_syllabus_mappings_lecture_topic', 'syllabus_mappings', type_='unique')

    # Drop version columns from syllabus_documents
    op.drop_index('ix_syllabus_documents_course_version', table_name='syllabus_documents')
    op.drop_column('syllabus_documents', 'is_active')
    op.drop_column('syllabus_documents', 'version')

    op.drop_index(op.f('ix_syllabus_subtopics_syllabus_unit_id'), table_name='syllabus_subtopics')
    op.drop_table('syllabus_subtopics')

    op.drop_index(op.f('ix_syllabus_units_syllabus_document_id'), table_name='syllabus_units')
    op.drop_table('syllabus_units')

    op.drop_index(op.f('ix_syllabus_documents_course_id'), table_name='syllabus_documents')
    op.drop_table('syllabus_documents')

    op.drop_column('syllabus_topics', 'embedding')
