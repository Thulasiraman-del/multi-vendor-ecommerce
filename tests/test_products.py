
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.core.dependencies import get_current_user


client = TestClient(app)


# --------------------------------------------------
# TEST HELPERS
# --------------------------------------------------

def setup_user(role="customer"):
    user = MagicMock()
    user.id = 3
    user.role = role
    return user


def setup_overrides(user=None, db=None):
    user = user if user is not None else setup_user()
    db = db if db is not None else AsyncMock()

    async def override_current_user():
        return user

    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = (
        override_current_user
    )

    app.dependency_overrides[get_db] = override_db


def teardown_overrides():
    app.dependency_overrides.clear()


def setup_product_search_db(total=0, products=None):
    """Create database mocks for the product search service."""

    count_result = MagicMock()
    count_result.scalar_one.return_value = total

    products_result = MagicMock()
    products_result.scalars.return_value.all.return_value = (
        products if products is not None else []
    )

    db = AsyncMock()
    db.execute.side_effect = [
        count_result,
        products_result,
    ]

    return db


# --------------------------------------------------
# GET PRODUCTS - PUBLIC ACCESS AND PAGINATION
# --------------------------------------------------

def test_get_products_is_public():
    db = setup_product_search_db()

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    try:
        response = client.get("/products")

        assert response.status_code == 200

        assert response.json() == {
            "items": [],
            "total": 0,
            "page": 1,
            "limit": 20,
            "pages": 0,
        }

        assert db.execute.await_count == 2

    finally:
        teardown_overrides()


# --------------------------------------------------
# CUSTOMER AUTHORIZATION
# --------------------------------------------------

def test_customer_cannot_create_product():
    customer = setup_user("customer")
    db = AsyncMock()

    setup_overrides(customer, db)

    try:
        response = client.post(
            "/products",
            json={
                "category_id": 1,
                "name": "Keyboard",
                "description": "USB keyboard",
                "sku": "KEYBOARD-001",
                "price": "799.00",
                "stock_quantity": 10,
            },
        )

        assert response.status_code == 403

        assert response.json()["detail"] == (
            "Only vendor accounts can manage products"
        )

        db.execute.assert_not_awaited()

    finally:
        teardown_overrides()


# --------------------------------------------------
# AUTHENTICATION
# --------------------------------------------------

def test_create_product_requires_authentication():
    response = client.post(
        "/products",
        json={
            "category_id": 1,
            "name": "Keyboard",
            "description": "USB keyboard",
            "sku": "KEYBOARD-001",
            "price": "799.00",
            "stock_quantity": 10,
        },
    )

    assert response.status_code == 401


# --------------------------------------------------
# PRODUCT VALIDATION
# --------------------------------------------------

def test_create_product_rejects_invalid_price():
    setup_overrides(setup_user("vendor"))

    try:
        response = client.post(
            "/products",
            json={
                "category_id": 1,
                "name": "Keyboard",
                "description": "USB keyboard",
                "sku": "KEYBOARD-001",
                "price": "0",
                "stock_quantity": 10,
            },
        )

        assert response.status_code == 422

    finally:
        teardown_overrides()


# --------------------------------------------------
# GET PRODUCT
# --------------------------------------------------

def test_get_missing_product_returns_404():
    result = MagicMock()
    result.scalar_one_or_none.return_value = None

    db = AsyncMock()
    db.execute.return_value = result

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    try:
        response = client.get("/products/999999")

        assert response.status_code == 404

        assert response.json()["detail"] == (
            "Product not found"
        )

    finally:
        teardown_overrides()


# --------------------------------------------------
# VENDOR AUTHORIZATION - UPDATE
# --------------------------------------------------

def test_vendor_cannot_update_another_vendors_product():
    vendor_user = setup_user("vendor")
    db = AsyncMock()

    own_vendor = MagicMock()
    own_vendor.id = 10
    own_vendor.user_id = vendor_user.id
    own_vendor.is_active = True

    another_vendors_product = MagicMock()
    another_vendors_product.id = 5
    another_vendors_product.vendor_id = 20

    vendor_result = MagicMock()
    vendor_result.scalar_one_or_none.return_value = own_vendor

    product_result = MagicMock()
    product_result.scalar_one_or_none.return_value = (
        another_vendors_product
    )

    db.execute.side_effect = [
        vendor_result,
        product_result,
    ]

    setup_overrides(vendor_user, db)

    try:
        response = client.put(
            "/products/5",
            json={
                "name": "Updated Keyboard"
            },
        )

        assert response.status_code == 403

        assert response.json()["detail"] == (
            "You can only update your own products"
        )

        db.commit.assert_not_awaited()

    finally:
        teardown_overrides()


