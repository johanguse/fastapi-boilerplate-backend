from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.common.config import settings
from src.common.security import (
    _decode_hs256_token,
    get_current_user,
    get_current_active_user,
)
from src.common.session import get_async_session

oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl=f'{settings.API_V1_STR}/auth/jwt/login',
    auto_error=False,
)

# Re-export from security.py for convenience
current_active_user = get_current_active_user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_async_session),
) -> Optional[User]:
    """Return the authenticated user if a valid token is provided, else None.

    Unlike get_current_user, this does not raise 401 when no token is present.
    """
    if token is None:
        return None

    payload = _decode_hs256_token(token)
    if payload is None:
        return None

    sub = payload.get('sub')
    try:
        user_id = int(sub)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user
