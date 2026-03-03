import json
from openai import AsyncOpenAI
from pydantic import SecretStr
from src.core.config import settings
from src.bot.schemas import CarSearchQuery

# ==============================================================================
# 1. SAFE CREDENTIALS RESOLUTION
# ==============================================================================
raw_key = getattr(settings, "LLM_API_KEY", None)

if isinstance(raw_key, SecretStr):
    api_key = raw_key.get_secret_value()
else:
    api_key = raw_key or "mock"

base_url = getattr(settings, "LLM_BASE_URL", None)

client = AsyncOpenAI(
    api_key=api_key,
    base_url=base_url
)

# Описание "инструмента" для OpenAI
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_cars",
            "description": "Поиск машин в базе данных по параметрам",
            "parameters": CarSearchQuery.model_json_schema(),
        },
    }
]


async def analyze_user_query(text: str) -> CarSearchQuery | None:
    try:
        response = await client.chat.completions.create(
            # Если юзаешь Ollama - поставь llama3.1, если прокси - оставь gpt-4o-mini
            model=settings.LLM_MODEL_NAME if hasattr(settings, "LLM_MODEL_NAME") else "gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты помощник по авто. Выдели параметры из запроса."},
                {"role": "user", "content": text},
            ],
            tools=tools,
            tool_choice="auto",
        )

        tool_calls = response.choices[0].message.tool_calls

        if tool_calls:
            # OpenAI решил вызвать функцию
            args = tool_calls[0].function.arguments
            data = json.loads(args)
            return CarSearchQuery(**data)

        return None
    except Exception as e:
        print(f"AI Error: {e}")
        return None