"""create_user_token_table

Revision ID: 9d2202158584
Revises: b41c0e6c35fe
Create Date: 2025-10-06 23:21:59.474618

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d2202158584'
down_revision: Union[str, Sequence[str], None] = 'b41c0e6c35fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'user_token',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_user_token_user_id'), 'user_token', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_token_token'), 'user_token', ['token'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_user_token_token'), table_name='user_token')
    op.drop_index(op.f('ix_user_token_user_id'), table_name='user_token')
    op.drop_table('user_token')
