import json
import logging
from openai import AsyncOpenAI
from pydantic import SecretStr

from src.core.config import settings
from src.bot.schemas import CarSearchQuery

logger = logging.getLogger(__name__)

# Безопасное извлечение ключа
api_key = settings.LLM_API_KEY.get_secret_value() if isinstance(settings.LLM_API_KEY,
                                                                SecretStr) else settings.LLM_API_KEY

client = AsyncOpenAI(
    api_key=api_key,
    base_url=settings.LLM_BASE_URL
)

# Инструмент, который OpenAI (или Ollama) будет видеть
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_cars",
            "description": "Поиск машин в базе данных по заданным параметрам.",
            "parameters": CarSearchQuery.model_json_schema(),
        },
    }
]


async def analyze_user_query(text: str) -> CarSearchQuery | None:
    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты AI-ассистент по подбору японских автомобилей. "
                        "Твоя задача - извлечь параметры поиска из запроса и передать их в функцию search_cars. "
                        "Цвета обязательно переводи на английский язык."
                    )
                },
                {"role": "user", "content": text},
            ],
            tools=tools,
            tool_choice="auto",
        )

        message = response.choices[0].message

        # Если LLM решила вызвать функцию
        if message.tool_calls:
            args = message.tool_calls[0].function.arguments
            data = json.loads(args)
            logger.info(f"AI Extracted Filters: {data}")
            return CarSearchQuery(**data)

        logger.warning("AI did not trigger tool_calls.")
        return None

    except Exception as e:
        logger.error(f"AI Error during analysis: {e}")
        return None