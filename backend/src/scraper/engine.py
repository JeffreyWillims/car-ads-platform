# backend/src/scraper/engine.py
import asyncio
import logging
import re
from typing import List, Dict, Any
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class CarSensorScraper:
    BASE_URL = "https://www.carsensor.net"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Referer": "https://www.carsensor.net/",
    }

    # Маппинг URL-кодов на реальные бренды
    TARGET_BRANDS = {
        "bTO": "Toyota",
        "bHO": "Honda",
        "bNI": "Nissan",
        "bMA": "Mazda"
    }

    # Маппинг японских цветов на английские
    COLOR_MAP = {
        "黒": "Black", "ブラック": "Black",
        "白": "White", "ホワイト": "White", "パール": "Pearl",
        "赤": "Red", "レッド": "Red",
        "青": "Blue", "ブルー": "Blue",
        "銀": "Silver", "シルバー": "Silver",
        "灰": "Grey", "グレー": "Grey"
    }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def _fetch_page(self, client: httpx.AsyncClient, url: str) -> str:
        logger.info(f"Fetching: {url}")
        response = await client.get(url, headers=self.HEADERS, timeout=20.0)
        response.raise_for_status()
        return response.text

    async def scrape_cars(self, pages_per_brand: int = 1) -> List[Dict[str, Any]]:
        cars_dict: Dict[str, Dict[str, Any]] = {}
        now = datetime.now(timezone.utc)

        async with httpx.AsyncClient(http2=True, follow_redirects=True) as client:
            # Проходимся по 4 разным маркам автомобилей
            for brand_code, brand_name in self.TARGET_BRANDS.items():
                logger.info(f"🚗 Starting scraping for brand: {brand_name}")

                for page in range(1, pages_per_brand + 1):
                    # Динамически меняем URL под бренд
                    url = f"{self.BASE_URL}/usedcar/{brand_code}/index{page}.html"

                    try:
                        html = await self._fetch_page(client, url)
                    except httpx.HTTPError as e:
                        logger.error(f"Network error on {url}: {e}")
                        continue

                    soup = BeautifulSoup(html, "html.parser")

                    # Ищем карточки целиком, чтобы вытащить картинку и текст
                    car_cards = (
                            soup.select(".casetBoard") or
                            soup.select(".cassette") or
                            soup.select(".caset") or
                            soup.select(".list-item") or  # Общий класс списков
                            soup.select(".property_unit")  # Часто используется в каталогах
                    )

                    if not car_cards:
                        logger.warning(f"⚠️ No cards found for {brand_name} on page {page}.")
                        continue

                    logger.info(f"✅ Found {len(car_cards)} potential cards on page {page} for {brand_name}!")

                    for card in car_cards:
                        try:
                            # 1. Ссылка
                            link_tag = (
                                    card.select_one("a[href*='/usedcar/detail/']") or
                                    card.select_one("h3 a") or
                                    card.select_one(".casetBoard_carName a")
                            )
                            if not link_tag:
                                continue

                            href = link_tag.get("href", "")
                            full_link = self.BASE_URL + href if href.startswith("/") else href
                            clean_link = full_link.split("?")[0]

                            if clean_link in cars_dict:
                                continue

                            # 2. Картинка (Data Enrichment)
                            img_tag = card.select_one("img")
                            image_url = img_tag.get("data-src") or img_tag.get("src") if img_tag else None

                            # 3. Весь текст карточки для Regex поиска
                            card_text = card.get_text(separator=" ", strip=True)

                            # 4. Модель
                            model = link_tag.get_text(strip=True) or "Unknown Model"

                            # 5. Цена
                            price = 0
                            price_match = re.search(r'(\d+\.?\d*)\s*万円', card_text)
                            if price_match:
                                price = int(float(price_match.group(1)) * 10000)

                            # 6. Год (Data Enrichment)
                            year = 0
                            year_match = re.search(r'(20\d{2}|19\d{2})\s*年', card_text)
                            if year_match:
                                year = int(year_match.group(1))

                            # 7. Пробег (Data Enrichment)
                            mileage = 0
                            mil_match_man = re.search(r'(\d+\.?\d*)\s*万km', card_text)
                            if mil_match_man:
                                mileage = int(float(mil_match_man.group(1)) * 10000)
                            else:
                                mil_match_km = re.search(r'(\d+)\s*km', card_text)
                                if mil_match_km:
                                    mileage = int(mil_match_km.group(1))

                            # 8. Цвет (Data Enrichment)
                            color = "Other"
                            for jp_color, en_color in self.COLOR_MAP.items():
                                if jp_color in card_text:
                                    color = en_color
                                    break

                            # Сохраняем в словарь
                            cars_dict[clean_link] = {
                                "brand": brand_name,  # Динамический бренд
                                "model": model[:100],  # Ограничиваем длину
                                "year": year if year > 0 else 2020,
                                "price": price if price > 0 else 1000000,
                                "color": color[:50],
                                "mileage": mileage,  # НОВОЕ ПОЛЕ
                                "link": clean_link[:500],
                                "image_url": image_url[:1000] if image_url else None,  # НОВОЕ ПОЛЕ
                                "created_at": now,
                                "updated_at": now,
                            }
                        except Exception as e:
                            logger.debug(f"Parsing error for specific card: {e}")

                    await asyncio.sleep(1)

        unique_cars = list(cars_dict.values())
        logger.info(f"🚀 Extracted {len(unique_cars)} STRICTLY UNIQUE cars across all brands.")

        # Если почему-то вообще ничего не спарсилось, выдаем Mock
        if not unique_cars:
            return self._generate_synthetic_data(now)

        return unique_cars

    def _generate_synthetic_data(self, current_time: datetime) -> List[Dict[str, Any]]:
        import uuid
        return [{
            "brand": "Toyota",
            "model": "Fallback Data",
            "year": 2024,
            "price": 2500000,
            "color": "White",
            "mileage": 15000,
            "link": f"https://www.carsensor.net/usedcar/detail/{uuid.uuid4()}",
            "image_url": "https://placehold.co/600x400?text=No+Image",
            "created_at": current_time,
            "updated_at": current_time,
        } for _ in range(5)]