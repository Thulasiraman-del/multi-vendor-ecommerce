from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.core.dependencies import get_current_user


client = TestClient(app)


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

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = override_db

    return db


def teardown_overrides():
    app.dependency_overrides.clear()


def test_create_category_requires_authentication():
    response = client.post(
        "/categories",
        json={
            "name": "Test Electronics",
            "description": "Test category",
        },
    )

    assert response.status_code == 401


def test_customer_cannot_create_category():
    setup_overrides(setup_user("customer"))

    try:
        response = client.post(
            "/categories",
            json={
                "name": "Customer Category",
                "description": "Should not be created",
            },
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Insufficient permissions"

    finally:
        teardown_overrides()


def test_admin_can_create_category():
    db = AsyncMock()
    setup_overrides(setup_user("admin"), db)

    created_category = SimpleNamespace(
        id=10,
        name="Admin Electronics",
        description="Created by admin",
        is_active=True,
    )

    try:
        with patch(
            "app.routes.categories.get_category_by_name",
            new_callable=AsyncMock,
            return_value=None,
        ) as mock_get_category, patch(
            "app.routes.categories.create_category",
            new_callable=AsyncMock,
            return_value=created_category,
        ) as mock_create_category:

            response = client.post(
                "/categories",
                json={
                    "name": "Admin Electronics",
                    "description": "Created by admin",
                },
            )

        assert response.status_code == 201
        assert response.json()["id"] == 10
        assert response.json()["name"] == "Admin Electronics"
        assert response.json()["is_active"] is True

        mock_get_category.assert_awaited_once()
        mock_create_category.assert_awaited_once()

    finally:
        teardown_overrides()


def test_get_categories_remains_public():
    result = MagicMock()
    result.scalars.return_value.all.return_value = []

    db = AsyncMock()
    db.execute.return_value = result

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    try:
        response = client.get("/categories")

        assert response.status_code == 200
        assert response.json() == []

    finally:
        teardown_overrides()