from pydantic import SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ==========================================
    # Метаданные приложения (Значения по умолчанию)
    # ==========================================
    PROJECT_NAME: str = "Car Ads Platform API"
    VERSION: str = "1.0.0"

    # ==========================================
    # Инфраструктура (Ожидаем из .env или ОС)
    # ==========================================
    POSTGRES_USER: str
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432

    # ==========================================
    # Безопасность
    # ==========================================
    SECRET_KEY: SecretStr
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # Время жизни токена по умолчанию

    # ==========================================
    # Вычисляемые поля (Computed Fields)
    # ==========================================
    @computed_field
    @property
    def database_url(self) -> str:
        """Сборка DSN для SQLAlchemy (AsyncPG)"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD.get_secret_value()}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Настройки самого Pydantic Settings
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Игнорируем лишние ключи из .env (например, FRONTEND_PORT)
    )


settings = Settings()