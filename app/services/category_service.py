from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.category import Category
from app.schemas.category import CategoryCreate,CategoryResponse
async def get_category_by_name(session: AsyncSession, name: str):
    result = await session.execute(
        select(Category).where(Category.name == name)
    )
    return result.scalar_one_or_none()

async def create_category(db: AsyncSession, category_data: CategoryCreate):
    category = Category(
        name=category_data.name,
        description=category_data.description
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category