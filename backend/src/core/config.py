# backend/src/core/config.py
from pydantic import SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # ==========================================
    # 📝 Метаданные приложения
    # ==========================================
    PROJECT_NAME: str = "Car Ads Platform API"
    VERSION: str = "1.0.0"

    # ==========================================
    # 🗄️ Database Infrastructure (PostgreSQL)
    # ==========================================
    POSTGRES_USER: str
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432

    # ==========================================
    # ⚡ Cache & Broker Infrastructure (Redis)
    # ==========================================
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    # ==========================================
    # 🤖 External Services (Bot & AI)
    # ==========================================
    # Токен Telegram (обязателен)
    BOT_TOKEN: SecretStr

    # Настройки LLM (Ollama).
    # Задаем дефолты для Docker -> Host коммуникации.
    LLM_API_KEY: str = "ollama"  # Заглушка, т.к. локальная Ollama не требует ключа
    LLM_BASE_URL: str = "http://host.docker.internal:11434/v1"
    LLM_MODEL_NAME: str = "llama3"

    # Legacy OpenAI (Оставляем опциональным для обратной совместимости)
    OPENAI_API_KEY: SecretStr | None = None

    # ==========================================
    # 🔐 Безопасность (Auth)
    # ==========================================
    SECRET_KEY: SecretStr
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ==========================================
    # 🧮 Computed Fields (Авто-сборка URL)
    # ==========================================
    @computed_field
    @property
    def database_url(self) -> str:
        """Сборка DSN для SQLAlchemy (AsyncPG)"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD.get_secret_value()}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @computed_field
    @property
    def redis_url(self) -> str:
        """Сборка URL для Celery и Redis Client"""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # ==========================================
    # ⚙️ Pydantic Config
    # ==========================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Игнорировать лишние переменные (например, FRONTEND_PORT)
    )

# Синглтон настроек
settings = Settings()