from fastapi import APIRouter
from pydantic import BaseModel

from src.common.config import settings


class HealthResponse(BaseModel):
    status: str = 'ok'
    version: str


router = APIRouter(tags=['Health'])


@router.get('/health', response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring and Docker healthcheck
    """
    return HealthResponse(
        status='ok',
        version=settings.PROJECT_VERSION,
    )
