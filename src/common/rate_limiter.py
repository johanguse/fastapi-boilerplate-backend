"""
Rate limiting for API endpoints using slowapi.

This module provides rate limiting functionality to protect against:
- Brute force attacks (login, password reset)
- API abuse
- DDoS attempts

Features:
- Per-IP rate limiting
- Per-endpoint custom limits
- Automatic 429 responses
- Integration with audit logger
"""

import os

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded


def get_real_ip(request: Request) -> str:
    """
    Get the real client IP address, considering proxies.

    Checks X-Forwarded-For and X-Real-IP headers for proxied requests.
    Falls back to request.client.host if no proxy headers are present.

    Args:
        request: FastAPI request object

    Returns:
        Client IP address as string
    """
    # Check X-Forwarded-For (can contain multiple IPs: "client, proxy1, proxy2")
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        # Take the first IP (the original client)
        return forwarded_for.split(',')[0].strip()

    # Check X-Real-IP (single IP)
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip.strip()

    # Fallback to direct connection IP
    if request.client:
        return request.client.host

    return '127.0.0.1'  # Fallback for testing


# Initialize limiter
# Uses in-memory storage by default
# For production with multiple instances, use Redis:
# storage_uri="redis://localhost:6379"
IS_PRODUCTION = os.getenv('ENVIRONMENT', 'development') == 'production'

limiter = Limiter(
    key_func=get_real_ip,
    default_limits=['200/minute', '2000/hour'],  # Global defaults
    storage_uri='memory://',  # Use Redis in production for distributed limiting
    # storage_uri="redis://localhost:6379/0" if IS_PRODUCTION else "memory://",
    headers_enabled=True,  # Add X-RateLimit-* headers to responses
)


async def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> Response:
    """
    Custom error handler for rate limit violations.

    Returns a JSON response with:
    - 429 status code
    - User-friendly error message
    - Retry-After header
    - Rate limit information in headers

    Also logs the violation for security monitoring.
    """
    # Log rate limit violation
    try:
        from src.common.audit_logger import AuditLogger, EventStatus

        client_ip = get_real_ip(request)

        AuditLogger.log_security_alert(  # type: ignore
            action='rate_limit_exceeded',
            status=EventStatus.WARNING,  # type: ignore
            ip_address=client_ip,
            metadata={
                'path': str(request.url.path),
                'method': request.method,
                'user_agent': request.headers.get('user-agent'),
                'limit': str(exc.detail)
                if hasattr(exc, 'detail')
                else 'unknown',
            },
            message=f'Rate limit exceeded for {request.method} {request.url.path}',
        )
    except Exception:
        # Don't let logging errors break the rate limit response
        pass

    return JSONResponse(
        status_code=429,
        content={
            'detail': 'Too many requests. Please slow down and try again later.',
            'error': 'rate_limit_exceeded',
            'retry_after': exc.detail
            if hasattr(exc, 'detail')
            else '60 seconds',
        },
        headers={
            'Retry-After': '60',
        },
    )


# Rate limit presets for common use cases

# Authentication endpoints - strict limits
AUTH_LIMIT = '5/minute'  # 5 attempts per minute
AUTH_LIMIT_HOURLY = '20/hour'  # 20 attempts per hour

# Password reset - very strict
PASSWORD_RESET_LIMIT = '3/hour'  # 3 attempts per hour
PASSWORD_RESET_DAILY = '10/day'  # 10 attempts per day

# Email verification/resend - moderate
EMAIL_LIMIT = '10/hour'  # 10 emails per hour

# Organization operations - moderate
ORG_LIMIT = '30/minute'  # 30 operations per minute

# General API - lenient
API_LIMIT = '100/minute'  # 100 requests per minute
API_LIMIT_HOURLY = '1000/hour'  # 1000 requests per hour

# Public endpoints - very lenient
PUBLIC_LIMIT = '200/minute'  # 200 requests per minute
