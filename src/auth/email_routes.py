"""
Email-related routes for verification and password reset.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.models import User
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
async def forgot_password(
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

    # Always return success to prevent email enumeration
    # But only send email if user actually exists
    if user:
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
                pass

        except Exception:
            # Log error but don't expose to user
            pass

    return {
        'success': True,
        'message': "If an account with that email exists, we've sent a password reset link.",
    }


@router.post('/reset-password')
async def reset_password(
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
async def verify_email(
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
        await email_service.send_welcome_email(user.email, user.name)
    except Exception:
        # Don't fail verification if welcome email fails
        pass

    return {'success': True, 'message': 'Email verified successfully'}


@router.post('/resend-verification')
async def resend_verification(
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

    # Always return success to prevent email enumeration
    if user and not user.is_verified:
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
                pass

        except Exception:
            # Log error but don't expose to user
            pass

    return {
        'success': True,
        'message': "If your account needs verification, we've sent a new verification email.",
    }
