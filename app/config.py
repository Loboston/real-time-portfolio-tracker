from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database — either full URL or individual parts
    database_url: Optional[str] = None
    db_host: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    db_name: Optional[str] = None

    def get_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if self.db_host and self.db_user and self.db_password and self.db_name:
            return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}/{self.db_name}"
        raise ValueError("Either DATABASE_URL or DB_HOST/DB_USER/DB_PASSWORD/DB_NAME must be set")

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours

    # App
    environment: str = "development"
    log_level: str = "INFO"

    # Market data
    price_poll_interval_seconds: int = 5
    polygon_api_key: str | None = None

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
