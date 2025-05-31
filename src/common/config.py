import os
from typing import Union

from dotenv import load_dotenv
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = os.getenv('PROJECT_NAME', 'AI Chat SaaS API')
    PROJECT_VERSION: str = os.getenv('PROJECT_VERSION', '0.0.1')
    PROJECT_DESCRIPTION: str = os.getenv(
        'PROJECT_DESCRIPTION',
        'API for AI Chat SaaS application with team management and training capabilities',
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

    # AI
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    EMBEDDING_MODEL: str = 'text-embedding-3-small'
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    TOP_K_RESULTS: int = 5

    ALLOWED_FILE_TYPES: list = [
        'text/plain',
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/markdown',
        'text/x-markdown',
        'text/mdx',
    ]

    class Config:
        case_sensitive = True
        env_file = '.env'


settings = Settings()
