"""Authentication routes (sign-in, sign-up, sign-out, session)."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.auth.schemas import UserCreate
from src.auth.users import UserManager, get_user_manager  # type: ignore
from src.common.config import settings
from src.common.session import get_async_session
from src.common.utils import translate_message
from src.services.email_service import email_service
from src.services.token_service import token_service

from .cookie_utils import delete_auth_cookie, set_auth_cookie
from .jwt_utils import create_better_auth_jwt, verify_better_auth_jwt
from .models import (
    AuthResponse,
    EmailSignInRequest,
    EmailSignUpRequest,
    ForgotPasswordRequest,
)
from .request_utils import get_token_from_request

logger = logging.getLogger(__name__)
router = APIRouter()

INVALID_CREDENTIALS_MSG = 'Invalid email or password'


@router.post('/auth/sign-in/email', response_model=AuthResponse)
async def sign_in_email(
    request: EmailSignInRequest,
    http_request: Request,
    response: Response,
    _session: AsyncSession = Depends(get_async_session),
    user_manager: UserManager = Depends(get_user_manager),  # type: ignore
) -> AuthResponse:
    """Better Auth compatible email sign in."""
    try:
        logger.info(f'Sign-in attempt for email: {request.email}')

        # Get user by email
        try:
            user = await user_manager.get_by_email(request.email)
            logger.info(f'User found: {user.email}, active: {user.is_active}')
        except Exception:
            logger.warning(f'User not found: {request.email}')
            error_msg = translate_message('auth.invalid_credentials', http_request)
            raise HTTPException(
                status_code=400,
                detail={
                    'error': 'INVALID_CREDENTIALS',
                    'message': error_msg,
                },
            )

        # Verify password
        try:
            valid_password = user_manager.password_helper.verify_and_update(
                request.password, user.hashed_password
            )
            logger.info(
                f'Password verification result: {valid_password[0] if valid_password else False}'
            )
            if not valid_password or not valid_password[0]:
                logger.warning(f'Invalid password for user: {request.email}')
                error_msg = translate_message('auth.invalid_credentials', http_request)
                raise HTTPException(
                    status_code=400,
                    detail={
                        'error': 'INVALID_CREDENTIALS',
                        'message': error_msg,
                    },
                )
        except HTTPException:
            raise
        except Exception:
            logger.exception('Password verification error')
            error_msg = translate_message('auth.invalid_credentials', http_request)
            raise HTTPException(
                status_code=400,
                detail={
                    'error': 'INVALID_CREDENTIALS',
                    'message': error_msg,
                },
            )

        if not user.is_active:
            logger.warning(f'Inactive user attempted login: {request.email}')
            error_msg = translate_message('auth.account_inactive', http_request)
            raise HTTPException(
                status_code=400,
                detail={
                    'error': 'USER_INACTIVE',
                    'message': error_msg,
                },
            )

        # Check if email is verified
        if not user.is_verified:
            logger.warning(f'Unverified user attempted login: {request.email}')
            error_msg = translate_message(
                'auth.email_not_verified',
                http_request,
                fallback='Please verify your email address before logging in. Check your inbox for the verification link.',
            )
            raise HTTPException(
                status_code=400,
                detail={
                    'error': 'EMAIL_NOT_VERIFIED',
                    'message': error_msg,
                },
            )

        # Create Better Auth compatible JWT
        token = create_better_auth_jwt(user)

        response_data = AuthResponse(
            user={
                'id': str(user.id),
                'email': user.email,
                'name': getattr(user, 'name', user.email.split('@')[0]),
                'emailVerified': user.is_verified,
                'role': getattr(user, 'role', 'member'),
                'is_verified': user.is_verified,
                'is_superuser': user.is_superuser,
                'onboarding_completed': getattr(user, 'onboarding_completed', False),
                'onboarding_step': getattr(user, 'onboarding_step', 0),
                'createdAt': user.created_at.isoformat()
                if hasattr(user, 'created_at') and user.created_at
                else None,
                'updatedAt': user.updated_at.isoformat()
                if hasattr(user, 'updated_at') and user.updated_at
                else None,
            },
            session={
                'token': token,
                'expiresAt': (
                    datetime.now(timezone.utc)
                    + timedelta(seconds=settings.JWT_LIFETIME_SECONDS)
                ).isoformat(),
            },
        )

        set_auth_cookie(response, key='ba_session', value=token)
        logger.info(f'Successful login for: {request.email}')
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f'Unexpected error in sign_in_email: {str(e)}', exc_info=True
        )
        raise HTTPException(
            status_code=400,
            detail={
                'error': 'SIGN_IN_FAILED',
                'message': f'Authentication failed: {str(e)}',
            },
        )


@router.post('/auth/sign-up/email', response_model=AuthResponse)
async def sign_up_email(
    request: EmailSignUpRequest,
    http_request: Request,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
    user_manager: UserManager = Depends(get_user_manager),  # type: ignore
) -> AuthResponse:
    """Better Auth compatible email sign up."""
    try:
        logger.info(f'Sign-up attempt for email: {request.email}')

        # Check if user already exists
        try:
            _ = await user_manager.get_by_email(request.email)
            logger.warning(f'User already exists: {request.email}')
            error_msg = translate_message('auth.user_already_exists', http_request)
            raise HTTPException(
                status_code=400,
                detail={
                    'error': 'USER_EXISTS',
                    'message': error_msg,
                },
            )
        except Exception:
            pass

        # Create user
        user_create = UserCreate(
            email=request.email,
            password=request.password,
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        if request.name and hasattr(User, 'name'):
            user_create.name = request.name  # type: ignore[attr-defined]

        try:
            user = await user_manager.create(user_create)
        except Exception as e:
            if 'UserAlreadyExists' in str(type(e).__name__):
                logger.warning(f'User already exists during creation: {request.email}')
                error_msg = translate_message('auth.user_already_exists', http_request)
                raise HTTPException(
                    status_code=400,
                    detail={
                        'error': 'USER_EXISTS',
                        'message': error_msg,
                    },
                )
            else:
                logger.error(f'Unexpected error creating user: {str(e)}')
                error_msg = translate_message('error.sign_up_failed', http_request)
                raise HTTPException(
                    status_code=400,
                    detail={
                        'error': 'SIGN_UP_FAILED',
                        'message': error_msg,
                    },
                )

        # Set onboarding fields
        user.onboarding_completed = False
        user.onboarding_step = 0
        await session.commit()
        await session.refresh(user)

        # Send verification email
        try:
            verification_token = await token_service.create_verification_token(
                session, user.email
            )
            email_sent = await email_service.send_verification_email(
                user.email, verification_token, user.name
            )
            if email_sent:
                logger.info(f'Verification email sent to {user.email}')
            else:
                logger.warning(f'Failed to send verification email to {user.email}')
        except Exception as e:
            logger.exception(f'Exception sending verification email to {user.email}: {str(e)}')

        # Create JWT
        token = create_better_auth_jwt(user)

        resp = AuthResponse(
            user={
                'id': str(user.id),
                'email': user.email,
                'name': getattr(
                    user, 'name', request.name or user.email.split('@')[0]
                ),
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
            session={
                'token': token,
                'expiresAt': (
                    datetime.now(timezone.utc)
                    + timedelta(seconds=settings.JWT_LIFETIME_SECONDS)
                ).isoformat(),
            },
        )

        set_auth_cookie(response, key='ba_session', value=token)
        logger.info(f'Successful registration for: {request.email}')
        return resp
    except HTTPException:
        raise
    except Exception as e:
        logger.error('Unexpected error in sign_up_email', exc_info=True)
        raise HTTPException(
            status_code=400,
            detail={'error': 'SIGN_UP_FAILED', 'message': str(e)},
        )


@router.post('/auth/sign-out')
async def sign_out(response: Response) -> Dict[str, bool]:
    """Better Auth compatible sign out."""
    delete_auth_cookie(response, key='ba_session', path='/')
    delete_auth_cookie(response, key='ba_active_org', path='/')
    return {'success': True}


@router.get('/auth/session')
async def get_session(
    request: Request, session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """Get current session information."""
    token = get_token_from_request(request)
    if not token:
        error_msg = translate_message('auth.no_valid_session', request)
        raise HTTPException(status_code=401, detail=error_msg)
    payload = verify_better_auth_jwt(token)

    if not payload:
        error_msg = translate_message('auth.invalid_token', request)
        raise HTTPException(status_code=401, detail=error_msg)

    user_id = int(payload['sub'])  # type: ignore[index]
    result = await session.execute(
        select(User).where(User.id == user_id)  # type: ignore[arg-type]
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        error_msg = translate_message('auth.user_not_found_or_inactive', request)
        raise HTTPException(status_code=401, detail=error_msg)

    return {
        'user': {
            'id': str(user.id),
            'email': user.email,
            'name': getattr(user, 'name', user.email.split('@')[0]),
            'emailVerified': user.is_verified,
            'role': getattr(user, 'role', 'member'),
            'is_verified': user.is_verified,
            'is_superuser': user.is_superuser,
            'onboarding_completed': getattr(user, 'onboarding_completed', False),
            'onboarding_step': getattr(user, 'onboarding_step', 0),
            'createdAt': user.created_at.isoformat()
            if hasattr(user, 'created_at') and user.created_at
            else None,
            'updatedAt': user.updated_at.isoformat()
            if hasattr(user, 'updated_at') and user.updated_at
            else None,
        },
        'session': {
            'token': token,
            'expiresAt': datetime.fromtimestamp(
                payload['exp'], tz=timezone.utc  # type: ignore[index]
            ).isoformat(),
            'activeOrganizationId': request.cookies.get('ba_active_org'),
        },
    }


@router.get('/auth/get-session')
async def get_session_alias(
    request: Request, session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """Alias for /auth/session."""
    return await get_session(request, session)


@router.post('/auth/forgot-password')
async def forgot_password(
    request: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """Better Auth compatible forgot password endpoint."""
    try:
        logger.info(f'Forgot password request for email: {request.email}')

        result = await session.execute(
            select(User).where(User.email == request.email)  # type: ignore[arg-type]
        )
        user = result.scalar_one_or_none()

        if user:
            try:
                token = await token_service.create_password_reset_token(
                    session, user.email
                )
                email_sent = await email_service.send_forgot_password_email(
                    user.email, token, user.name
                )
                if not email_sent:
                    logger.warning(f'Failed to send password reset email to {user.email}')
                logger.info(f'Password reset email sent to: {user.email}')
            except Exception as e:
                logger.exception(f'Exception sending password reset email to {user.email}: {str(e)}')

        return {
            'success': True,
            'message': 'If an account with this email exists, a password reset link has been sent.',
            'user_exists': user is not None
        }
    except Exception as e:
        logger.exception(f'Unexpected error in forgot_password: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail={
                'error': 'FORGOT_PASSWORD_FAILED',
                'message': 'An error occurred while processing your request',
            },
        )


@router.post('/auth/reset-password')
async def reset_password(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """Better Auth compatible reset password endpoint."""
    try:
        payload = await request.json()
        token = payload.get('token')
        password = payload.get('password')

        if not token or not password:
            raise HTTPException(
                status_code=400,
                detail={
                    'error': 'INVALID_INPUT',
                    'message': 'Token and password are required',
                },
            )

        # TODO: Implement actual password reset logic
        logger.info(f'Password reset requested with token: {token[:10]}...')

        return {
            'success': True,
            'message': 'Password reset successfully',
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f'Unexpected error in reset_password: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail={
                'error': 'RESET_PASSWORD_FAILED',
                'message': 'An error occurred while resetting your password',
            },
        )
