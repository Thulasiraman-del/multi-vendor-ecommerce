
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.vendor import VendorCreate, VendorResponse
from app.schemas.vendor_order import VendorOrderItemResponse
from app.services.vendor_service import (
    create_vendor,
    get_vendor_by_user_id,
)
from app.services.vendor_order_service import get_vendor_order_items


router = APIRouter(
    prefix="/vendors",
    tags=["Vendors"],
)


@router.post(
    "",
    response_model=VendorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_vendor_profile(
    vendor_data: VendorCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing_vendor = await get_vendor_by_user_id(
        db,
        current_user.id,
    )

    if existing_vendor:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vendor profile already exists",
        )

    vendor = await create_vendor(
        db,
        current_user.id,
        vendor_data,
    )

    return vendor


@router.get(
    "/me/orders",
    response_model=list[VendorOrderItemResponse],
)
async def list_my_vendor_orders(
    order_status: str | None = Query(
        default=None,
        description=(
            "Filter by order status: pending, confirmed, "
            "shipped, delivered, or cancelled"
        ),
    ),
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of order items to skip",
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of order items to return",
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "vendor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vendor account required",
        )

    return await get_vendor_order_items(
        db,
        current_user.id,
        order_status=order_status,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/me",
    response_model=VendorResponse,
)
async def get_my_vendor(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    vendor = await get_vendor_by_user_id(
        db,
        current_user.id,
    )

    if vendor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor profile not found",
        )

    return vendor
