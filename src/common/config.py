import os
from functools import lru_cache
from typing import Union

from dotenv import load_dotenv
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        case_sensitive=True,
        extra='ignore',
    )
    PROJECT_NAME: str = os.getenv('PROJECT_NAME', 'FastAPI SaaS Boilerplate')
    PROJECT_VERSION: str = os.getenv('PROJECT_VERSION', '0.0.1')
    PROJECT_DESCRIPTION: str = os.getenv(
        'PROJECT_DESCRIPTION',
        'Boilerplate API for SaaS apps with auth, teams, projects, payments, logs, and uploads',
    )
    API_V1_STR: str = os.getenv('API_V1_STR', '/api/v1')

    DEFAULT_PAGE_SIZE: int = int(os.getenv('DEFAULT_PAGE_SIZE', '30'))

    SECRET_KEY: str = os.getenv('SECRET_KEY')
    JWT_SECRET: str = os.getenv('JWT_SECRET', 'your-secret-key')
    JWT_LIFETIME_SECONDS: int = int(os.getenv('JWT_LIFETIME_SECONDS', '3600'))

    ALGORITHM: str = os.getenv('ALGORITHM', 'HS256')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30')
    )
    REFRESH_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv('REFRESH_TOKEN_EXPIRE_MINUTES', '10080')
    )

    FRONTEND_URL: str = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    ALLOWED_ORIGINS: list[str] = [
        FRONTEND_URL,
        'http://localhost:5173',
        'http://127.0.0.1:5173',
    ]

    DATABASE_URL: Union[str, PostgresDsn]

    # Better Auth (optional) JWT acceptance alongside FastAPI Users
    BETTER_AUTH_ENABLED: bool = bool(os.getenv('BETTER_AUTH_ENABLED', ''))
    BETTER_AUTH_ALGORITHM: str = os.getenv('BETTER_AUTH_ALGORITHM', 'RS256')
    BETTER_AUTH_JWKS_URL: str | None = os.getenv('BETTER_AUTH_JWKS_URL')
    BETTER_AUTH_SHARED_SECRET: str | None = os.getenv(
        'BETTER_AUTH_SHARED_SECRET'
    )
    BETTER_AUTH_ISSUER: str | None = os.getenv('BETTER_AUTH_ISSUER')
    BETTER_AUTH_AUDIENCE: str | None = os.getenv('BETTER_AUTH_AUDIENCE')
    BETTER_AUTH_EMAIL_CLAIM: str = os.getenv(
        'BETTER_AUTH_EMAIL_CLAIM', 'email'
    )
    BETTER_AUTH_SUB_IS_EMAIL: bool = (
        os.getenv('BETTER_AUTH_SUB_IS_EMAIL', 'false').lower() == 'true'
    )

    RESEND_API_KEY: str = os.getenv('RESEND_API_KEY')
    RESEND_FROM_EMAIL: str = os.getenv('RESEND_FROM_EMAIL')

    R2_ENDPOINT_URL: str = os.getenv('R2_ENDPOINT_URL')
    R2_ACCESS_KEY_ID: str = os.getenv('R2_ACCESS_KEY_ID')
    R2_SECRET_ACCESS_KEY: str = os.getenv('R2_SECRET_ACCESS_KEY')
    R2_BUCKET_NAME: str = os.getenv('R2_BUCKET_NAME')

    # Stripe
    STRIPE_SECRET_KEY: str = ''
    STRIPE_WEBHOOK_SECRET: str = ''
    STRIPE_PUBLIC_KEY: str = ''
    STRIPE_PLANS: dict = {
        # Starter
        'price_1M': {
            'name': 'starter',
            'price': 990,
            'interval': 'month',
            'max_projects': 1,
        },
        'price_1Y': {
            'name': 'starter',
            'price': 9900,
            'interval': 'year',
            'max_projects': 1,
        },
        # Pro
        'price_2M': {
            'name': 'pro',
            'price': 2990,
            'interval': 'month',
            'max_projects': 5,
        },
        'price_2Y': {
            'name': 'pro',
            'price': 29900,
            'interval': 'year',
            'max_projects': 5,
        },
        # Business
        'price_3M': {
            'name': 'business',
            'price': 9990,
            'interval': 'month',
            'max_projects': 20,
        },
        'price_3Y': {
            'name': 'business',
            'price': 99900,
            'interval': 'year',
            'max_projects': 20,
        },
    }
    PAYMENT_SUCCESS_URL: str = 'https://yourapp.com/success'
    PAYMENT_CANCEL_URL: str = 'https://yourapp.com/cancel'

    # OAuth Providers
    GOOGLE_CLIENT_ID: str = os.getenv('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET: str = os.getenv('GOOGLE_CLIENT_SECRET', '')

    GITHUB_CLIENT_ID: str = os.getenv('GITHUB_CLIENT_ID', '')
    GITHUB_CLIENT_SECRET: str = os.getenv('GITHUB_CLIENT_SECRET', '')

    MICROSOFT_CLIENT_ID: str = os.getenv('MICROSOFT_CLIENT_ID', '')
    MICROSOFT_CLIENT_SECRET: str = os.getenv('MICROSOFT_CLIENT_SECRET', '')

    APPLE_CLIENT_ID: str = os.getenv('APPLE_CLIENT_ID', '')
    APPLE_CLIENT_SECRET: str = os.getenv('APPLE_CLIENT_SECRET', '')
    APPLE_TEAM_ID: str = os.getenv('APPLE_TEAM_ID', '')
    APPLE_KEY_ID: str = os.getenv('APPLE_KEY_ID', '')
    APPLE_PRIVATE_KEY: str = os.getenv('APPLE_PRIVATE_KEY', '')

    # Uploads
    ALLOWED_FILE_TYPES: list = [
        'text/plain',
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'image/png',
        'image/jpeg',
    ]


settings = Settings()


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance to avoid re-creating the settings object.
    This provides significant performance improvement for dependency injection.
    """
    return Settings()
