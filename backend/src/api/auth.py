from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import create_access_token, verify_password, get_password_hash, get_current_user
from src.models.user import User
from src.schemas.auth import Token, UserCreate

# Настраиваем роутер (Теги нужны для красоты в Swagger)
router = APIRouter(prefix="/auth", tags=["Authentication"])


# ==========================================
# 1. РЕГИСТРАЦИЯ
# ==========================================
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
        user_in: UserCreate,
        session: Annotated[AsyncSession, Depends(get_db)]
):
    """Регистрация нового пользователя."""
    # Проверяем, нет ли уже такого email
    query = select(User).where(User.email == user_in.email)
    result = await session.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )

    # Создаем пользователя, предварительно захешировав пароль
    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password)
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return {"message": "Пользователь успешно создан", "user_id": new_user.id}

# ==========================================
# 2. ЛОГИН
# ==========================================

@router.post(
    "/login",
    response_model=Token,
    summary="Авторизация пользователя (Получение JWT)",
)
async def login_for_access_token(
        # form_data автоматически парсит Body как Form-Data (не JSON!)
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        # Инжектим сессию БД
        session: Annotated[AsyncSession, Depends(get_db)]
) -> Token:
    """
    OAuth2 compatible token login.
    Обратите внимание: email передается в поле **username**.
    """
    # 1. Запрашиваем пользователя из БД
    query = select(User).where(User.email == form_data.username)
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    # 2. ПРОДВИНУТАЯ БЕЗОПАСНОСТЬ: Митигация Timing Attack
    # Мы всегда должны вычислять хеш пароля, даже если юзер не найден.
    # Иначе хакер сможет по времени ответа (быстро = нет юзера, медленно = есть юзер)
    # собрать базу существующих email'ов.
    if not user:
        # Считаем "пустой" хеш, чтобы потратить те же 200мс процессорного времени
        verify_password(form_data.password, "$2b$12$DummyHashToPreventTimingAttacks")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",  # Никогда не говорим "Пользователь не найден"!
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Проверяем реальный пароль
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Генерируем токен (Используем неизменяемый ID!)
    access_token = create_access_token(subject=user.id)

    return Token(access_token=access_token, token_type="bearer")

# ==========================================
# 3. ЗАЩИЩЕННЫЙ МАРШРУТ (Тестируем get_current_user)
# ==========================================
@router.get("/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Получение данных о себе.
    Этот эндпоинт НЕ сработает без валидного JWT токена!
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "message": "Ты успешно прошел аутентификацию и система узнала тебя по токену!"
    }