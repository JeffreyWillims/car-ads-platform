# python 3.12+
import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config, AsyncEngine

from src.models.user import User
from src.models.car import Car

# ==============================================================================
# 1. SYS PATH RESOLUTION (Bulletproof Import Fixing)
# ==============================================================================
# Гарантируем, что Alembic видит папку 'src', независимо от того,
# откуда запущена команда (из корня, из докера или из вложенной папки).
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Импортируем настройки и реестр метаданных
from src.core.config import settings
from src.core.database import Base  
# ВАЖНО: В src/models/__init__.py должны быть импортированы ВСЕ модели,
# иначе Alembic решит, что таблиц нет, и сгенерирует DROP TABLE.

# ==============================================================================
# 2. ALEMBIC CONFIGURATION
# ==============================================================================
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Динамическая инъекция URL БД. Скрывает пароли из alembic.ini
# str() обязателен для совместимости с Pydantic V2 PostgresDsn
config.set_main_option("sqlalchemy.url", str(settings.database_url))


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    Генерирует чистый SQL-скрипт без создания реального подключения к БД.
    Идеально для передачи SQL-дампов администраторам баз данных (DBA).
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Синхронный контекст выполнения.
    Вызывается внутри асинхронного Event Loop'а через `run_sync`.
    """
    context.configure(
        connection=connection, 
        target_metadata=target_metadata,
        # compare_type=True  # Раскомментируй, если нужно отслеживать изменение длины String(50) -> String(100)
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Создает AsyncEngine и проксирует миграции в синхронное ядро Alembic.
    """
    connectable: AsyncEngine = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Запрещаем пулинг соединений для миграций (освобождаем ресурсы сразу)
    )

    try:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        # Гарантированное закрытие соединений даже при падении миграции (OOM/Timeout)
        await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    Entrypoint для онлайн-миграций с защитой от уже запущенного Event Loop.
    """
    try:
        asyncio.run(run_async_migrations())
    except RuntimeError as e:
        # Graceful-деградация: если миграция запускается из уже работающего
        # асинхронного контекста (например, из pytest или Jupyter).
        if "already running" in str(e):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(run_async_migrations())
        else:
            raise


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()