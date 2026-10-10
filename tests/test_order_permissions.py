
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.core.dependencies import get_current_user


client = TestClient(app)


def test_customer_cannot_view_another_users_order():
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
        with patch(
            "app.routes.orders.get_order_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ) as mock_get_order:
            response = client.get("/orders/999999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Order not found"

        mock_get_order.assert_awaited_once_with(
            mock_get_order.call_args.args[0],
            3,
            999999,
        )
    finally:
        app.dependency_overrides.clear()

def test_customer_cannot_update_fulfillment_status():
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
        response = client.patch(
            "/orders/8/items/7/status",
            json={"status": "shipped"},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Only vendors can update fulfillment"
        )
    finally:
        app.dependency_overrides.clear()
