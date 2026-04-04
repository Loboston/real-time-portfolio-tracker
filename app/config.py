from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours

    # App
    environment: str = "development"
    log_level: str = "INFO"

    # Market data (used in Phase 4)
    price_poll_interval_seconds: int = 5

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
