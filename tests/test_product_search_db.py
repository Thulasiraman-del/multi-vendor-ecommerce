
from decimal import Decimal

import pytest

from app.models.user import User
from app.models.vendor import Vendor
from app.models.category import Category
from app.models.product import Product
from app.services.product_service import search_products


@pytest.fixture
def sample_data():
    return [
        {
            "name": "Python Laptop",
            "description": "Laptop for Python development",
            "sku": "LAP-001",
            "price": Decimal("75000.00"),
            "category": "Electronics",
            "is_active": True,
        },
        {
            "name": "Python Keyboard",
            "description": "Mechanical keyboard",
            "sku": "KEY-001",
            "price": Decimal("5000.00"),
            "category": "Electronics",
            "is_active": True,
        },
        {
            "name": "Java Book",
            "description": "Programming book",
            "sku": "BOOK-001",
            "price": Decimal("800.00"),
            "category": "Books",
            "is_active": True,
        },
        {
            "name": "Old Laptop",
            "description": "Inactive laptop",
            "sku": "LAP-002",
            "price": Decimal("40000.00"),
            "category": "Electronics",
            "is_active": False,
        },
    ]


async def insert_sample_products(db, sample_data):
    user = User(
        full_name="Test Vendor",
        email="vendor@example.com",
        password_hash="test-password",
        role="vendor",
    )
    db.add(user)
    await db.flush()

    vendor = Vendor(
        user_id=user.id,
        business_name="Test Store",
        is_active=True,
    )
    db.add(vendor)

    electronics = Category(name="Electronics")
    books = Category(name="Books")

    db.add_all([electronics, books])
    await db.flush()

    categories = {
        "Electronics": electronics.id,
        "Books": books.id,
    }

    for item in sample_data:
        db.add(
            Product(
                vendor_id=vendor.id,
                category_id=categories[item["category"]],
                name=item["name"],
                description=item["description"],
                sku=item["sku"],
                price=item["price"],
                stock_quantity=10,
                is_active=item["is_active"],
            )
        )

    await db.commit()

    return electronics.id, books.id


@pytest.mark.asyncio
async def test_search_products_by_name(test_db, sample_data):
    await insert_sample_products(test_db, sample_data)

    result = await search_products(
        test_db,
        search="Python",
    )

    names = [product.name for product in result["items"]]

    assert "Python Laptop" in names
    assert "Python Keyboard" in names
    assert "Java Book" not in names
    assert result["total"] == 2


@pytest.mark.asyncio
async def test_search_products_by_description(test_db, sample_data):
    await insert_sample_products(test_db, sample_data)

    result = await search_products(
        test_db,
        search="mechanical",
    )

    assert result["total"] == 1
    assert result["items"][0].name == "Python Keyboard"


@pytest.mark.asyncio
async def test_filter_products_by_category(test_db, sample_data):
    electronics_id, _ = await insert_sample_products(
        test_db,
        sample_data,
    )

    result = await search_products(
        test_db,
        category_id=electronics_id,
    )

    assert result["total"] == 2
    assert all(
        product.category_id == electronics_id
        for product in result["items"]
    )


@pytest.mark.asyncio
async def test_filter_products_by_price_range(test_db, sample_data):
    await insert_sample_products(test_db, sample_data)

    result = await search_products(
        test_db,
        min_price=Decimal("1000.00"),
        max_price=Decimal("10000.00"),
    )

    assert result["total"] == 1
    assert result["items"][0].name == "Python Keyboard"


@pytest.mark.asyncio
async def test_exclude_inactive_products(test_db, sample_data):
    await insert_sample_products(test_db, sample_data)

    result = await search_products(test_db)

    names = [product.name for product in result["items"]]

    assert "Old Laptop" not in names
    assert result["total"] == 3


@pytest.mark.asyncio
async def test_sort_products_by_price_ascending(test_db, sample_data):
    await insert_sample_products(test_db, sample_data)

    result = await search_products(
        test_db,
        sort_by="price",
        sort_order="asc",
    )

    prices = [product.price for product in result["items"]]

    assert prices == sorted(prices)


@pytest.mark.asyncio
async def test_sort_products_by_price_descending(test_db, sample_data):
    await insert_sample_products(test_db, sample_data)

    result = await search_products(
        test_db,
        sort_by="price",
        sort_order="desc",
    )

    prices = [product.price for product in result["items"]]

    assert prices == sorted(prices, reverse=True)


@pytest.mark.asyncio
async def test_product_pagination(test_db, sample_data):
    await insert_sample_products(test_db, sample_data)

    result = await search_products(
        test_db,
        page=1,
        limit=2,
    )

    assert len(result["items"]) == 2
    assert result["total"] == 3
    assert result["page"] == 1
    assert result["limit"] == 2
    assert result["pages"] == 2


@pytest.mark.asyncio
async def test_second_product_page(test_db, sample_data):
    await insert_sample_products(test_db, sample_data)

    result = await search_products(
        test_db,
        page=2,
        limit=2,
    )

    assert len(result["items"]) == 1
    assert result["total"] == 3
    assert result["pages"] == 2
