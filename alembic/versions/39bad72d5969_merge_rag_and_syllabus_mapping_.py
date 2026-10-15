"""merge rag and syllabus mapping migrations

Revision ID: 39bad72d5969
Revises: a91f42c7d831, 742effa7f289
Create Date: 2026-10-09 15:19:13.519674

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39bad72d5969'
down_revision: Union[str, Sequence[str], None] = ('a91f42c7d831', '742effa7f289')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
