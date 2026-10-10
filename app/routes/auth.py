from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import create_access_token
from app.schemas.user import UserCreate,UserResponse
from fastapi.security import OAuth2PasswordRequestForm
from app.services.auth_service import(
    authenticate_user,
    get_user_by_email,
    create_user
)
from app.schemas.user import(UserCreate,UserResponse,UserLogin,TokenResponse)
router=APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)
@router.post("/register",response_model=UserResponse,status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data:UserCreate,
    db:AsyncSession=Depends(get_db)
):
    existing_user=await get_user_by_email(db,user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    new_user=await create_user(db,user_data)
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

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }