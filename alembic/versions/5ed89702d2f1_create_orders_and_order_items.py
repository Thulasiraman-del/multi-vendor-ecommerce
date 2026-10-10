"""create orders and order items
Revision ID: 5ed89702d2f1
Revises: 3d04e5ae6c3c
"""
from alembic import op
import sqlalchemy as sa
revision = "5ed89702d2f1"
down_revision = "3d04e5ae6c3c"
branch_labels = None
depends_on = None
def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "total_amount",
            sa.Numeric(10, 2),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_orders_user_id",
        "orders",
        ["user_id"],
    )
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "order_id",
            sa.Integer(),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("products.id"),
            nullable=False,
        ),
        sa.Column(
            "product_name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "quantity",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "unit_price",
            sa.Numeric(10, 2),
            nullable=False,
        ),
        sa.Column(
            "subtotal",
            sa.Numeric(10, 2),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_order_items_order_id",
        "order_items",
        ["order_id"],
    )
def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS order_items CASCADE")
    op.execute("DROP TABLE IF EXISTS orders CASCADE")
