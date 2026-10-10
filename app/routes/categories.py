from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.category import Category
from app.schemas.category import CategoryCreate,CategoryResponse
from app.models.user import User
from app.services.category_service import (create_category,get_category_by_name)
router=APIRouter(
    prefix="/categories",
    tags=["Categories"]
)
@router.post("",response_model=CategoryResponse,status_code=status.HTTP_201_CREATED)
async def create_new_category(
    category_data:CategoryCreate,
    db:AsyncSession=Depends(get_db)
):
    existing_category=await get_category_by_name(db,category_data.name)
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category with this name already exists"
        )
    new_category=await create_category(db,category_data)
    return new_category
@router.get("",response_model=list[CategoryResponse])
async def get_categories(
    db:AsyncSession=Depends(get_db)
):
    result=await db.execute(
        select(Category).where(Category.is_active==True)
    )
    categories=result.scalars().all()
    return categories
@router.get("/{category_id}",response_model=CategoryResponse)
async def get_category(
    category_id:int,
    db:AsyncSession=Depends(get_db)
):
    result=await db.execute(
        select(Category).where(Category.id==category_id,Category.is_active==True)
    )
    category=result.scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category