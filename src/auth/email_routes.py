"""
Email-related routes for verification and password reset.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..auth.models import User
from ..common.rate_limiter import (
    EMAIL_LIMIT,
    PASSWORD_RESET_DAILY,
    PASSWORD_RESET_LIMIT,
    limiter,
)
from ..common.session import get_async_session
from ..services.email_service import email_service
from ..services.token_service import token_service

# Password hashing
pwd_context = CryptContext(schemes=['argon2'], deprecated='auto')

router = APIRouter(prefix='/auth', tags=['auth-email'])


class ForgotPasswordRequest(BaseModel):
    """Request model for forgot password."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Request model for password reset."""

    token: str
    new_password: str


class VerifyEmailRequest(BaseModel):
    """Request model for email verification."""

    token: str


@router.post('/forgot-password')
@limiter.limit(PASSWORD_RESET_LIMIT)  # 3 requests per hour
@limiter.limit(PASSWORD_RESET_DAILY)  # 10 requests per day
async def forgot_password(
    http_request: Request,  # Required for rate limiter
    request: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Send password reset email to user.
    """
    # Check if user exists
    result = await session.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalars().first()

    if user:
        # User exists - send password reset email
        try:
            # Generate password reset token
            token = await token_service.create_password_reset_token(
                session, user.email
            )

            # Send password reset email
            email_sent = await email_service.send_forgot_password_email(
                user.email, token, user.name
            )

            if not email_sent:
                # Log error but don't expose to user
                logger.warning(f'Failed to send password reset email to {user.email} - email_sent returned False')

            return {
                'success': True,
                'message': 'Password reset link sent to your email address.',
                'user_exists': True
            }

        except Exception as e:
            # Log error but don't expose to user
            logger.exception(f'Exception in forgot_password for {request.email}: {str(e)}')
            return {
                'success': False,
                'message': 'Unable to send password reset email. Please try again later.',
                'user_exists': True
            }
    else:
        # User doesn't exist
        return {
            'success': False,
            'message': 'No account found with this email address. Would you like to create an account?',
            'user_exists': False
        }


@router.post('/reset-password')
@limiter.limit(PASSWORD_RESET_LIMIT)  # 3 requests per hour
async def reset_password(
    http_request: Request,  # Required for rate limiter
    request: ResetPasswordRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Reset user password with token.
    """
    # Verify token and get email
    email = await token_service.verify_token(
        session, request.token, 'password_reset'
    )

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid or expired reset token',
        )

    # Find user
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='User not found'
        )

    # Update password
    hashed_password = pwd_context.hash(request.new_password)
    user.hashed_password = hashed_password

    await session.commit()

    return {'success': True, 'message': 'Password reset successfully'}


@router.post('/verify-email')
@limiter.limit(EMAIL_LIMIT)  # 10 requests per hour
async def verify_email(
    http_request: Request,  # Required for rate limiter
    request: VerifyEmailRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Verify user email with token.
    """
    # Verify token and get email
    email = await token_service.verify_token(
        session, request.token, 'verification'
    )

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid or expired verification token',
        )

    # Find user
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='User not found'
        )

    # Mark email as verified
    user.is_verified = True
    await session.commit()

    # Send welcome email
    try:
        welcome_sent = await email_service.send_welcome_email(user.email, user.name)
        if not welcome_sent:
            logger.warning(f'Failed to send welcome email to {user.email} - email_sent returned False')
    except Exception as e:
        # Don't fail verification if welcome email fails
        logger.exception(f'Exception sending welcome email to {user.email}: {str(e)}')

    return {'success': True, 'message': 'Email verified successfully'}


@router.post('/resend-verification')
@limiter.limit(EMAIL_LIMIT)  # 10 requests per hour
async def resend_verification(
    http_request: Request,  # Required for rate limiter
    request: ForgotPasswordRequest,  # Reuse same model (just email)
    session: AsyncSession = Depends(get_async_session),
):
    """
    Resend email verification.
    """
    # Check if user exists and is not verified
    result = await session.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalars().first()

    if not user:
        # User doesn't exist
        return {
            'success': False,
            'message': 'No account found with this email address. Please sign up first.',
            'user_exists': False
        }
    elif user.is_verified:
        # User already verified
        return {
            'success': False,
            'message': 'This email address is already verified.',
            'user_exists': True,
            'already_verified': True
        }
    else:
        # User exists but not verified - send verification email
        try:
            # Generate verification token
            token = await token_service.create_verification_token(
                session, user.email
            )

            # Send verification email
            email_sent = await email_service.send_verification_email(
                user.email, token, user.name
            )

            if not email_sent:
                # Log error but don't expose to user
                logger.warning(f'Failed to send verification email to {user.email} - email_sent returned False')

            return {
                'success': True,
                'message': 'Verification email sent to your email address.',
                'user_exists': True
            }

        except Exception as e:
            # Log error but don't expose to user
            logger.exception(f'Exception in resend_verification for {request.email}: {str(e)}')
            return {
                'success': False,
                'message': 'Unable to send verification email. Please try again later.',
                'user_exists': True
            }
