from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore[import]

class Settings(BaseSettings):
    ELECTRUM_API_KEY: str = "default_dev_key"
    ELECTRUM_WEBHOOK_SECRET: str = "default_dev_secret"
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/taxifare"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Pydantic V2 Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()


