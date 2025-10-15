"""Database models for team invitations and email verification."""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.database import Base


def generate_token():
    """Generate a secure random token."""
    return secrets.token_urlsafe(32)


class EmailVerificationToken(Base):
    """Email verification tokens for new user registration."""

    __tablename__ = 'email_verification_tokens'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), index=True
    )
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships
    from src.auth.models import User

    user: Mapped['User'] = relationship('User', foreign_keys=[user_id])

    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now(UTC) > self.expires_at

    def is_used(self) -> bool:
        """Check if token has been used."""
        return self.used_at is not None

    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not used)."""
        return not self.is_expired() and not self.used_at

    def __repr__(self) -> str:
        return f'<EmailVerificationToken {self.email}>'


class PasswordResetToken(Base):
    """Password reset tokens for forgot password flow."""

    __tablename__ = 'password_reset_tokens'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), index=True
    )
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships
    from src.auth.models import User

    user: Mapped['User'] = relationship('User', foreign_keys=[user_id])

    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now(UTC) > self.expires_at

    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not used)."""
        return not self.is_expired() and not self.used_at

    def __repr__(self) -> str:
        return f'<PasswordResetToken {self.email}>'


class TeamInvitation(Base):
    """Team/Organization invitations."""

    __tablename__ = 'team_invitations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('organizations.id', ondelete='CASCADE'), index=True
    )
    invited_by_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id', ondelete='CASCADE')
    )
    email: Mapped[str] = mapped_column(String(255), index=True)
    role: Mapped[str] = mapped_column(String(50), default='member')
    token: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, default=generate_token
    )
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20), default='pending', index=True
    )  # pending, accepted, declined, expired

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC) + timedelta(days=7),
    )
    accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    accepted_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    from src.auth.models import User
    from src.organizations.models import Organization

    organization: Mapped['Organization'] = relationship('Organization')
    invited_by: Mapped['User'] = relationship(
        'User', foreign_keys=[invited_by_id]
    )
    accepted_by: Mapped[Optional['User']] = relationship(
        'User', foreign_keys=[accepted_by_id]
    )

    def is_expired(self) -> bool:
        """Check if invitation is expired."""
        return datetime.now(UTC) > self.expires_at

    def is_pending(self) -> bool:
        """Check if invitation is still pending."""
        return self.status == 'pending' and not self.is_expired()

    def __repr__(self) -> str:
        return f'<TeamInvitation {self.email} to org {self.organization_id}>'
