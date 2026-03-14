from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
    get_current_user
)
from src.models.user import User
from src.schemas.auth import Token, UserCreate


router = APIRouter(prefix="/auth", tags=["Authentication"])

# ==============================================================================
# 1. REGISTER
# ==============================================================================
@router.post("/register", status_code=status.HTTP_201_CREATED, summary="Регистрация пользователя")
async def register_user(
        user_in: UserCreate,
        session: Annotated[AsyncSession, Depends(get_db)]
):
    # Проверка уникальности Email
    query = select(User).where(User.email == user_in.email)
    result = await session.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # Создание пользователя
    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password)
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return {"message": "User created successfully", "user_id": new_user.id}


# ==============================================================================
# 2. LOGIN (OAuth2)
# ==============================================================================
@router.post("/login", response_model=Token, summary="Получение JWT токена")
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        session: Annotated[AsyncSession, Depends(get_db)]
) -> Token:
    """
    Принимает username (email) и password в Form Data.
    Возвращает access_token.
    """
    # Поиск пользователя
    query = select(User).where(User.email == form_data.username)
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    # Валидация пароля (защита от Timing Attack)
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Если юзера нет, делаем фейковую проверку, чтобы время ответа было одинаковым
        if not user:
            verify_password("fake", "$2b$12$DummyHashToPreventTimingAttacks")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Генерация токена (subject = user.id)
    access_token = create_access_token(subject=user.id)

    return Token(access_token=access_token, token_type="bearer")


# ==============================================================================
# 3. PROFILE (Protected Route)
# ==============================================================================
@router.get("/me", summary="Профиль текущего пользователя")
async def read_users_me(
        current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Требует Header: Authorization: Bearer <token>
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_active": True,
        "role": "user"
    }
