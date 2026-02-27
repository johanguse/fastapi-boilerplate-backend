from datetime import UTC, datetime, timedelta
from typing import Any, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.common.config import settings
from src.common.session import get_async_session

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f'{settings.API_V1_STR}/auth/jwt/login'
)


def create_access_token(
    data: dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict[str, Any]) -> str:
    expires_delta = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    return create_access_token(data, expires_delta)


def _decode_hs256_token(token: str) -> Optional[dict[str, Any]]:
    """Decode an HS256 JWT signed with JWT_SECRET (or SECRET_KEY as fallback).

    Tries JWT_SECRET first (issued by better_auth_compat), then SECRET_KEY
    (FastAPI Users native tokens).  Both share the same audience claim.
    """
    for secret in filter(None, [settings.JWT_SECRET, settings.SECRET_KEY]):
        try:
            return jwt.decode(
                token,
                secret,
                algorithms=['HS256'],
                audience='fastapi-users:auth',
            )
        except jwt.InvalidTokenError:
            continue
    return None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_session),
):
    """Resolve the authenticated user by verifying the JWT and querying by numeric user ID.

    The JWT `sub` claim is always str(user.id) (a numeric DB primary key).
    We cast it to int and query WHERE users.id = ? — never by email.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    payload = _decode_hs256_token(token)
    if payload is None:
        raise credentials_exception

    sub = payload.get('sub')
    try:
        user_id = int(sub)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))  # type: ignore[arg-type]
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail='Inactive user')
    return current_user
