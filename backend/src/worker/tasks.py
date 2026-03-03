import asyncio
import logging
from celery import shared_task


from src.core.database import AsyncSessionLocal
from src.services.scraper import CarScraper
from src.repositories.car import CarRepository

# Наш новый AI сервис
from src.services.ai_generator import generate_car_description

logger = logging.getLogger(__name__)


# ==============================================================================
# 1. DATA INGESTION (Скрапинг)
# ==============================================================================
async def run_scraping_logic():
    scraper = CarScraper()
    logger.info("Starting scraper...")

    cars_data = await scraper.run(max_pages=1)
    logger.info(f"Scraped {len(cars_data)} cars.")

    if not cars_data:
        return "No cars found"

    async with AsyncSessionLocal() as session:
        repo = CarRepository(session)
        count = await repo.upsert_bulk(cars_data)
        return f"Upserted {count} cars"


@shared_task(name="scrape_cars_task")
def scrape_cars_task():
    try:
        return asyncio.run(run_scraping_logic())
    except Exception as e:
        logger.error(f"Scrape Task failed: {e}")
        raise e


# ==============================================================================
# 2. DATA ENRICHMENT (Локальная Нейросеть Ollama)
# ==============================================================================
async def run_ai_enrichment_logic():
    """
    Берет "сырые" машины из базы и прогоняет их через локальную Ollama.
    """
    logger.info("Starting AI enrichment pipeline...")

    async with AsyncSessionLocal() as session:
        repo = CarRepository(session)

        # Берем партию необработанных авто (например, 5 штук)
        cars_to_process = await repo.get_cars_without_description(batch_size=5)

        if not cars_to_process:
            logger.info("No cars require AI enrichment right now.")
            return "No cars to process"

        processed_count = 0
        for car in cars_to_process:
            try:
                logger.info(f"Generating AI description for: {car.title} (ID: {car.id})")

                # Поскольку в твоей модели Car поля называются title/price/color:
                # Адаптируем вызов!
                # P.S. Если функция generate_car_description ожидает brand/model,
                # просто передай car.title в brand, а остальные заглушками, либо обнови саму функцию.
                description = await generate_car_description(
                    brand=car.title,  # Используем title вместо brand
                    model="",  # пусто
                    year=car.year,
                    mileage=0  # Если пробега нет в модели, ставим 0
                )

                await repo.update_description(car.id, description)
                processed_count += 1
                logger.info(f"Successfully enriched car ID: {car.id}")

            except Exception as e:
                logger.error(f"Failed to generate description for car {car.id}: {e}")
                # Если одна машина упала, продолжаем обрабатывать остальные из батча
                continue

        return f"AI Enriched {processed_count} cars"


@shared_task(name="enrich_cars_with_ai_task", max_retries=3)
def enrich_cars_with_ai_task():
    """
    Независимая задача. Можно вызывать по расписанию (Celery Beat)
    каждые 5 минут или ставить в очередь (chain) сразу после скрапинга.
    """
    try:
        return asyncio.run(run_ai_enrichment_logic())
    except Exception as e:
        logger.error(f"AI Enrichment Task failed: {e}")
        raise e