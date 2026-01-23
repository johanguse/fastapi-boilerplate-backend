"""Main router combining all Better Auth routes."""

from fastapi import APIRouter

from .auth_routes import router as auth_router
from .oauth_routes import router as oauth_router
from .organization_routes import router as org_router

router = APIRouter()

# Include all sub-routers
router.include_router(auth_router)
router.include_router(oauth_router)
router.include_router(org_router)

__all__ = ['router']
