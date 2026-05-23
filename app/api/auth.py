from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import LoginResponse, UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/signup", response_model=UserResponse)
async def signup(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
    is_admin = user_data.admin_code == "SUPER_SECRET_123"
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=AuthService.get_password_hash(user_data.password),
        tfa_enabled=False,
        is_admin=is_admin,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not AuthService.verify_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    if user.tfa_enabled:
        return LoginResponse(
            access_token="",
            refresh_token="",
            requires_2fa=True,
            temp_token=AuthService.create_temp_2fa_token(user.id),
        )
    return LoginResponse(
        access_token=AuthService.create_access_token(data={"sub": str(user.id)}),
        refresh_token=AuthService.create_refresh_token(data={"sub": str(user.id)}),
        requires_2fa=False,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
