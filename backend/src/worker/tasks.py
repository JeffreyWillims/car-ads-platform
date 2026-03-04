# backend/src/worker/tasks.py
import asyncio
from celery.utils.log import get_task_logger

# Импортируем конструкторы, но НЕ готовые объекты
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from src.core.celery_app import celery_app
from src.scraper.engine import CarSensorScraper
from src.repositories.car import CarRepository
from src.core.config import settings

logger = get_task_logger(__name__)


async def _run_scraping_pipeline():
    """
    Полностью изолированный пайплайн.
    Создает свои собственные соединения с БД, чтобы избежать конфликта Event Loop.
    """
    scraper = CarSensorScraper()
    logger.info("Starting car scraper engine...")

    # 1. Парсинг
    cars_data = await scraper.scrape_cars(pages_per_brand=1)

    if not cars_data:
        logger.warning("No cars scraped. Aborting DB insert.")
        return "No data"

    # =========================================================================
    # 🛡️ SCOPED ENGINE PATTERN (Критически важно!)
    # Мы создаем движок с нуля ЗДЕСЬ, а не импортируем его.
    # Это гарантирует, что он привяжется к ТЕКУЩЕМУ Event Loop'у этой задачи.
    # =========================================================================
    local_engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,  # Обязательно для Celery (fork-safe)
        echo=False
    )

    LocalSession = async_sessionmaker(
        bind=local_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    try:
        # 2. Работа с БД через локальную сессию
        async with LocalSession() as session:
            repo = CarRepository(session)
            logger.info(f"Upserting {len(cars_data)} cars into PostgreSQL...")
            await repo.bulk_upsert(cars_data)
    finally:
        # 3. Чистка ресурсов (закрываем соединения)
        await local_engine.dispose()

    logger.info("Pipeline finished successfully.")
    return f"Upserted {len(cars_data)} cars"


@celery_app.task(name="scrape_cars_task", bind=True, max_retries=3)
def scrape_cars_task(self):
    """
    Синхронная точка входа. Управляет жизненным циклом Event Loop.
    """
    # Создаем новый чистый цикл событий для этой задачи
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(_run_scraping_pipeline())
        return result
    except Exception as exc:
        logger.error(f"Scraper task failed: {exc}")
        # Retry через 60 секунд при ошибке
        raise self.retry(exc=exc, countdown=60)
    finally:
        # Корректное завершение всех асинхронных генераторов и закрытие цикла
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()