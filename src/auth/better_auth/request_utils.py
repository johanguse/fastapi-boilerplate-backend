"""Request utilities for Better Auth compatibility."""

from typing import Optional

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User

from .jwt_utils import verify_better_auth_jwt


def get_token_from_request(request: Request) -> Optional[str]:
    """Extract JWT from Authorization header or fallback to session cookie."""
    # Bearer token first
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]
    # Fallback to cookie set by this compat layer
    cookie_token = request.cookies.get('ba_session')
    if cookie_token:
        return cookie_token
    return None


async def get_user_from_request(
    request: Request, session: AsyncSession
) -> User:
    """Get the authenticated user from the request."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail='No valid session')
    payload = verify_better_auth_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail='Invalid token')
    user_id = int(payload['sub'])  # type: ignore[index]
    result = await session.execute(
        select(User).where(User.id == user_id)  # type: ignore[arg-type]
    )
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=401, detail='User not found or inactive'
        )
    return user
