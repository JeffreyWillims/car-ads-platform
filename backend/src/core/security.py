# backend/src/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.models.user import User
from src.schemas.auth import TokenPayload

# ==========================================
# ⚙️ Настройки криптографии и Swagger
# ==========================================

# Контекст хеширования (bcrypt - устойчив к GPU-брутфорсу)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Симметричный алгоритм подписи
ALGORITHM = "HS256"

# Указываем FastAPI, откуда брать токен (URL должен совпадать с роутом логина)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ==========================================
# 🔐 Блок 1: Хеширование паролей
# ==========================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Сравнение сырого пароля с хэшем из БД.
    Time Complexity: CPU-bound операция (~100-300ms).
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Генерация bcrypt-хэша с уникальной встроенной 'солью' (salt).
    """
    return pwd_context.hash(password)


# ==========================================
# 🎟 Блок 2: Генерация JWT
# ==========================================

def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """
    Генерация JWT (JSON Web Token).
    Time Complexity: O(1) Time / O(1) Space.
    """
    # Используем строго timezone.utc для защиты от расхождения часовых поясов серверов
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        # Берем дефолтное время жизни из конфига (по умолчанию 30 или 60 минут)
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # JWT Claims (Стандарт RFC 7519)
    to_encode = {
        "exp": expire,  # Время смерти токена
        "sub": str(subject),  # Уникальный ID сущности (user_id)
        "iat": now  # Время выдачи
    }

    # Безопасное извлечение ключа из Pydantic SecretStr
    secret = settings.SECRET_KEY.get_secret_value()

    # Кодируем словарь в Base64 и подписываем криптографическим секретом
    encoded_jwt = jwt.encode(to_encode, secret, algorithm=ALGORITHM)
    return encoded_jwt


# ==========================================
# 🛡️ Блок 3: Инъекция зависимостей (Auth Dependency)
# ==========================================

async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        session: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """
    FastAPI Dependency: Перехватывает JWT из заголовка 'Authorization: Bearer <token>',
    валидирует его и возвращает объект пользователя из базы данных.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 1. Декодируем токен (PyJWT сам выбросит ошибку, если срок годности 'exp' истек)
        secret = settings.SECRET_KEY.get_secret_value()
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])

        # 2. Строгая валидация структуры токена через Pydantic DTO
        token_data = TokenPayload(**payload)

        if token_data.sub is None:
            raise credentials_exception

    except (jwt.InvalidTokenError, ValidationError):
        # Ловим поддельные, просроченные токены и сломанный payload
        raise credentials_exception

    # 3. Идем в БД за пользователем.
    # Приводим 'sub' к числу, так как в JWT он хранится как строка, а ID в БД - Integer.
    try:
        user_id = int(token_data.sub)
    except ValueError:
        raise credentials_exception

    # SQLAlchemy 2.0 Async Select
    user = await session.scalar(select(User).where(User.id == user_id))

    if not user:
        raise credentials_exception

    return user