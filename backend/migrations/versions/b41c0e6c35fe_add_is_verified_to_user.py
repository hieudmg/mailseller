"""add_is_verified_to_user

Revision ID: b41c0e6c35fe
Revises: 724be072873e
Create Date: 2025-10-03 22:38:47.206785

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b41c0e6c35fe'
down_revision: Union[str, Sequence[str], None] = '724be072873e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('user', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('user', 'is_verified')
