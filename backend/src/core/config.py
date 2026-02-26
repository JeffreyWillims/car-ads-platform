from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Enterprise Configuration Management.
    """
    DATABASE_URL: str
    SECRET_KEY: str = "super-secret-key-change-in-production"

    # 2. Настройки чтения .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()