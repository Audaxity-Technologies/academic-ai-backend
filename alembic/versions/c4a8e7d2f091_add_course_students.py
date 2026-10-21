"""add course student enrollments

Revision ID: c4a8e7d2f091
Revises: 39bad72d5969
Create Date: 2026-10-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4a8e7d2f091"
down_revision: Union[str, Sequence[str], None] = "39bad72d5969"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "course_students",
        sa.Column("course_id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["course_id"], ["courses.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["student_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("course_id", "student_id"),
    )
    op.create_index(
        "ix_course_students_student_id",
        "course_students",
        ["student_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_course_students_student_id",
        table_name="course_students",
    )
    op.drop_table("course_students")
