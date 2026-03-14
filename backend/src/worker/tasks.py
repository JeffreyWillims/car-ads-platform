import asyncio
from celery.utils.log import get_task_logger

from src.core.celery_app import celery_app
from src.scraper.engine import CarSensorScraper

from src.core.database import AsyncSessionLocal
from src.repositories.car import CarRepository
from src.services.ai_enrichment import AIEnrichmentService

logger = get_task_logger(__name__)


# ==============================================================================
# SCRAPING PIPELINE
# ==============================================================================
async def _run_scraping_pipeline():
    """
    Асинхронная корутина для сбора и сохранения данных.
    """
    scraper = CarSensorScraper()
    logger.info("Starting car scraper engine...")

    # Парсим 1 страницу (для теста)
    cars_data = await scraper.scrape_cars(pages_per_brand=1)

    if not cars_data:
        logger.warning("No cars scraped. Aborting DB insert.")
        return "No data"

    # Сохраняем в базу данных (Используем наш глобальный, но fork-safe сессионный мейкер)
    async with AsyncSessionLocal() as session:
        repo = CarRepository(session)
        logger.info(f"Upserting {len(cars_data)} cars into PostgreSQL...")
        await repo.bulk_upsert(cars_data)

    logger.info("Pipeline finished successfully.")
    return f"Upserted {len(cars_data)} cars"


@celery_app.task(name="scrape_cars_task", bind=True, max_retries=3)
def scrape_cars_task(self):
    """
    Синхронная обертка для Celery.
    """
    try:
        # asyncio.run() автоматически управляет Event Loop
        result = asyncio.run(_run_scraping_pipeline())

        # Скрапер успешно отработал -> Триггерим задачу ИИ обогащения
        enrich_cars_with_ai_task.delay()

        return result
    except Exception as exc:
        logger.error(f"Scraper task failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


# ==============================================================================
# AI ENRICHMENT PIPELINE
# ==============================================================================
async def _run_ai_enrichment():
    """
    Асинхронное ядро для обогащения данных с помощью Ollama/OpenAI.
    """
    logger.info("Starting AI Enrichment pipeline...")

    async with AsyncSessionLocal() as session:
        repo = CarRepository(session)
        # Берем батч машин без описания (5 штук, чтобы не перегрузить LLM)
        cars = await repo.get_cars_without_description(batch_size=5)

        if not cars:
            logger.info("No cars need AI enrichment at the moment.")
            return "No cars to enrich"

        enriched_count = 0
        # Обрабатываем последовательно
        for car in cars:
            logger.info(f"Generating description for Car ID: {car.id} ({car.brand} {car.model})")

            description = await AIEnrichmentService.generate_seo_description(
                brand=car.brand,
                model=car.model,
                year=car.year,
                price=car.price,
                color=car.color
            )

            if description:
                # Сохраняем результат в БД
                await repo.update_description(car.id, description)
                enriched_count += 1

    return f"Successfully enriched {enriched_count} cars."


@celery_app.task(name="enrich_cars_with_ai_task", bind=True, max_retries=3)
def enrich_cars_with_ai_task(self):
    """Синхронная обертка для Celery AI Task."""
    try:
        result = asyncio.run(_run_ai_enrichment())
        return result
    except Exception as exc:
        logger.error(f"AI Enrichment task failed: {exc}")
        raise self.retry(exc=exc, countdown=120)