"""add product vendor and category indexes

Revision ID: 9ccf6f3ae910
Revises: da761c90a15d
Create Date: 2026-11-01 09:34:49.327613

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '9ccf6f3ae910'
down_revision: Union[str, Sequence[str], None] = 'da761c90a15d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add indexes for product category and vendor lookups."""
    op.create_index(
        'ix_products_category_id',
        'products',
        ['category_id'],
        unique=False,
    )

    op.create_index(
        'ix_products_vendor_id',
        'products',
        ['vendor_id'],
        unique=False,
    )


def downgrade() -> None:
    """Remove product category and vendor indexes."""
    op.drop_index(
        'ix_products_vendor_id',
        table_name='products',
    )

    op.drop_index(
        'ix_products_category_id',
        table_name='products',
    )