"""Create Transaction Tables

Revision ID: 724be072873e
Revises: 61915a178a26
Create Date: 2025-09-26 11:33:06.084075

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '724be072873e'
down_revision: Union[str, Sequence[str], None] = '61915a178a26'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'user_credit',
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id'), nullable=False, primary_key=True, index=True),
        sa.Column('credits', sa.Integer, nullable=False, default=0),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_table(
        'transaction',
        sa.Column('id', sa.Integer, primary_key=True, index=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id'), nullable=False, index=True),
        sa.Column('amount', sa.Integer, nullable=False),
        sa.Column('timestamp', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('description', sa.String, nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('user_credit')
    op.drop_table('transaction')
