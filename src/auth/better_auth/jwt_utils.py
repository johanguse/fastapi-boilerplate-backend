"""JWT token utilities for Better Auth compatibility."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt

from src.common.config import settings

logger = logging.getLogger(__name__)


def create_better_auth_jwt(user: Any) -> str:
    """Create a JWT token in Better Auth format but compatible with FastAPI Users."""
    payload = {
        'sub': str(user.id),  # Subject (user ID)
        'email': user.email,
        'name': getattr(user, 'name', user.email.split('@')[0]),
        'iat': datetime.now(timezone.utc),
        'exp': datetime.now(timezone.utc)
        + timedelta(seconds=settings.JWT_LIFETIME_SECONDS),
        'aud': [
            'fastapi-users:auth'
        ],  # Keep FastAPI Users audience for compatibility
        'iss': 'better-auth-compat',  # Better Auth compatible issuer
    }

    return jwt.encode(
        payload, settings.JWT_SECRET, algorithm=settings.ALGORITHM
    )


def verify_better_auth_jwt(token: str) -> Optional[Dict[str, Any]]:
    """Verify Better Auth JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.ALGORITHM],
            audience=['fastapi-users:auth'],
        )
        return payload
    except jwt.InvalidTokenError:
        return None
