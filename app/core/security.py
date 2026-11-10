
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import jwt, JWTError
from pwdlib import PasswordHash

from app.core.config import settings


password_hasher = PasswordHash.recommended()

REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hasher.verify(password, hashed_password)


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None
) -> str:
    to_encode = data.copy()

    if expires_delta is None:
        expires_delta = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    expire = datetime.now(timezone.utc) + expires_delta

    to_encode.update({
        "exp": expire,
        "type": "access"
    })

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()

    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": str(uuid4()),
        "type": "refresh"
    })

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        if payload.get("type") != "access":
            return None
        if not payload.get("sub"):
            return None

        return payload

    except JWTError:
        return None


def decode_refresh_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        if payload.get("type") != "refresh":
            return None

        if not payload.get("jti"):
            return None

        if not payload.get("sub"):
            return None

        return payload

    except JWTError:
        return None
