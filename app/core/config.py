import os

from dotenv import load_dotenv
from fastapi import Query
from fastapi_pagination import Page as BasePage
from fastapi_pagination.customization import CustomizedPage, UseParamsFields
from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = os.getenv('PROJECT_NAME', 'FastAPI Boilerplate')
    API_V1_STR: str = os.getenv('API_V1_STR', '/api/v1')
    DEFAULT_PAGE_SIZE: int = int(os.getenv('DEFAULT_PAGE_SIZE', '30'))
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'local')

    # Security settings
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

    # CORS settings
    FRONTEND_URL: str = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    BACKEND_CORS_ORIGINS: str = os.getenv('BACKEND_CORS_ORIGINS', '')
    ALLOWED_ORIGINS: list[str] = []

    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str], info) -> list[str]:
        if isinstance(v, str) and not v.startswith('['):
            origins = [
                i.strip()
                for i in info.data.get('BACKEND_CORS_ORIGINS', '').split(',')
                if i
            ]
            if info.data.get('FRONTEND_URL'):
                origins.append(info.data['FRONTEND_URL'])
            return list(filter(None, origins))
        return v

    # Database settings
    DATABASE_URL: str | PostgresDsn

    # Email settings
    RESEND_API_KEY: str = os.getenv('RESEND_API_KEY')
    RESEND_FROM_EMAIL: str = os.getenv('RESEND_FROM_EMAIL')

    # Storage settings
    R2_ENDPOINT_URL: str = os.getenv('R2_ENDPOINT_URL')
    R2_ACCESS_KEY_ID: str = os.getenv('R2_ACCESS_KEY_ID')
    R2_SECRET_ACCESS_KEY: str = os.getenv('R2_SECRET_ACCESS_KEY')
    R2_BUCKET_NAME: str = os.getenv('R2_BUCKET_NAME')

    class Config:
        case_sensitive = True
        env_file = '.env'


settings = Settings()

Page = CustomizedPage[
    BasePage,
    UseParamsFields(
        size=Query(settings.DEFAULT_PAGE_SIZE, ge=0),
    ),
]
