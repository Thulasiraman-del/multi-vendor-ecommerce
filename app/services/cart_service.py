
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import Cart, CartItem
from app.models.product import Product


async def get_or_create_cart(
    db: AsyncSession,
    user_id: int
) -> Cart:
    result = await db.execute(
        select(Cart).where(Cart.user_id == user_id)
    )

    cart = result.scalar_one_or_none()

    if cart is not None:
        return cart

    cart = Cart(user_id=user_id)
    db.add(cart)

    await db.commit()
    await db.refresh(cart)

    return cart


async def add_item_to_cart(
    db: AsyncSession,
    user_id: int,
    product_id: int,
    quantity: int
) -> Cart:
    # Find an active product
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.is_active.is_(True)
        )
    )

    product = result.scalar_one_or_none()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or inactive"
        )

    cart = await get_or_create_cart(db, user_id)

    # Find an existing item for this product
    result = await db.execute(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product_id
        )
    )

    cart_item = result.scalar_one_or_none()

    new_quantity = quantity

    if cart_item is not None:
        new_quantity += cart_item.quantity

    if new_quantity > product.stock_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested quantity exceeds available stock"
        )

    if cart_item is not None:
        cart_item.quantity = new_quantity
    else:
        db.add(
            CartItem(
                cart_id=cart.id,
                product_id=product_id,
                quantity=quantity
            )
        )

    await db.commit()

    return cart


async def get_cart(
    db: AsyncSession,
    user_id: int
) -> Cart:
    # Ensure the customer has a saved cart
    cart = await get_or_create_cart(db, user_id)

    # Load cart items explicitly for async SQLAlchemy
    result = await db.execute(
        select(Cart)
        .options(selectinload(Cart.items))
        .where(Cart.id == cart.id)
    )

    return result.scalar_one()


async def remove_item_from_cart(
    db: AsyncSession,
    user_id: int,
    item_id: int
) -> None:
    cart = await get_or_create_cart(db, user_id)

    result = await db.execute(
        select(CartItem).where(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id
        )
    )

    cart_item = result.scalar_one_or_none()

    if cart_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )

    await db.delete(cart_item)
    await db.commit()