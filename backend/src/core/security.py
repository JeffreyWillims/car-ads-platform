from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.models.user import User

# ==============================================================================
# ⚙️ CONFIGURATION
# ==============================================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"

# Точка входа для Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ==============================================================================
# 🔐 HASHING UTILS
# ==============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Сравнение пароля с хешем."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Генерация хеша пароля."""
    return pwd_context.hash(password)


# ==============================================================================
# 🎟 JWT UTILS
# ==============================================================================

def create_access_token(subject: str | int | Any, expires_delta: timedelta | None = None) -> str:
    """Создание JWT токена."""
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        # Берем настройки из конфига
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "exp": expire,
        "iat": now,
        "sub": str(subject)
    }

    secret = settings.SECRET_KEY.get_secret_value()

    encoded_jwt = jwt.encode(to_encode, secret, algorithm=ALGORITHM)
    return encoded_jwt


# ==============================================================================
# 🛡️ AUTH DEPENDENCY (INJECTION)
# ==============================================================================

async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        session: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """
    Зависимость FastAPI: Валидирует токен и возвращает пользователя из БД.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        secret = settings.SECRET_KEY.get_secret_value()
        # Декодируем токен (автоматическая проверка срока действия exp)
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        user_id_str: str | None = payload.get("sub")

        if user_id_str is None:
            raise credentials_exception

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",  # Фронтенд должен ловить эту ошибку для рефреша
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise credentials_exception

    # Ищем пользователя в БД по ID
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    user = await session.get(User, user_id)

    if user is None:
        raise credentials_exception

    return user
