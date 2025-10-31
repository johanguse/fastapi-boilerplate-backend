"""Cookie utilities for Better Auth compatibility."""

from typing import Any, Dict, Optional
from urllib.parse import urlparse

from fastapi import Response

from src.common.config import settings


def _cookie_options() -> Dict[str, Any]:
    """Derive cookie security options from FRONTEND_URL.

    - secure=True when FRONTEND_URL is https
    - samesite=None (sent as 'none') when secure, else 'lax'
    - domain set to FRONTEND_URL hostname when not localhost
    """
    frontend = settings.FRONTEND_URL or ''
    secure = frontend.startswith('https')
    samesite = 'none' if secure else 'lax'
    domain: Optional[str] = None
    try:
        parsed = urlparse(frontend)
        host = parsed.hostname
        if host and host not in {'localhost', '127.0.0.1'}:
            domain = host
    except Exception:
        domain = None
    return {'secure': secure, 'samesite': samesite, 'domain': domain}


def set_auth_cookie(
    response: Response, key: str, value: str, path: str = '/'
) -> None:
    """Set an authentication cookie with proper security options."""
    opts = _cookie_options()
    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        secure=opts['secure'],
        samesite=opts['samesite'],
        path=path,
        domain=opts['domain'],
    )


def delete_auth_cookie(response: Response, key: str, path: str = '/') -> None:
    """Delete an authentication cookie."""
    opts = _cookie_options()
    response.delete_cookie(key=key, path=path, domain=opts['domain'])
