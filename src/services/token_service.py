"""
Token management for email verification and password reset.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.models import EmailToken


class TokenService:
    """Service for managing email verification and password reset tokens."""

    @staticmethod
    def generate_token() -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a token for secure storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    async def create_verification_token(
        self, session: AsyncSession, email: str
    ) -> str:
        """
        Create an email verification token.

        Args:
            session: Database session
            email: User's email address

        Returns:
            str: Plain text token (to be sent in email)
        """
        # Delete any existing verification tokens for this email
        await session.execute(
            delete(EmailToken).where(
                EmailToken.user_email == email,
                EmailToken.token_type == 'verification',
            )
        )

        # Generate new token
        token = self.generate_token()
        token_hash = self.hash_token(token)

        # Create token record
        email_token = EmailToken(
            id=secrets.token_urlsafe(16),
            user_email=email,
            token_type='verification',
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc)
            + timedelta(hours=24),  # 24 hour expiry
        )

        session.add(email_token)
        await session.commit()

        return token

    async def create_password_reset_token(
        self, session: AsyncSession, email: str
    ) -> str:
        """
        Create a password reset token.

        Args:
            session: Database session
            email: User's email address

        Returns:
            str: Plain text token (to be sent in email)
        """
        # Delete any existing password reset tokens for this email
        await session.execute(
            delete(EmailToken).where(
                EmailToken.user_email == email,
                EmailToken.token_type == 'password_reset',
            )
        )

        # Generate new token
        token = self.generate_token()
        token_hash = self.hash_token(token)

        # Create token record
        email_token = EmailToken(
            id=secrets.token_urlsafe(16),
            user_email=email,
            token_type='password_reset',
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc)
            + timedelta(hours=1),  # 1 hour expiry
        )

        session.add(email_token)
        await session.commit()

        return token

    async def create_otp_token(
        self, session: AsyncSession, email: str, otp_code: str
    ) -> str:
        """
        Create an OTP token for email verification.

        Args:
            session: Database session
            email: User's email address
            otp_code: 6-digit OTP code

        Returns:
            str: Plain text OTP code (to be sent in email)
        """
        # Delete any existing OTP tokens for this email
        await session.execute(
            delete(EmailToken).where(
                EmailToken.user_email == email,
                EmailToken.token_type == 'otp',
            )
        )

        # Hash the OTP code for storage
        token_hash = self.hash_token(otp_code)

        # Create token record
        email_token = EmailToken(
            id=secrets.token_urlsafe(16),
            user_email=email,
            token_type='otp',
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=15),  # 15 minute expiry
        )

        session.add(email_token)
        await session.commit()

        return otp_code

    async def verify_otp_token(
        self, session: AsyncSession, email: str, otp_code: str
    ) -> Optional[str]:
        """
        Verify an OTP token and return the associated email if valid.

        Args:
            session: Database session
            email: User's email address
            otp_code: 6-digit OTP code to verify

        Returns:
            Optional[str]: Email address if OTP is valid, None otherwise
        """
        token_hash = self.hash_token(otp_code)

        # Find matching OTP token
        result = await session.execute(
            select(EmailToken).where(
                EmailToken.user_email == email,
                EmailToken.token_hash == token_hash,
                EmailToken.token_type == 'otp',
                EmailToken.expires_at > datetime.now(timezone.utc),
            )
        )

        email_token = result.scalars().first()

        if email_token:
            # OTP is valid, delete it (one-time use)
            await session.delete(email_token)
            await session.commit()
            return email_token.user_email

        return None

    async def verify_token(
        self, session: AsyncSession, token: str, token_type: str
    ) -> Optional[str]:
        """
        Verify a token and return the associated email if valid.

        Args:
            session: Database session
            token: Plain text token to verify
            token_type: Type of token ('verification' or 'password_reset')

        Returns:
            Optional[str]: Email address if token is valid, None otherwise
        """
        token_hash = self.hash_token(token)

        # Find matching token
        result = await session.execute(
            select(EmailToken).where(
                EmailToken.token_hash == token_hash,
                EmailToken.token_type == token_type,
                EmailToken.expires_at > datetime.now(timezone.utc),
            )
        )

        email_token = result.scalars().first()

        if email_token:
            # Token is valid, delete it (one-time use)
            await session.delete(email_token)
            await session.commit()
            return email_token.user_email

        return None

    @staticmethod
    async def cleanup_expired_tokens(session: AsyncSession) -> int:
        """
        Clean up expired tokens from the database.

        Args:
            session: Database session

        Returns:
            int: Number of tokens deleted
        """
        result = await session.execute(
            delete(EmailToken).where(
                EmailToken.expires_at <= datetime.now(timezone.utc)
            )
        )

        deleted_count = result.rowcount
        await session.commit()

        return deleted_count


# Global instance
token_service = TokenService()
