
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token
)

from app.models.user import User

from app.schemas.user import (
    UserCreate,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest
)

from app.services.auth_service import (
    authenticate_user,
    get_user_by_email,
    create_user,
    store_refresh_token,
    get_valid_refresh_token,
    rotate_refresh_token,
    revoke_refresh_token
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    existing_user = await get_user_by_email(
        db,
        user_data.email
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    new_user = await create_user(db, user_data)

    return new_user


@router.post(
    "/login",
    response_model=TokenResponse
)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(
        db,
        form_data.username,
        form_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    token_data = {
        "sub": str(user.id),
        "role": user.role
    }

    access_token = create_access_token(
        data=token_data
    )

    refresh_token = create_refresh_token(
        data=token_data
    )

    payload = decode_refresh_token(refresh_token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate refresh token"
        )

    expires_at = datetime.fromtimestamp(
        payload["exp"],
        tz=timezone.utc
    )

    await store_refresh_token(
        db=db,
        user_id=user.id,
        token=refresh_token,
        expires_at=expires_at
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post(
    "/refresh",
    response_model=TokenResponse
)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    # Step 1: Validate the refresh JWT
    payload = decode_refresh_token(request.refresh_token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # Step 2: Extract the user ID
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Step 3: Check the token against the database
    old_token = await get_valid_refresh_token(
        db,
        request.refresh_token
    )

    if not old_token or old_token.user_id != user_id:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked or expired"
        )

    # Step 4: Fetch the current user
    result = await db.execute(
        select(User).where(User.id == user_id)
    )

    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found or inactive"
        )

    # Step 5: Generate new tokens using the current user role
    token_data = {
        "sub": str(user.id),
        "role": user.role
    }

    new_access_token = create_access_token(
        data=token_data
    )

    new_refresh_token = create_refresh_token(
        data=token_data
    )

    new_payload = decode_refresh_token(new_refresh_token)

    if not new_payload:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate refresh token"
        )

    new_expires_at = datetime.fromtimestamp(
        new_payload["exp"],
        tz=timezone.utc
    )

    # Step 6: Revoke the old token and save the new one
    try:
        await rotate_refresh_token(
            db=db,
            old_token=old_token,
            user_id=user.id,
            new_token=new_refresh_token,
            expires_at=new_expires_at
        )
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not rotate refresh token"
        )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT
)
async def logout_user(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    # Validate the refresh JWT
    payload = decode_refresh_token(request.refresh_token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # Find the active database session
    refresh_token = await get_valid_refresh_token(
        db,
        request.refresh_token
    )

    # Revoke it if it is still active
    if refresh_token:
        await revoke_refresh_token(
            db,
            refresh_token
        )
    else:
        await db.rollback()

    return Response(status_code=status.HTTP_204_NO_CONTENT)