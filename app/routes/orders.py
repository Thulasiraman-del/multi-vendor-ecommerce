from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.order import OrderResponse, OrderItemStatusUpdate
from app.services.order_service import (
    create_order_from_cart,
    get_order_by_id,
    get_user_orders,
    cancel_order,
    update_order_item_status,
)
router = APIRouter(prefix="/orders", tags=["Orders"])
@router.post(
    "/checkout",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def checkout(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create an order from the current user's cart."""
    if current_user.role != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can checkout",
        )
    return await create_order_from_cart(db, current_user.id)
@router.get("/", response_model=list[OrderResponse])
async def list_my_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List orders belonging to the current user."""
    return await get_user_orders(db, current_user.id)
@router.get("/{order_id}", response_model=OrderResponse)
async def get_my_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get an order belonging to the current user."""
    order = await get_order_by_id(
        db,
        current_user.id,
        order_id,
    )
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return order
@router.patch(
    "/{order_id}/cancel",
    response_model=OrderResponse,
)
async def cancel_my_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel the customer's own pending order."""
    if current_user.role != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can cancel orders",
        )
    return await cancel_order(
        db,
        current_user.id,
        order_id,
    )
@router.patch(
    "/{order_id}/items/{item_id}/status",
    response_model=OrderResponse,
)
async def update_item_fulfillment(
    order_id: int,
    item_id: int,
    payload: OrderItemStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update fulfillment for an item belonging to the current vendor."""
    if current_user.role != "vendor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only vendors can update fulfillment",
        )
    return await update_order_item_status(
        db,
        current_user.id,
        order_id,
        item_id,
        payload.status,
    )
