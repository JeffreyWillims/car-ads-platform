# python 3.12+
from openai import AsyncOpenAI
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

# ==============================================================================
# 1. CONFIGURATION LAYER (Pydantic V2 Strict Validation)
# ==============================================================================
class AISettings(BaseSettings):
    llm_api_key: SecretStr
    llm_base_url: str
    llm_model_name: str

    # FIX: Современный подход Pydantic V2 вместо устаревшего class Config
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

ai_settings = AISettings()

# ==============================================================================
# 2. CLIENT INITIALIZATION (Thread-Safe Singleton)
# ==============================================================================
ai_client = AsyncOpenAI(
    api_key=ai_settings.llm_api_key.get_secret_value(),
    base_url=ai_settings.llm_base_url
)

# ==============================================================================
# 3. DOMAIN SERVICE LOGIC
# ==============================================================================
async def generate_car_description(brand: str, model: str, year: int, mileage: int) -> str:
    """
    O(1) Сетевой вызов. Генерация SEO-оптимизированного описания автомобиля.
    Использует локальную модель через API, совместимое с OpenAI.
    """
    prompt = (
        f"Ты опытный автодилер. Напиши короткое, продающее описание для "
        f"автомобиля {brand} {model}, {year} года выпуска с пробегом {mileage} км. "
        f"Текст должен быть на русском языке, без воды, с акцентом на надежность."
    )

    response = await ai_client.chat.completions.create(
        model=ai_settings.llm_model_name,
        messages=[
            {"role": "system", "content": "Ты профессиональный копирайтер автосалона."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=300
    )

    return response.choices[0].message.content.strip()