from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore[import]

class Settings(BaseSettings):
    ELECTRUM_API_KEY: str = "default_dev_key"
    ELECTRUM_WEBHOOK_SECRET: str = "default_dev_secret"
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/taxifare"
    REDIS_URL: str = "redis://localhost:6379/0"

    # ---- JWT Security Settings ----
    JWT_SECRET_KEY: str = "generate_a_random_secure_string_for_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720  # 12-hour shift duration

    # Pydantic V2 Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()


