
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.product import Product
from app.models.user import User
from app.models.vendor import Vendor
from app.schemas.product import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from app.services.product_service import (
    create_product,
    get_category_by_id,
    get_product_by_sku,
)


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


# --------------------------------------------------
# VENDOR AUTHORIZATION
# --------------------------------------------------

async def get_active_vendor(
    current_user: User,
    db: AsyncSession,
) -> Vendor:
    # Only users with the vendor role can manage products
    if current_user.role != "vendor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only vendor accounts can manage products",
        )

    # Find the vendor profile belonging to the current user
    result = await db.execute(
        select(Vendor).where(
            Vendor.user_id == current_user.id
        )
    )

    vendor = result.scalar_one_or_none()

    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vendor profile not found",
        )

    # Only active vendors can manage products
    if not vendor.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vendor account is not active",
        )

    return vendor


# --------------------------------------------------
# CREATE PRODUCT
# --------------------------------------------------

@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_new_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    vendor = await get_active_vendor(current_user, db)

    # Verify that the category exists
    category = await get_category_by_id(
        db,
        product_data.category_id,
    )

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Prevent duplicate SKUs
    existing_product = await get_product_by_sku(
        db,
        product_data.sku,
    )

    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product SKU already exists",
        )

    # Create the product under the authenticated vendor
    product = await create_product(
        db,
        vendor.id,
        product_data,
    )

    return product


# --------------------------------------------------
# GET ALL ACTIVE PRODUCTS
# --------------------------------------------------

@router.get(
    "",
    response_model=list[ProductResponse],
)
async def get_products(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Product).where(
            Product.is_active.is_(True)
        )
    )

    products = result.scalars().all()

    return products


# --------------------------------------------------
# GET MY PRODUCTS
# --------------------------------------------------

@router.get(
    "/vendor/me",
    response_model=list[ProductResponse],
)
async def get_my_products(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Require an active vendor profile
    vendor_result = await db.execute(
        select(Vendor).where(
            Vendor.user_id == current_user.id
        )
    )

    vendor = vendor_result.scalar_one_or_none()

    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vendor profile not found",
        )

    if not vendor.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vendor account is not active",
        )

    # Return only this vendor's active products
    result = await db.execute(
        select(Product).where(
            Product.vendor_id == vendor.id,
            Product.is_active.is_(True),
        )
    )

    products = result.scalars().all()

    return products


# --------------------------------------------------
# UPDATE PRODUCT
# --------------------------------------------------

@router.put(
    "/{product_id}",
    response_model=ProductResponse,
)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    vendor = await get_active_vendor(current_user, db)

    # Find the requested product
    result = await db.execute(
        select(Product).where(
            Product.id == product_id
        )
    )

    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Enforce product ownership
    if product.vendor_id != vendor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own products",
        )

    # Validate the category if it was supplied
    if product_data.category_id is not None:
        category = await get_category_by_id(
            db,
            product_data.category_id,
        )

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )

    # Update only fields supplied by the client
    update_data = product_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)

    return product


# --------------------------------------------------
# GET PRODUCT BY ID
# --------------------------------------------------

@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.is_active.is_(True),
        )
    )

    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product


# --------------------------------------------------
# DELETE PRODUCT (SOFT DELETE)
# --------------------------------------------------

@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    vendor = await get_active_vendor(current_user, db)

    # Find the requested product
    result = await db.execute(
        select(Product).where(
            Product.id == product_id
        )
    )

    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Enforce product ownership
    if product.vendor_id != vendor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own products",
        )

    # Soft-delete the product
    product.is_active = False

    await db.commit()

    return None