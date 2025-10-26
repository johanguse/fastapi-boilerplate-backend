"""
OTP-based authentication routes for registration and login.
Provides passwordless authentication using email-based OTP codes.
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.auth.schemas import OTPResponse, OTPSendRequest, OTPVerifyRequest
from src.auth.users import UserManager, get_user_manager
from src.common.config import settings
from src.common.session import get_async_session
from src.services.email_service import email_service
from src.services.token_service import token_service

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()


def create_better_auth_jwt(user: User) -> str:
    """Create a JWT token in Better Auth format but compatible with FastAPI Users"""
    import jwt
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


def _cookie_options() -> Dict[str, Any]:
    """Derive cookie security options from FRONTEND_URL."""
    from urllib.parse import urlparse
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


def _set_cookie(
    response: Response, key: str, value: str, path: str = '/'
) -> None:
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


@router.post('/auth/otp/send', response_model=OTPResponse)
async def send_otp(
    request: OTPSendRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """Send OTP code to email for registration or login."""
    try:
        logger.info(f'OTP send request for email: {request.email}')

        # Check if user exists
        result = await session.execute(
            select(User).where(User.email == request.email)
        )
        user = result.scalar_one_or_none()
        user_exists = user is not None

        # Generate 6-digit OTP code
        otp_code = f"{secrets.randbelow(1000000):06d}"

        # Store OTP token in database
        try:
            await token_service.create_otp_token(
                session, request.email, otp_code
            )
        except Exception as e:
            logger.error(f'Failed to create OTP token: {str(e)}')
            raise HTTPException(
                status_code=500,
                detail={
                    'error': 'OTP_TOKEN_FAILED',
                    'message': 'Failed to generate verification code',
                },
            )

        # Send OTP email
        try:
            email_sent = await email_service.send_otp_email(
                request.email, otp_code, user.name if user else None
            )

            if not email_sent:
                logger.warning(f'Failed to send OTP email to {request.email}')
                raise HTTPException(
                    status_code=500,
                    detail={
                        'error': 'EMAIL_SEND_FAILED',
                        'message': 'Failed to send verification code. Please try again.',
                    },
                )

            logger.info(f'OTP email sent to {request.email}')

        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f'Exception sending OTP email to {request.email}: {str(e)}')
            raise HTTPException(
                status_code=500,
                detail={
                    'error': 'EMAIL_SEND_FAILED',
                    'message': 'Failed to send verification code. Please try again.',
                },
            )

        return OTPResponse(
            success=True,
            message='Verification code sent to your email address',
            user_exists=user_exists
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f'Unexpected error in send_otp: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail={
                'error': 'OTP_SEND_FAILED',
                'message': 'An error occurred while sending the verification code',
            },
        )


@router.post('/auth/otp/verify')
async def verify_otp(
    request: OTPVerifyRequest,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
    user_manager: UserManager = Depends(get_user_manager),
):
    """Verify OTP code and complete registration or login."""
    try:
        logger.info(f'OTP verify request for email: {request.email}')

        # Verify OTP token
        email = await token_service.verify_otp_token(
            session, request.email, request.code
        )

        if not email:
            logger.warning(f'Invalid or expired OTP for {request.email}')
            raise HTTPException(
                status_code=400,
                detail={
                    'error': 'INVALID_OTP',
                    'message': 'Invalid or expired verification code',
                },
            )

        # Check if user exists
        result = await session.execute(
            select(User).where(User.email == request.email)
        )
        user = result.scalar_one_or_none()

        if user:
            # Existing user - login
            logger.info(f'OTP login for existing user: {request.email}')

            # Update user info if name provided
            if request.name and not user.name:
                user.name = request.name
                await session.commit()
                await session.refresh(user)

        else:
            # New user - create account
            logger.info(f'OTP registration for new user: {request.email}')

            from src.auth.schemas import UserCreate

            user_create = UserCreate(
                email=request.email,
                password=secrets.token_urlsafe(32),  # Random password for OTP users
                name=request.name,
                is_active=True,
                is_superuser=False,
                is_verified=True,  # OTP verification counts as email verification
            )

            try:
                user = await user_manager.create(user_create)

                # Set onboarding fields for new users
                user.onboarding_completed = False
                user.onboarding_step = 0
                await session.commit()
                await session.refresh(user)

                logger.info(f'Created new user via OTP: {request.email}')

            except Exception as e:
                logger.error(f'Failed to create user via OTP: {str(e)}')
                raise HTTPException(
                    status_code=500,
                    detail={
                        'error': 'USER_CREATION_FAILED',
                        'message': 'Failed to create account. Please try again.',
                    },
                )

        # Create JWT token
        token = create_better_auth_jwt(user)

        # Set session cookie
        _set_cookie(response, key='ba_session', value=token)

        # Return auth response
        auth_response = {
            'user': {
                'id': str(user.id),
                'email': user.email,
                'name': getattr(user, 'name', request.name or user.email.split('@')[0]),
                'emailVerified': user.is_verified,
                'role': getattr(user, 'role', 'member'),
                'is_verified': user.is_verified,
                'is_superuser': user.is_superuser,
                'onboarding_completed': user.onboarding_completed,
                'onboarding_step': user.onboarding_step,
                'createdAt': user.created_at.isoformat()
                if hasattr(user, 'created_at') and user.created_at
                else None,
                'updatedAt': user.updated_at.isoformat()
                if hasattr(user, 'updated_at') and user.updated_at
                else None,
            },
            'session': {
                'token': token,
                'expiresAt': (
                    datetime.now(timezone.utc)
                    + timedelta(seconds=settings.JWT_LIFETIME_SECONDS)
                ).isoformat(),
            },
        }

        logger.info(f'Successful OTP verification for: {request.email}')
        return auth_response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f'Unexpected error in verify_otp: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail={
                'error': 'OTP_VERIFY_FAILED',
                'message': 'An error occurred while verifying the code',
            },
        )
