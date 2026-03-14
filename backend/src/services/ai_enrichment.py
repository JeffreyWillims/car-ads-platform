import logging
from openai import AsyncOpenAI
from src.core.config import settings

logger = logging.getLogger(__name__)

# Инициализируем клиент
# Pydantic гарантирует, что переменные есть
client = AsyncOpenAI(
    api_key=settings.LLM_API_KEY if settings.LLM_API_KEY else "ollama",
    base_url=settings.LLM_BASE_URL
)


class AIEnrichmentService:
    """
    Сервис для обогащения данных с помощью LLM (Large Language Models).
    """

    @staticmethod
    async def generate_seo_description(brand: str, model: str, year: int, price: int, color: str) -> str | None:
        """
        Генерирует продающее описание автомобиля.
        """
        prompt = (
            f"Напиши привлекательное, краткое SEO-описание для продажи автомобиля: "
            f"{brand} {model}, {year} года выпуска. Цвет: {color}, Цена: {price} JPY. "
            f"Пиши на русском языке, эмоционально, не более 3 предложений. "
            f"Не используй Markdown, только чистый текст."
        )

        try:
            response = await client.chat.completions.create(
                model=settings.LLM_MODEL_NAME,
                messages=[
                    {"role": "system", "content": "Ты профессиональный автомаркетолог."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"LLM Generation failed: {e}")
            return None