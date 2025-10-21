"""Update Transaction Amount Type

Revision ID: bb49903d0e1e
Revises: 63217df1520e
Create Date: 2025-10-21 22:02:33.074065

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bb49903d0e1e"
down_revision: Union[str, Sequence[str], None] = "63217df1520e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "transaction",
        "amount",
        existing_type=sa.Integer(),
        type_=sa.Float(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "transaction",
        "amount",
        existing_type=sa.Float(),
        type_=sa.Integer(),
        existing_nullable=False,
    )
