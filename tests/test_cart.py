
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.core.dependencies import get_current_user


client = TestClient(app)


def test_get_cart_requires_authentication():
    response = client.get("/cart")

    assert response.status_code == 401


def test_customer_can_view_cart():
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

        mock_get_cart.assert_awaited_once()

    finally:
        app.dependency_overrides.clear()


def test_customer_can_add_product_to_cart():
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

    fake_cart = {
        "id": 1,
        "user_id": 3,
        "items": [],
    }

    try:
        with (
            patch(
                "app.routes.cart.add_item_to_cart",
                new_callable=AsyncMock,
            ) as mock_add,
            patch(
                "app.routes.cart.get_cart",
                new_callable=AsyncMock,
                return_value=fake_cart,
            ) as mock_get_cart,
        ):
            response = client.post(
                "/cart/items",
                json={
                    "product_id": 6,
                    "quantity": 2,
                },
            )

        assert response.status_code == 201
        assert response.json() == fake_cart

        mock_add.assert_awaited_once()
        call_kwargs = mock_add.await_args.kwargs

        assert call_kwargs["user_id"] == 3
        assert call_kwargs["product_id"] == 6
        assert call_kwargs["quantity"] == 2

        mock_get_cart.assert_awaited_once()

    finally:
        app.dependency_overrides.clear()

def test_customer_can_update_cart_item_quantity():
    from app.models.cart import CartItem
    from app.models.product import Product

    customer = MagicMock()
    customer.id = 3
    customer.role = "customer"

    fake_cart = MagicMock()
    fake_cart.id = 1

    fake_item = MagicMock()
    fake_item.id = 7
    fake_item.cart_id = 1
    fake_item.product_id = 6
    fake_item.quantity = 1

    fake_product = MagicMock()
    fake_product.id = 6
    fake_product.is_active = True
    fake_product.stock_quantity = 10

    async def override_get_current_user():
        return customer

    async def override_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_current_user] = (
        override_get_current_user
    )
    app.dependency_overrides[get_db] = override_get_db

    try:
        with (
            patch(
                "app.routes.cart.get_cart",
                new_callable=AsyncMock,
                return_value=fake_cart,
            ),
            patch(
                "app.routes.cart.select",
            ) as mock_select,
        ):
            cart_query = MagicMock()
            cart_query.where.return_value = cart_query
            mock_select.return_value = cart_query

            fake_result_item = MagicMock()
            fake_result_item.scalar_one_or_none.return_value = fake_item

            fake_result_product = MagicMock()
            fake_result_product.scalar_one_or_none.return_value = fake_product

            db = AsyncMock()
            db.execute.side_effect = [
                fake_result_item,
                fake_result_product,
            ]

            async def override_get_db_with_mock():
                yield db

            app.dependency_overrides[get_db] = (
                override_get_db_with_mock
            )

            with patch(
                "app.routes.cart.get_cart",
                new_callable=AsyncMock,
                side_effect=[fake_cart, {"id": 1, "user_id": 3, "items": [
                    {"id": 7, "product_id": 6, "quantity": 4}
                ]}],
            ):
                response = client.put(
                    "/cart/items/7",
                    json={"quantity": 4},
                )

        assert response.status_code == 200
        assert fake_item.quantity == 4

    finally:
        app.dependency_overrides.clear()


def test_update_cart_item_rejects_quantity_above_stock():
    customer = MagicMock()
    customer.id = 3
    customer.role = "customer"

    async def override_get_current_user():
        return customer

    fake_cart = MagicMock()
    fake_cart.id = 1

    fake_item = MagicMock()
    fake_item.id = 7
    fake_item.cart_id = 1
    fake_item.product_id = 6

    fake_product = MagicMock()
    fake_product.id = 6
    fake_product.is_active = True
    fake_product.stock_quantity = 2

    async def override_get_db():
        db = AsyncMock()
        db.execute.side_effect = [
            MagicMock(
                scalar_one_or_none=MagicMock(
                    return_value=fake_item
                )
            ),
            MagicMock(
                scalar_one_or_none=MagicMock(
                    return_value=fake_product
                )
            ),
        ]
        yield db

    app.dependency_overrides[get_current_user] = (
        override_get_current_user
    )
    app.dependency_overrides[get_db] = override_get_db

    try:
        with patch(
            "app.routes.cart.get_cart",
            new_callable=AsyncMock,
            return_value=fake_cart,
        ):
            response = client.put(
                "/cart/items/7",
                json={"quantity": 5},
            )

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Requested quantity exceeds available stock"
        )

    finally:
        app.dependency_overrides.clear()

def test_customer_can_remove_cart_item():
    customer = MagicMock()
    customer.id = 3
    customer.role = "customer"

    fake_cart = MagicMock()
    fake_cart.id = 1

    fake_item = MagicMock()
    fake_item.id = 7
    fake_item.cart_id = 1

    async def override_get_current_user():
        return customer

    db = AsyncMock()

    async def override_get_db():
        yield db

    app.dependency_overrides[get_current_user] = (
        override_get_current_user
    )
    app.dependency_overrides[get_db] = override_get_db

    try:
        with (
            patch(
                "app.routes.cart.get_cart",
                new_callable=AsyncMock,
                return_value=fake_cart,
            ),
            patch(
                "app.routes.cart.select",
            ) as mock_select,
        ):
            query = MagicMock()
            query.where.return_value = query
            mock_select.return_value = query

            result = MagicMock()
            result.scalar_one_or_none.return_value = fake_item
            db.execute.return_value = result

            response = client.delete("/cart/items/7")

        assert response.status_code == 204
        db.delete.assert_awaited_once_with(fake_item)
        db.commit.assert_awaited_once()

    finally:
        app.dependency_overrides.clear()


def test_customer_cannot_remove_item_not_in_cart():
    customer = MagicMock()
    customer.id = 3
    customer.role = "customer"

    fake_cart = MagicMock()
    fake_cart.id = 1

    async def override_get_current_user():
        return customer

    db = AsyncMock()

    async def override_get_db():
        yield db

    app.dependency_overrides[get_current_user] = (
        override_get_current_user
    )
    app.dependency_overrides[get_db] = override_get_db

    try:
        with (
            patch(
                "app.routes.cart.get_cart",
                new_callable=AsyncMock,
                return_value=fake_cart,
            ),
            patch(
                "app.routes.cart.select",
            ) as mock_select,
        ):
            query = MagicMock()
            query.where.return_value = query
            mock_select.return_value = query

            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            db.execute.return_value = result

            response = client.delete("/cart/items/999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Cart item not found"
        db.delete.assert_not_awaited()
        db.commit.assert_not_awaited()

    finally:
        app.dependency_overrides.clear()
