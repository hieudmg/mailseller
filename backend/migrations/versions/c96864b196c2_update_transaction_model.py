"""Update transaction model

Revision ID: c96864b196c2
Revises: 1f7027e49f93
Create Date: 2025-10-27 13:57:26.770070

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c96864b196c2"
down_revision: Union[str, Sequence[str], None] = "1f7027e49f93"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "transaction",
        sa.Column(
            "type", sa.String(length=50), server_default="purchase", nullable=False
        ),
    )
    op.execute(
        """
        UPDATE transaction
        SET type = CASE
            WHEN amount < 0 THEN 'purchase'
            WHEN amount > 0 THEN 'admin_deposit'
            ELSE 'purchase'
        END
    """
    )
    op.create_index("ix_transaction_type", "transaction", ["type"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_transaction_type", table_name="transaction")

    # Drop column
    op.drop_column("transaction", "type")
