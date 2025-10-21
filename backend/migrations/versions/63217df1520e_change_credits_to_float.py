"""Change credits to float

Revision ID: 63217df1520e
Revises: 934d91d41794
Create Date: 2025-10-21 21:02:14.577912

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "63217df1520e"
down_revision: Union[str, Sequence[str], None] = "934d91d41794"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "user_credit",
        "credits",
        existing_type=sa.Integer(),
        type_=sa.Float(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "user_credit",
        "credits",
        existing_type=sa.Float(),
        type_=sa.Integer(),
        existing_nullable=False,
    )
