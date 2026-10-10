
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.services.vendor_order_service import get_vendor_order_items


client = TestClient(app)


def test_vendor_orders_requires_authentication():
    response = client.get("/vendors/me/orders")

    assert response.status_code == 401


def test_customer_cannot_access_vendor_orders():
    customer = MagicMock()
    customer.id = 3
    customer.role = "customer"

    async def override_get_current_user():
        return customer

    async def override_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_current_user] = (
        override_get_current_user
    )
    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.get("/vendors/me/orders")
        assert response.status_code == 403
        assert response.json()["detail"] == "Vendor account required"
    finally:
        app.dependency_overrides.clear()

def test_vendor_can_access_vendor_orders():
    vendor = MagicMock()
    vendor.id = 2
    vendor.role = "vendor"

    async def override_get_current_user():
        return vendor

    async def override_get_db():
        yield AsyncMock()

    mock_get_orders = AsyncMock(return_value=[])

    app.dependency_overrides[get_current_user] = (
        override_get_current_user
    )
    app.dependency_overrides[get_db] = override_get_db

    # Patch the service used by the vendor route.
    from unittest.mock import patch

    try:
        with patch(
            "app.routes.vendors.get_vendor_order_items",
            mock_get_orders,
        ):
            response = client.get("/vendors/me/orders")

        assert response.status_code == 200
        assert response.json() == []
        mock_get_orders.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()
