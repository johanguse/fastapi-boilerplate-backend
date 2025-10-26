from datetime import UTC, datetime, timedelta
from typing import Any, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.common.config import settings
from src.common.session import get_async_session

try:
    # Optional dependency for JWKS
    from jwt import PyJWKClient  # type: ignore
except Exception:  # pragma: no cover
    PyJWKClient = None  # type: ignore

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f'{settings.API_V1_STR}/auth/jwt/login'
)
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

# JWT configuration
ALGORITHM = 'RS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_MINUTES = 10080

security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
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


def _decode_fastapi_users_token(token: str) -> Optional[dict[str, Any]]:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=['HS256'],
            audience='fastapi-users:auth',
        )
    except Exception:
        return None


def _decode_better_auth_token(token: str) -> Optional[dict[str, Any]]:
    if not settings.BETTER_AUTH_ENABLED:
        return None
    alg = (settings.BETTER_AUTH_ALGORITHM or 'RS256').upper()
    audience = settings.BETTER_AUTH_AUDIENCE
    issuer = settings.BETTER_AUTH_ISSUER
    try:
        if alg == 'RS256':
            if not PyJWKClient or not settings.BETTER_AUTH_JWKS_URL:
                return None
            jwks_client = PyJWKClient(settings.BETTER_AUTH_JWKS_URL)
            signing_key = jwks_client.get_signing_key_from_jwt(token).key
            return jwt.decode(
                token,
                signing_key,
                algorithms=['RS256'],
                audience=audience,
                issuer=issuer,
            )
        if alg == 'HS256' and settings.BETTER_AUTH_SHARED_SECRET:
            return jwt.decode(
                token,
                settings.BETTER_AUTH_SHARED_SECRET,
                algorithms=['HS256'],
                audience=audience,
                issuer=issuer,
            )
    except Exception:
        return None
    return None


def _resolve_email_from_payload(payload: dict[str, Any]) -> Optional[str]:
    if not payload:
        return None
    # Prefer explicit email claim if present; fall back to sub
    email_claim = payload.get(settings.BETTER_AUTH_EMAIL_CLAIM or 'email')
    sub_claim = payload.get('sub')
    if settings.BETTER_AUTH_ENABLED and settings.BETTER_AUTH_SUB_IS_EMAIL:
        return sub_claim or email_claim
    return email_claim or sub_claim


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_session),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    payload = _decode_fastapi_users_token(token)
    if payload is None:
        payload = _decode_better_auth_token(token)
    if payload is None:
        raise credentials_exception

    email = _resolve_email_from_payload(payload)
    if not email:
        raise credentials_exception

    result = await db.execute(select(User).filter(User.email == str(email)))  # type: ignore
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
