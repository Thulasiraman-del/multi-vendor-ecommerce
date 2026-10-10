from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.user import UserResponse
from app.models.user import User
router=APIRouter(
    prefix="/users",
    tags=["Users"]
)
@router.get("/me",response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user
