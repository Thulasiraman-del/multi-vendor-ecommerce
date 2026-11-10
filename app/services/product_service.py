
from decimal import Decimal

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.product import Product
from app.schemas.product import ProductCreate


async def get_product_by_sku(
    db: AsyncSession,
    sku: str,
):
    result = await db.execute(
        select(Product).where(
            Product.sku == sku
        )
    )
    return result.scalar_one_or_none()


async def get_category_by_id(
    db: AsyncSession,
    category_id: int,
):
    result = await db.execute(
        select(Category).where(
            Category.id == category_id,
            Category.is_active.is_(True),
        )
    )
    return result.scalar_one_or_none()


async def create_product(
    db: AsyncSession,
    vendor_id: int,
    product_data: ProductCreate,
):
    product = Product(
        vendor_id=vendor_id,
        category_id=product_data.category_id,
        name=product_data.name,
        description=product_data.description,
        sku=product_data.sku,
        price=product_data.price,
        stock_quantity=product_data.stock_quantity,
    )

    db.add(product)
    await db.commit()
    await db.refresh(product)

    return product


async def search_products(
    db: AsyncSession,
    search: str | None = None,
    category_id: int | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    sort_by: str = "id",
    sort_order: str = "asc",
    page: int = 1,
    limit: int = 20,
):
    # Validate pagination
    if page < 1:
        raise ValueError("Page must be greater than or equal to 1")

    if limit < 1 or limit > 100:
        raise ValueError("Limit must be between 1 and 100")

    # Common filters
    filters = [
        Product.is_active.is_(True)
    ]

    # Search name and description
    if search and search.strip():
        search_term = f"%{search.strip()}%"

        filters.append(
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term),
            )
        )

    # Category filter
    if category_id is not None:
        filters.append(
            Product.category_id == category_id
        )

    # Minimum price filter
    if min_price is not None:
        filters.append(
            Product.price >= min_price
        )

    # Maximum price filter
    if max_price is not None:
        filters.append(
            Product.price <= max_price
        )

    # Count matching products
    count_query = (
        select(func.count())
        .select_from(Product)
        .where(*filters)
    )

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # Calculate pagination
    offset = (page - 1) * limit
    pages = (total + limit - 1) // limit

    # Allowed sorting columns
    sort_columns = {
        "id": Product.id,
        "name": Product.name,
        "price": Product.price,
    }

    sort_column = sort_columns.get(
        sort_by,
        Product.id,
    )

    # Build product query
    query = select(Product).where(*filters)

    # Apply sorting
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Stable secondary sorting
    if sort_by != "id":
        query = query.order_by(Product.id.asc())

    # Database pagination
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    products = result.scalars().all()

    return {
        "items": products,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }
