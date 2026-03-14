import sys
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from src.core.config import settings

# ==============================================================================
# ⚙️ ПОЛИТИКА УПРАВЛЕНИЯ СОЕДИНЕНИЯМИ
# ==============================================================================

# Проверяем, запущен ли этот код внутри процесса Celery
IS_CELERY = "celery" in sys.argv[0]

# Если это Celery (фоновые воркеры-форки) -> отключаем пулинг (NullPool),
# чтобы избежать SSL/Socket конфликтов между процессами.
# Если это FastAPI (веб-сервер) -> оставляем стандартный пулинг (QueuePool = None)
pool_class = NullPool if IS_CELERY else None

# Создаем движок
engine = create_async_engine(
    settings.database_url,
    echo=False,
    poolclass=pool_class,
    # pool_pre_ping защищает FastAPI от "протухших" соединений.
    # В NullPool (для Celery) SQLAlchemy просто игнорирует этот флаг.
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

class Base(DeclarativeBase):
    """Registry for all SQLAlchemy models."""
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для получения сессии БД в FastAPI."""
    async with AsyncSessionLocal() as session:
        yield session