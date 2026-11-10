
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.cart import (
    CartItemCreate,
    CartItemUpdate,
    CartResponse,
)
from app.services.cart_service import (
    add_item_to_cart,
    get_cart,
    update_cart_item,
    remove_item_from_cart,
)


router = APIRouter(
    prefix="/cart",
    tags=["Shopping Cart"],
)


# GET CUSTOMER CART
@router.get(
    "",
    response_model=CartResponse,
)
async def get_my_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_cart(
        db=db,
        user_id=current_user.id,
    )


# ADD PRODUCT TO CART
@router.post(
    "/items",
    response_model=CartResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_product_to_cart(
    item_data: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await add_item_to_cart(
        db=db,
        user_id=current_user.id,
        product_id=item_data.product_id,
        quantity=item_data.quantity,
    )


# UPDATE CART ITEM QUANTITY
@router.put(
    "/items/{item_id}",
    response_model=CartResponse,
)
async def update_cart_item_quantity(
    item_id: int,
    item_data: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await update_cart_item(
        db=db,
        user_id=current_user.id,
        item_id=item_id,
        quantity=item_data.quantity,
    )


# REMOVE ITEM FROM CART
@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_cart_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await remove_item_from_cart(
        db=db,
        user_id=current_user.id,
        item_id=item_id,
    )

    return None