# --------------------------------------------------
# VENDOR AUTHORIZATION - DELETE
# --------------------------------------------------

def test_vendor_cannot_delete_another_vendors_product():
    vendor_user = setup_user("vendor")
    db = AsyncMock()

    own_vendor = MagicMock()
    own_vendor.id = 10
    own_vendor.user_id = vendor_user.id
    own_vendor.is_active = True

    another_vendors_product = MagicMock()
    another_vendors_product.id = 5
    another_vendors_product.vendor_id = 20
    another_vendors_product.is_active = True

    vendor_result = MagicMock()
    vendor_result.scalar_one_or_none.return_value = own_vendor

    product_result = MagicMock()
    product_result.scalar_one_or_none.return_value = (
        another_vendors_product
    )

    db.execute.side_effect = [
        vendor_result,
        product_result,
    ]

    setup_overrides(vendor_user, db)

    try:
        response = client.delete("/products/5")

        assert response.status_code == 403

        assert response.json()["detail"] == (
            "You can only delete your own products"
        )

        assert another_vendors_product.is_active is True

        db.commit.assert_not_awaited()

    finally:
        teardown_overrides()


# --------------------------------------------------
# VENDOR PROFILE VALIDATION
# --------------------------------------------------

def test_vendor_without_profile_cannot_create_product():
    vendor_user = setup_user("vendor")
    db = AsyncMock()

    result = MagicMock()
    result.scalar_one_or_none.return_value = None

    db.execute.return_value = result

    setup_overrides(vendor_user, db)

    try:
        response = client.post(
            "/products",
            json={
                "category_id": 1,
                "name": "Keyboard",
                "description": "USB keyboard",
                "sku": "KEYBOARD-001",
                "price": "799.00",
                "stock_quantity": 10,
            },
        )

        assert response.status_code == 403

        assert response.json()["detail"] == (
            "Vendor profile not found"
        )

        db.commit.assert_not_awaited()

    finally:
        teardown_overrides()


# --------------------------------------------------
# PRODUCT PAGINATION
# --------------------------------------------------

def test_products_support_custom_pagination():
    db = setup_product_search_db(total=25)

    setup_overrides(db=db)

    try:
        response = client.get(
            "/products?page=2&limit=10"
        )

        assert response.status_code == 200

        assert response.json() == {
            "items": [],
            "total": 25,
            "page": 2,
            "limit": 10,
            "pages": 3,
        }

        assert db.execute.await_count == 2

    finally:
        teardown_overrides()


# --------------------------------------------------
# PAGINATION VALIDATION
# --------------------------------------------------

def test_products_reject_invalid_page():
    response = client.get(
        "/products?page=0"
    )

    assert response.status_code == 422


def test_products_reject_invalid_limit():
    response = client.get(
        "/products?limit=101"
    )

    assert response.status_code == 422


# --------------------------------------------------
# PRICE FILTER VALIDATION
# --------------------------------------------------

def test_products_reject_min_price_greater_than_max_price():
    response = client.get(
        "/products?min_price=1000&max_price=500"
    )

    assert response.status_code == 422


# --------------------------------------------------
# SEARCH, FILTER AND SORT PARAMETERS
# --------------------------------------------------

def test_products_accept_search_and_sort_parameters():
    db = setup_product_search_db()

    setup_overrides(db=db)

    try:
        response = client.get(
            "/products"
            "?search=keyboard"
            "&category_id=1"
            "&min_price=100"
            "&max_price=1000"
            "&sort_by=price"
            "&sort_order=desc"
            "&page=1"
            "&limit=10"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["page"] == 1
        assert data["limit"] == 10
        assert data["items"] == []

        assert db.execute.await_count == 2

    finally:
        teardown_overrides()
