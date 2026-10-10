
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.cart import CartItem
from app.models.user import User
from app.schemas.cart import (
    CartItemCreate,
    CartItemUpdate,
    CartResponse,
)
from app.services.cart_service import (
    add_item_to_cart,
    get_cart,
)


router = APIRouter(
    prefix="/cart",
    tags=["Shopping Cart"]
)


# GET MY CART
@router.get(
    "",
    response_model=CartResponse
)
async def get_my_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cart = await get_cart(db, current_user.id)
    return cart


# ADD PRODUCT TO CART
@router.post(
    "/items",
    response_model=CartResponse,
    status_code=status.HTTP_201_CREATED
)
async def add_product_to_cart(
    item_data: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cart = await add_item_to_cart(
        db=db,
        user_id=current_user.id,
        product_id=item_data.product_id,
        quantity=item_data.quantity,
    )

    # Reload the cart with its items
    cart = await get_cart(db, current_user.id)
    return cart


# UPDATE CART ITEM QUANTITY
@router.put(
    "/items/{item_id}",
    response_model=CartResponse
)
async def update_cart_item(
    item_id: int,
    item_data: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Find this customer's cart
    cart = await get_cart(db, current_user.id)

    if not cart.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )

    # Find the requested item within this cart
    result = await db.execute(
        select(CartItem).where(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id
        )
    )

    cart_item = result.scalar_one_or_none()

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )

    # Check current product stock
    from app.models.product import Product

    result = await db.execute(
        select(Product).where(
            Product.id == cart_item.product_id,
            Product.is_active.is_(True)
        )
    )

    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or inactive"
        )

    if item_data.quantity > product.stock_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested quantity exceeds available stock"
        )

    cart_item.quantity = item_data.quantity

    await db.commit()

    return await get_cart(db, current_user.id)


# REMOVE ITEM FROM CART
@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def remove_cart_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cart = await get_cart(db, current_user.id)

    if not cart.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )

    result = await db.execute(
        select(CartItem).where(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id
        )
    )

    cart_item = result.scalar_one_or_none()

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )

    await db.delete(cart_item)
    await db.commit()

    return None