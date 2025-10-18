"""create_data_pool_tables

Revision ID: 934d91d41794
Revises: 9147a5c76583
Create Date: 2025-10-18 22:22:28.396513

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '934d91d41794'
down_revision: Union[str, Sequence[str], None] = '9147a5c76583'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create data_pool table
    op.create_table(
        'data_pool',
        sa.Column('id', sa.Integer, primary_key=True, index=True, autoincrement=True),
        sa.Column('type', sa.String, nullable=False, index=True),
        sa.Column('data', sa.String, nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # Create data_pool_sold table
    op.create_table(
        'data_pool_sold',
        sa.Column('pool_id', sa.Integer, sa.ForeignKey('data_pool.id'), primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id'), nullable=False, index=True),
        sa.Column('sold_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('data_pool_sold')
    op.drop_table('data_pool')
