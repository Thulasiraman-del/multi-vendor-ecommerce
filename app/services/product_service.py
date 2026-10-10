from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.product import Product
from app.schemas.product import ProductCreate


async def get_product_by_sku(
    db: AsyncSession,
    sku: str
):
    result = await db.execute(
        select(Product).where(
            Product.sku == sku
        )
    )

    return result.scalar_one_or_none()


async def get_category_by_id(
    db: AsyncSession,
    category_id: int
):
    result = await db.execute(
        select(Category).where(
            Category.id == category_id,
            Category.is_active == True
        )
    )

    return result.scalar_one_or_none()


async def create_product(
    db: AsyncSession,
    vendor_id: int,
    product_data: ProductCreate
):
    product = Product(
        vendor_id=vendor_id,
        category_id=product_data.category_id,
        name=product_data.name,
        description=product_data.description,
        sku=product_data.sku,
        price=product_data.price,
        stock_quantity=product_data.stock_quantity
    )

    db.add(product)

    await db.commit()
    await db.refresh(product)

    return product