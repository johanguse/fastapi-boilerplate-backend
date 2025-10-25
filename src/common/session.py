import logging

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.common.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL.replace(
    'postgresql://', 'postgresql+asyncpg://'
)

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, 
    echo=True,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "command_timeout": 60,
        "server_settings": {
            "application_name": "fastapi_saas_boilerplate",
        }
    }
)
async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_async_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session
