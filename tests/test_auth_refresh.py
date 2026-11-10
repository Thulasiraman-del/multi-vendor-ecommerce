from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db


client = TestClient(app)


def test_refresh_token_success():
    # 1. Mock an active user
    user = MagicMock()
    user.id = 1
    user.role = "customer"
    user.is_active = True

    # 2. Mock the database session
    mock_db = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_db.execute.return_value = mock_result

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    # 3. Prepare mock refresh-token data
    old_token = MagicMock()
    old_token.user_id = 1

    new_expiry = datetime.now(timezone.utc) + timedelta(days=7)

    # 4. Mock token decoding twice
    decoded_tokens = [
        {"sub": "1", "type": "refresh"},
        {
            "sub": "1",
            "type": "refresh",
            "exp": new_expiry.timestamp()
        }
    ]

    try:
        with patch(
            "app.routes.auth.decode_refresh_token",
            side_effect=decoded_tokens
        ), patch(
            "app.routes.auth.get_valid_refresh_token",
            new_callable=AsyncMock,
            return_value=old_token
        ), patch(
            "app.routes.auth.create_access_token",
            return_value="new-access-token"
        ), patch(
            "app.routes.auth.create_refresh_token",
            return_value="new-refresh-token"
        ), patch(
            "app.routes.auth.rotate_refresh_token",
            new_callable=AsyncMock
        ):

            response = client.post(
                "/auth/refresh",
                json={"refresh_token": "old-refresh-token"}
            )

        assert response.status_code == 200

        data = response.json()

        assert data["access_token"] == "new-access-token"
        assert data["refresh_token"] == "new-refresh-token"
        assert data["token_type"] == "bearer"

    finally:
        app.dependency_overrides.clear()
def test_refresh_token_reuse_rejected():
    mock_db = AsyncMock()

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with patch(
            "app.routes.auth.decode_refresh_token",
            return_value={"sub": "1", "type": "refresh"}
        ), patch(
            "app.routes.auth.get_valid_refresh_token",
            new_callable=AsyncMock,
            return_value=None
        ):

            response = client.post(
                "/auth/refresh",
                json={"refresh_token": "old-revoked-token"}
            )

        assert response.status_code == 401

        assert response.json()["detail"] == (
            "Refresh token revoked or expired"
        )

        mock_db.rollback.assert_awaited_once()

    finally:
        app.dependency_overrides.clear()
def test_invalid_refresh_token_rejected():
    mock_db = AsyncMock()

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with patch(
            "app.routes.auth.decode_refresh_token",
            return_value=None
        ), patch(
            "app.routes.auth.get_valid_refresh_token",
            new_callable=AsyncMock
        ) as mock_get_token:

            response = client.post(
                "/auth/refresh",
                json={"refresh_token": "invalid-token"}
            )

        assert response.status_code == 401

        assert response.json()["detail"] == (
            "Invalid or expired refresh token"
        )

        mock_get_token.assert_not_awaited()

    finally:
        app.dependency_overrides.clear()
def test_logout_revokes_refresh_token():
    mock_db = AsyncMock()

    refresh_token = MagicMock()

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with patch(
            "app.routes.auth.decode_refresh_token",
            return_value={"sub": "1", "type": "refresh"}
        ), patch(
            "app.routes.auth.get_valid_refresh_token",
            new_callable=AsyncMock,
            return_value=refresh_token
        ), patch(
            "app.routes.auth.revoke_refresh_token",
            new_callable=AsyncMock
        ) as mock_revoke:

            response = client.post(
                "/auth/logout",
                json={"refresh_token": "valid-refresh-token"}
            )

        assert response.status_code == 204

        mock_revoke.assert_awaited_once_with(
            mock_db,
            refresh_token
        )

    finally:
        app.dependency_overrides.clear()