"""Application configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "AAM Registry"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    secret_key: str = Field(default="change-me-in-production")

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://aam:aam@localhost:5432/aam"
    )
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Redis
    redis_url: RedisDsn = Field(default="redis://localhost:6379/0")

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Storage
    storage_backend: Literal["local", "s3"] = "local"
    storage_local_path: str = "/data/packages"
    s3_bucket: str = ""
    s3_region: str = "us-east-1"
    s3_endpoint_url: str | None = None

    # CORS
    cors_origins: list[str] = Field(default=["http://localhost:3000", "http://localhost:5173"])

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # Logging
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
