import logging
import uuid
from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class CarScraper:
    BASE_URL = "https://www.carsensor.net/usedcar/search.php"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def fetch_page(self, client: httpx.AsyncClient, page: int) -> str:
        url = f"{self.BASE_URL}?page={page}"
        response = await client.get(url, headers=self.headers, timeout=10.0)
        response.raise_for_status()
        return response.text

    def parse_html(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        cars = []

        # ... (тут твой код парсинга) ...

        # MOCK DATA FALLBACK
        if not cars:
            logger.warning("Генерирую MOCK-данные!")
            now = datetime.now(timezone.utc)

            # ВАЖНО: Ключи должны совпадать с моделью Car (brand, model, price...)
            cars.append({
                "brand": "Toyota",
                "model": "Camry 2.5",
                "price": 2500000,
                "year": 2021,
                "color": "Black",
                "link": f"https://example.com/car/{uuid.uuid4().hex[:8]}",
                "created_at": now,
                "updated_at": now,
            })
            cars.append({
                "brand": "Mazda",
                "model": "CX-5",
                "price": 3100000,
                "year": 2022,
                "color": "Red",
                "link": f"https://example.com/car/{uuid.uuid4().hex[:8]}",
                "created_at": now,
                "updated_at": now,
            })

        return cars

    async def run(self, max_pages: int = 1) -> list[dict]:
        all_cars = []
        async with httpx.AsyncClient() as client:
            for page in range(1, max_pages + 1):
                try:
                    html = await self.fetch_page(client, page)
                    cars = self.parse_html(html)
                    all_cars.extend(cars)
                except Exception as e:
                    logger.error(f"Error: {e}")
        return all_cars