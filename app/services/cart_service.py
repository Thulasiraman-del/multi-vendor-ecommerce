
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import Cart, CartItem
from app.models.product import Product


async def _get_or_create_locked_cart(
    db: AsyncSession,
    user_id: int,
) -> Cart:
    """
    Get the customer's cart while locking it.

    If it doesn't exist, create it safely using PostgreSQL
    ON CONFLICT to handle simultaneous cart creation.
    """

    result = await db.execute(
        select(Cart)
        .where(Cart.user_id == user_id)
        .with_for_update()
    )

    cart = result.scalar_one_or_none()

    if cart is not None:
        return cart

    # Safely handle two requests creating the same cart.
    statement = (
        pg_insert(Cart)
        .values(user_id=user_id)
        .on_conflict_do_nothing(
            index_elements=[Cart.user_id]
        )
    )

    await db.execute(statement)

    # Fetch and lock the cart, whether newly created
    # or created by another concurrent request.
    result = await db.execute(
        select(Cart)
        .where(Cart.user_id == user_id)
        .with_for_update()
    )

    cart = result.scalar_one()

    return cart


async def get_or_create_cart(
    db: AsyncSession,
    user_id: int,
) -> Cart:
    cart = await _get_or_create_locked_cart(
        db,
        user_id,
    )

    await db.commit()
    await db.refresh(cart)

    return cart


async def add_item_to_cart(
    db: AsyncSession,
    user_id: int,
    product_id: int,
    quantity: int,
) -> Cart:
    try:
        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be greater than zero",
            )

        # Always lock the cart first.
        cart = await _get_or_create_locked_cart(
            db,
            user_id,
        )

        # Lock the product after the cart.
        result = await db.execute(
            select(Product)
            .where(
                Product.id == product_id,
                Product.is_active.is_(True),
            )
            .with_for_update()
        )

        product = result.scalar_one_or_none()

        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found or inactive",
            )

        # Find an existing cart item.
        result = await db.execute(
            select(CartItem)
            .where(
                CartItem.cart_id == cart.id,
                CartItem.product_id == product_id,
            )
            .with_for_update()
        )

        cart_item = result.scalar_one_or_none()

        new_quantity = quantity

        if cart_item is not None:
            new_quantity += cart_item.quantity

        if new_quantity > product.stock_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Requested quantity exceeds available stock",
            )

        if cart_item is not None:
            cart_item.quantity = new_quantity
        else:
            db.add(
                CartItem(
                    cart_id=cart.id,
                    product_id=product_id,
                    quantity=quantity,
                )
            )

        await db.commit()

    except Exception:
        await db.rollback()
        raise

    return await get_cart(db, user_id)


async def update_cart_item(
    db: AsyncSession,
    user_id: int,
    item_id: int,
    quantity: int,
) -> Cart:
    try:
        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be greater than zero",
            )

        # Lock cart first.
        cart = await _get_or_create_locked_cart(
            db,
            user_id,
        )

        # Lock the requested item.
        result = await db.execute(
            select(CartItem)
            .where(
                CartItem.id == item_id,
                CartItem.cart_id == cart.id,
            )
            .with_for_update()
        )

        cart_item = result.scalar_one_or_none()

        if cart_item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart item not found",
            )

        # Lock product after cart and cart item.
        result = await db.execute(
            select(Product)
            .where(
                Product.id == cart_item.product_id,
                Product.is_active.is_(True),
            )
            .with_for_update()
        )

        product = result.scalar_one_or_none()

        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found or inactive",
            )

        if quantity > product.stock_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Requested quantity exceeds available stock",
            )

        cart_item.quantity = quantity

        await db.commit()

    except Exception:
        await db.rollback()
        raise

    return await get_cart(db, user_id)


async def remove_item_from_cart(
    db: AsyncSession,
    user_id: int,
    item_id: int,
) -> None:
    try:
        # Lock cart first.
        cart = await _get_or_create_locked_cart(
            db,
            user_id,
        )

        result = await db.execute(
            select(CartItem)
            .where(
                CartItem.id == item_id,
                CartItem.cart_id == cart.id,
            )
            .with_for_update()
        )

        cart_item = result.scalar_one_or_none()

        if cart_item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart item not found",
            )

        await db.delete(cart_item)
        await db.commit()

    except Exception:
        await db.rollback()
        raise


async def get_cart(
    db: AsyncSession,
    user_id: int,
) -> Cart:
    cart = await get_or_create_cart(
        db,
        user_id,
    )

    result = await db.execute(
        select(Cart)
        .options(selectinload(Cart.items))
        .where(Cart.id == cart.id)
    )

    return result.scalar_one()
