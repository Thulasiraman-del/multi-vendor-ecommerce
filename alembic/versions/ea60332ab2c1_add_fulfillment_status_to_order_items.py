
"""add fulfillment status to order items

Revision ID: ea60332ab2c1
Revises: 5ed89702d2f1
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ea60332ab2c1"
down_revision: Union[str, Sequence[str], None] = "5ed89702d2f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "order_items",
        sa.Column(
            "status",
            sa.String(length=30),
            server_default="pending",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("order_items", "status")