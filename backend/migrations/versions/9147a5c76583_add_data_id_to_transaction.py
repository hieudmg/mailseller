"""add_data_id_to_transaction

Revision ID: 9147a5c76583
Revises: 9d2202158584
Create Date: 2025-10-07 00:18:17.393956

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9147a5c76583'
down_revision: Union[str, Sequence[str], None] = '9d2202158584'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('transaction', sa.Column('data_id', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('transaction', 'data_id')
