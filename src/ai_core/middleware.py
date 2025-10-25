"""AI usage limits middleware."""

import logging
from typing import Callable

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class AIUsageLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to check AI usage limits."""

    def __init__(self, app, ai_routes_prefix: str = "/api/v1/ai-"):
        super().__init__(app)
        self.ai_routes_prefix = ai_routes_prefix

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check AI usage limits for AI routes."""
        # Skip if not an AI route
        if not request.url.path.startswith(self.ai_routes_prefix):
            return await call_next(request)

        # Skip if no user context (will be handled by auth middleware)
        if not hasattr(request.state, 'user') or not request.state.user:
            return await call_next(request)

        # Skip if no organization context
        if not hasattr(request.state, 'organization_id') or not request.state.organization_id:
            return await call_next(request)

        # Extract feature from path
        feature = self._extract_feature_from_path(request.url.path)
        if not feature:
            return await call_next(request)

        # Check usage limits
        from src.common.database import get_async_session
        from src.ai_core.usage_limits import AIUsageLimitService

        async with get_async_session() as db:
            usage_service = AIUsageLimitService(db)
            can_use, error = await usage_service.check_usage_limit(
                request.state.organization_id, feature
            )

            if not can_use:
                raise HTTPException(
                    status_code=402,  # Payment Required
                    detail=error or "AI usage limit exceeded"
                )

        return await call_next(request)

    def _extract_feature_from_path(self, path: str) -> Optional[str]:
        """Extract AI feature from request path."""
        if "/ai-documents/" in path:
            return "documents"
        elif "/ai-content/" in path:
            return "content"
        elif "/ai-analytics/" in path:
            return "analytics"
        return None
