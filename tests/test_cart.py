
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.core.dependencies import get_current_user


client = TestClient(app)


def setup_customer():
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

    return customer


def clear_overrides():
    app.dependency_overrides.clear()


def test_get_cart_requires_authentication():
    response = client.get("/cart")

    assert response.status_code == 401


def test_customer_can_view_cart():
    setup_customer()

    fake_cart = {
        "id": 1,
        "user_id": 3,
        "items": [],
    }

    try:
        with patch(
            "app.routes.cart.get_cart",
            new_callable=AsyncMock,
            return_value=fake_cart,
        ) as mock_get_cart:
            response = client.get("/cart")

        assert response.status_code == 200
        assert response.json() == fake_cart

        mock_get_cart.assert_awaited_once_with(
            db=mock_get_cart.await_args.kwargs["db"],
            user_id=3,
        )

    finally:
        clear_overrides()


def test_customer_can_add_product_to_cart():
    setup_customer()

    fake_cart = {
        "id": 1,
        "user_id": 3,
        "items": [],
    }

    try:
        with patch(
            "app.routes.cart.add_item_to_cart",
            new_callable=AsyncMock,
            return_value=fake_cart,
        ) as mock_add:
            response = client.post(
                "/cart/items",
                json={
                    "product_id": 6,
                    "quantity": 2,
                },
            )

        assert response.status_code == 201
        assert response.json() == fake_cart

        call_kwargs = mock_add.await_args.kwargs

        assert call_kwargs["user_id"] == 3
        assert call_kwargs["product_id"] == 6
        assert call_kwargs["quantity"] == 2

    finally:
        clear_overrides()


def test_customer_can_update_cart_item_quantity():
    setup_customer()

    fake_cart = {
        "id": 1,
        "user_id": 3,
        "items": [
            {
                "id": 7,
                "product_id": 6,
                "quantity": 4,
            }
        ],
    }

    try:
        with patch(
            "app.routes.cart.update_cart_item",
            new_callable=AsyncMock,
            return_value=fake_cart,
        ) as mock_update:
            response = client.put(
                "/cart/items/7",
                json={"quantity": 4},
            )

        assert response.status_code == 200
        assert response.json() == fake_cart

        call_kwargs = mock_update.await_args.kwargs

        assert call_kwargs["user_id"] == 3
        assert call_kwargs["item_id"] == 7
        assert call_kwargs["quantity"] == 4

    finally:
        clear_overrides()


def test_update_cart_item_rejects_quantity_above_stock():
    setup_customer()

    try:
        with patch(
            "app.routes.cart.update_cart_item",
            new_callable=AsyncMock,
            side_effect=HTTPException(
                status_code=400,
                detail="Requested quantity exceeds available stock",
            ),
        ) as mock_update:
            response = client.put(
                "/cart/items/7",
                json={"quantity": 5},
            )

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Requested quantity exceeds available stock"
        )

        mock_update.assert_awaited_once()

    finally:
        clear_overrides()


def test_customer_can_remove_cart_item():
    setup_customer()

    try:
        with patch(
            "app.routes.cart.remove_item_from_cart",
            new_callable=AsyncMock,
        ) as mock_remove:
            response = client.delete("/cart/items/7")

        assert response.status_code == 204

        call_kwargs = mock_remove.await_args.kwargs

        assert call_kwargs["user_id"] == 3
        assert call_kwargs["item_id"] == 7

    finally:
        clear_overrides()


def test_customer_cannot_remove_item_not_in_cart():
    setup_customer()

    try:
        with patch(
            "app.routes.cart.remove_item_from_cart",
            new_callable=AsyncMock,
            side_effect=HTTPException(
                status_code=404,
                detail="Cart item not found",
            ),
        ) as mock_remove:
            response = client.delete("/cart/items/999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Cart item not found"

        mock_remove.assert_awaited_once()

    finally:
        clear_overrides()
