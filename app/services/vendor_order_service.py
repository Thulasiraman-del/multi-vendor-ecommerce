
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vendor import Vendor
from app.models.order import Order, OrderItem
from app.models.product import Product


async def get_vendor_order_items(
    db: AsyncSession,
    user_id: int,
    order_status: str | None = None,
    skip: int = 0,
    limit: int = 20,
):
    # Find the active vendor profile belonging to this user.
    vendor_result = await db.execute(
        select(Vendor).where(
            Vendor.user_id == user_id,
            Vendor.is_active.is_(True),
        )
    )

    vendor = vendor_result.scalar_one_or_none()

    if vendor is None:
        raise HTTPException(
            status_code=403,
            detail="Active vendor account required",
        )

    # Retrieve only order items for this vendor's products.
    query = (
        select(
            Order.id.label("order_id"),
            OrderItem.id.label("order_item_id"),
            Order.created_at.label("order_date"),
            Order.status.label("order_status"),
            OrderItem.status.label("item_status"),
            Product.id.label("product_id"),
            OrderItem.product_name.label("product_name"),
            OrderItem.quantity.label("quantity"),
            OrderItem.unit_price.label("unit_price"),
            OrderItem.subtotal.label("subtotal"),
            Order.user_id.label("customer_id"),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .join(Product, OrderItem.product_id == Product.id)
        .where(Product.vendor_id == vendor.id)
    )

    # Optionally filter by the overall order status.
    if order_status is not None:
        normalized_status = order_status.strip().lower()

        allowed_statuses = {
            "pending",
            "confirmed",
            "shipped",
            "delivered",
            "cancelled",
        }

        if normalized_status not in allowed_statuses:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Invalid order status. Allowed values: "
                    "pending, confirmed, shipped, delivered, cancelled"
                ),
            )

        query = query.where(
            Order.status == normalized_status
        )

    # Sort newest orders first, then apply pagination.
    query = query.order_by(
        Order.created_at.desc(),
        Order.id.desc(),
        OrderItem.id,
    )

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)

    return [
        dict(row)
        for row in result.mappings().all()
    ]