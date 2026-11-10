
import hashlib

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password


def hash_refresh_token(token: str) -> str:
    """Create a SHA-256 hash of a refresh token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def get_user_by_email(
    db: AsyncSession,
    email: str
):
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    user_data: UserCreate
):
    hashed_password = hash_password(user_data.password)

    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        password_hash=hashed_password,
        phone=user_data.phone
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str
):
    user = await get_user_by_email(db, email)

    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


async def store_refresh_token(
    db: AsyncSession,
    user_id: int,
    token: str,
    expires_at
):
    token_hash = hash_refresh_token(token)

    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        is_revoked=False
    )

    db.add(refresh_token)
    await db.commit()
    await db.refresh(refresh_token)

    return refresh_token


async def get_valid_refresh_token(
    db: AsyncSession,
    token: str
):
    token_hash = hash_refresh_token(token)

    current_time = datetime.now(timezone.utc)

    result = await db.execute(
        select(RefreshToken)
        .where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked.is_(False),
            RefreshToken.expires_at > current_time
        )
        .with_for_update()
    )

    return result.scalar_one_or_none()


async def rotate_refresh_token(
    db: AsyncSession,
    old_token: RefreshToken,
    user_id: int,
    new_token: str,
    expires_at
):
    old_token.is_revoked = True

    new_refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=hash_refresh_token(new_token),
        expires_at=expires_at,
        is_revoked=False
    )

    db.add(new_refresh_token)

    await db.commit()

    return new_refresh_token


async def revoke_refresh_token(
    db: AsyncSession,
    refresh_token: RefreshToken
):
    refresh_token.is_revoked = True

    await db.commit()