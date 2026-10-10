
from certifi import where
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.user import UserCreate,UserResponse
from app.core.security import hash_password,verify_password,create_access_token

async def get_user_by_email(
        db:AsyncSession,
        email:str
):
    result=await db.execute(
        select(User).
        where(User.email==email)
        )
    return result.scalar_one_or_none()
async def create_user(
        db:AsyncSession,
        user_data=UserCreate
):
    hashed_password=hash_password(user_data.password)
    new_user=User(
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
        db:AsyncSession,
        email:str,
        password:str
):
    user=await get_user_by_email(db,email)
    if not user:
        return None
    if not verify_password(password,user.password_hash):
        return None
    return user