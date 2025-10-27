"""Add custom_discount to user model

Revision ID: 1f7027e49f93
Revises: bb49903d0e1e
Create Date: 2025-10-24 15:30:30.845850

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f7027e49f93'
down_revision: Union[str, Sequence[str], None] = 'bb49903d0e1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add custom_discount column to user table."""
    op.add_column(
        "user",
        sa.Column("custom_discount", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    """Remove custom_discount column from user table."""
    op.drop_column("user", "custom_discount")
