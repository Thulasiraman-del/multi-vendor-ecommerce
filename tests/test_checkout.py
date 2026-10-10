
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.core.dependencies import get_current_user


client = TestClient(app)


def setup_overrides(role="customer"):
    user = MagicMock()
    user.id = 3
    user.role = role

    db = AsyncMock()

    async def override_get_current_user():
        return user

    async def override_get_db():
        yield db

    app.dependency_overrides[get_current_user] = (
        override_get_current_user
    )
    app.dependency_overrides[get_db] = override_get_db

    return user, db


def teardown_overrides():
    app.dependency_overrides.clear()


def test_checkout_requires_authentication():
    response = client.post("/orders/checkout")

    assert response.status_code == 401


def test_vendor_cannot_checkout():
    setup_overrides(role="vendor")

    try:
        response = client.post("/orders/checkout")

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Only customers can checkout"
        )
    finally:
        teardown_overrides()



def test_checkout_rejects_empty_cart():
    _, db = setup_overrides(role="customer")

    from fastapi import HTTPException

    try:
        with patch(
            "app.routes.orders.create_order_from_cart",
            new_callable=AsyncMock,
            side_effect=HTTPException(
                status_code=400,
                detail="Your cart is empty",
            ),
        ) as mock_create_order:
            response = client.post("/orders/checkout")

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Your cart is empty"
        )

        mock_create_order.assert_awaited_once_with(db, 3)
    finally:
        teardown_overrides()
