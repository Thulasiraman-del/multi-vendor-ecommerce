from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.vendor import Vendor
async def create_order_from_cart(
    db: AsyncSession,
    user_id: int,
) -> Order:
    try:
        result = await db.execute(
            select(Cart)
            .where(Cart.user_id == user_id)
            .with_for_update()
        )
        cart = result.scalar_one_or_none()
        if cart is None:
            raise HTTPException(
                status_code=400,
                detail="Your cart is empty",
            )
        result = await db.execute(
            select(CartItem)
            .where(CartItem.cart_id == cart.id)
            .order_by(CartItem.id)
        )
        cart_items = list(result.scalars().all())
        if not cart_items:
            raise HTTPException(
                status_code=400,
                detail="Your cart is empty",
            )
        product_ids = sorted(
            {item.product_id for item in cart_items}
        )
        result = await db.execute(
            select(Product)
            .where(Product.id.in_(product_ids))
            .order_by(Product.id)
            .with_for_update()
        )
        products = {
            product.id: product
            for product in result.scalars().all()
        }
        for item in cart_items:
            product = products.get(item.product_id)
            if product is None or not product.is_active:
                raise HTTPException(
                    status_code=400,
                    detail=f"Product {item.product_id} is unavailable",
                )
            if item.quantity <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Quantity must be greater than zero",
                )
            if item.quantity > product.stock_quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for {product.name}",
                )
        order = Order(
            user_id=user_id,
            status="pending",
            total_amount=Decimal("0.00"),
        )
        db.add(order)
        await db.flush()
        total_amount = Decimal("0.00")
        for item in cart_items:
            product = products[item.product_id]
            unit_price = Decimal(str(product.price))
            subtotal = unit_price * item.quantity
            total_amount += subtotal
            db.add(
                OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    product_name=product.name,
                    quantity=item.quantity,
                    unit_price=unit_price,
                    subtotal=subtotal,
                    status="pending",
                )
            )
            product.stock_quantity -= item.quantity
            await db.delete(item)
        order.total_amount = total_amount
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order.id)
    )
    return result.scalar_one()
async def get_order_by_id(
    db: AsyncSession,
    user_id: int,
    order_id: int,
) -> Order | None:
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(
            Order.id == order_id,
            Order.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()
async def get_user_orders(
    db: AsyncSession,
    user_id: int,
) -> list[Order]:
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc(), Order.id.desc())
    )
    return list(result.scalars().all())
async def cancel_order(
    db: AsyncSession,
    user_id: int,
    order_id: int,
) -> Order:
    try:
        result = await db.execute(
            select(Order)
            .where(
                Order.id == order_id,
                Order.user_id == user_id,
            )
            .with_for_update()
        )
        order = result.scalar_one_or_none()
        if order is None:
            raise HTTPException(
                status_code=404,
                detail="Order not found",
            )
        if order.status != "pending":
            raise HTTPException(
                status_code=400,
                detail="Only pending orders can be cancelled",
            )
        result = await db.execute(
            select(OrderItem)
            .where(OrderItem.order_id == order.id)
            .order_by(OrderItem.product_id)
        )
        items = list(result.scalars().all())
        product_ids = sorted({item.product_id for item in items})
        result = await db.execute(
            select(Product)
            .where(Product.id.in_(product_ids))
            .order_by(Product.id)
            .with_for_update()
        ) if product_ids else None
        products = (
            {product.id: product for product in result.scalars().all()}
            if result is not None
            else {}
        )
        for item in items:
            product = products.get(item.product_id)
            if product is not None:
                product.stock_quantity += item.quantity
            item.status = "cancelled"
        order.status = "cancelled"
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id, Order.user_id == user_id)
    )
    return result.scalar_one()
async def update_order_item_status(
    db: AsyncSession,
    user_id: int,
    order_id: int,
    item_id: int,
    new_status: str,
) -> Order:
    try:
        if new_status not in {"confirmed", "shipped", "delivered"}:
            raise HTTPException(
                status_code=400,
                detail="Invalid fulfillment status",
            )
        result = await db.execute(
            select(Vendor)
            .where(
                Vendor.user_id == user_id,
                Vendor.is_active.is_(True),
            )
        )
        vendor = result.scalar_one_or_none()
        if vendor is None:
            raise HTTPException(
                status_code=403,
                detail="An active vendor profile is required",
            )
        result = await db.execute(
            select(OrderItem)
            .join(Order, Order.id == OrderItem.order_id)
            .join(Product, Product.id == OrderItem.product_id)
            .where(
                Order.id == order_id,
                OrderItem.id == item_id,
                Product.vendor_id == vendor.id,
            )
            .with_for_update()
        )
        item = result.scalar_one_or_none()
        if item is None:
            raise HTTPException(
                status_code=404,
                detail="Order item not found for this vendor",
            )
        transitions = {
            "pending": {"confirmed"},
            "confirmed": {"shipped"},
            "shipped": {"delivered"},
        }
        if new_status not in transitions.get(item.status, set()):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot change item status from {item.status} to {new_status}",
            )
        item.status = new_status
        result = await db.execute(
            select(Order)
            .where(Order.id == order_id)
            .with_for_update()
        )
        order = result.scalar_one()
        result = await db.execute(
            select(OrderItem)
            .where(OrderItem.order_id == order_id)
        )
        items = list(result.scalars().all())
        statuses = {order_item.status for order_item in items}
        if statuses and statuses == {"delivered"}:
            order.status = "delivered"
        elif "shipped" in statuses or "delivered" in statuses:
            order.status = "shipped"
        elif "confirmed" in statuses:
            order.status = "confirmed"
        else:
            order.status = "pending"
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )
    return result.scalar_one()
