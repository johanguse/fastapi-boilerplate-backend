from functools import cache
from typing import Optional

from pydantic import EmailStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Environment
    ENV_STATE: str = "dev"
    DROP_ENVS: list[str] = ["test"]

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/fastapi_db"
    )

    # Security
    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for JWT tokens",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    RESET_TOKEN_EXPIRE_MINUTES: int = 15

    # Email
    RESEND_API_KEY: Optional[str] = Field(
        None, description="Resend API key for email sending"
    )
    FROM_EMAIL: EmailStr = "noreply@example.com"

    # Admin
    ADMIN_EMAIL: EmailStr = "admin@example.com"
    ADMIN_PASSWORD: str = "admin123"
    ADMIN_NAME: str = "Admin User"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour in seconds

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Application
    APP_NAME: str = "FastAPI Boilerplate"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False


class TestConfig(BaseConfig):
    model_config = SettingsConfigDict(env_file=".env.test", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/test_db"
    SECRET_KEY: str = "test-secret-key"
    LOG_LEVEL: str = "DEBUG"
    DEBUG: bool = True
    RESEND_API_KEY: Optional[str] = None  # Don't send real emails in tests


class DevConfig(BaseConfig):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="DEV_", extra="ignore"
    )

    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/fastapi_db"
    )
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours for development
    LOG_LEVEL: str = "DEBUG"
    DEBUG: bool = True


class ProdConfig(BaseConfig):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="PROD_", extra="ignore"
    )

    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ALLOWED_ORIGINS: list[str] = []  # Set specific origins in production


@cache
def get_config(env: str = "dev") -> TestConfig | DevConfig | ProdConfig:
    configs = {"test": TestConfig, "dev": DevConfig, "prod": ProdConfig}
    return configs[env](ENV_STATE=env)


config = get_config(env=BaseConfig().ENV_STATE)
