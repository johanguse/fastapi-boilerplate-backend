"""
Email-related routes for verification and password reset.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from loguru import logger
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.models import EmailToken, User
from ..common.rate_limiter import (
    EMAIL_LIMIT,
    PASSWORD_RESET_DAILY,
    PASSWORD_RESET_LIMIT,
    limiter,
)
from ..common.session import get_async_session
from ..common.utils import translate_message
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
        error_msg = translate_message('auth.invalid_or_expired_reset_token', http_request)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    # Find user
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if not user:
        error_msg = translate_message('auth.user_not_found', http_request)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=error_msg
        )

    # Update password
    hashed_password = pwd_context.hash(request.new_password)
    user.hashed_password = hashed_password

    await session.commit()

    return {'success': True, 'message': 'Password reset successfully'}


@router.post('/verify-email')
@limiter.limit(EMAIL_LIMIT)  # 10 requests per hour
async def verify_email(
    request: Request,  # Required for rate limiter
    response: Response,  # Required for rate limiter to inject headers
    data: VerifyEmailRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Verify user email with token.
    """
    # Look up the token WITHOUT deleting it first
    from datetime import datetime, timezone
    
    if not data.token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'error': 'MISSING_TOKEN',
                'message': 'Verification token is required',
            },
        )
    
    logger.info(f'Verifying email with token (hash: {token_service.hash_token(data.token)[:16]}...)')
    
    token_hash = token_service.hash_token(data.token)
    token_result = await session.execute(
        select(EmailToken).where(
            EmailToken.token_hash == token_hash,
            EmailToken.token_type == 'verification',
        )
    )
    email_token_record = token_result.scalars().first()
    
    if email_token_record:
        logger.info(f'Token found for email: {email_token_record.user_email}')
    else:
        logger.warning(f'Token not found in database - may have been used or invalid')
    
    if not email_token_record:
        # Token doesn't exist - it might have been used already or invalid
        # Since we can't determine which user this was for without the token,
        # we return a clear error message
        error_msg = translate_message(
            'auth.invalid_or_expired_verification_token', 
            request
        ) or 'Invalid or expired verification token. If you\'ve already verified your email, you can proceed to login.'
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'error': 'INVALID_TOKEN',
                'message': error_msg,
            },
        )
    
    # Check if token is expired
    if email_token_record.expires_at <= datetime.now(timezone.utc):
        # Token expired, delete it
        await session.delete(email_token_record)
        await session.commit()
        error_msg = translate_message(
            'auth.invalid_or_expired_verification_token', 
            request
        ) or 'This verification link has expired. Please request a new one.'
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'error': 'EXPIRED_TOKEN',
                'message': error_msg,
            },
        )
    
    # Token is valid - get the email
    user_email = email_token_record.user_email
    
    # Find user
    user_result = await session.execute(
        select(User).where(User.email == user_email)
    )
    user = user_result.scalars().first()

    if not user:
        # Delete the orphaned token
        await session.delete(email_token_record)
        await session.commit()
        error_msg = translate_message('auth.user_not_found', request)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=error_msg
        )

    # Check if already verified
    if user.is_verified:
        # Already verified - delete the token and return success
        # This allows users to click the verification link multiple times without error
        await session.delete(email_token_record)
        await session.commit()
        logger.info(f'Email already verified for user {user.email}')
        return {
            'success': True,
            'message': 'Email already verified',
            'already_verified': True
        }

    # Mark email as verified and delete the token
    user.is_verified = True
    await session.delete(email_token_record)
    await session.commit()

    # Don't send welcome email here - it will be sent after onboarding completion
    # Welcome email should only be sent after user completes onboarding

    return {'success': True, 'message': 'Email verified successfully'}


@router.post('/resend-verification')
@limiter.limit(EMAIL_LIMIT)  # 10 requests per hour
async def resend_verification(
    request: Request,  # Required for rate limiter
    response: Response,  # Required for rate limiter to inject headers
    data: ForgotPasswordRequest,  # Reuse same model (just email)
    session: AsyncSession = Depends(get_async_session),
):
    """
    Resend email verification.
    """
    # Check if user exists and is not verified
    result = await session.execute(
        select(User).where(User.email == data.email)
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
            logger.exception(f'Exception in resend_verification for {data.email}: {str(e)}')
            return {
                'success': False,
                'message': 'Unable to send verification email. Please try again later.',
                'user_exists': True
            }
