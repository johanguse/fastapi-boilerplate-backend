"""Seed data for users."""

from datetime import UTC, datetime, timedelta

from passlib.context import CryptContext

from src.auth.models import User

from .constants import DEFAULT_PASSWORD

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def create_users():
    """Create diverse user seed data."""
    hashed_password = pwd_context.hash(DEFAULT_PASSWORD)

    users = [
        # Admin user - verified and active
        User(
            email='admin@example.com',
            name='Admin User',
            role='admin',
            status='active',
            is_active=True,
            is_superuser=True,
            is_verified=True,
            hashed_password=hashed_password,
            created_at=datetime.now(UTC) - timedelta(days=90),
        ),
        # Regular verified members
        User(
            email='john@example.com',
            name='John Doe',
            role='member',
            status='active',
            is_active=True,
            is_verified=True,
            hashed_password=hashed_password,
            created_at=datetime.now(UTC) - timedelta(days=60),
        ),
        User(
            email='jane@example.com',
            name='Jane Smith',
            role='member',
            status='active',
            is_active=True,
            is_verified=True,
            hashed_password=hashed_password,
            created_at=datetime.now(UTC) - timedelta(days=45),
        ),
        User(
            email='sarah@example.com',
            name='Sarah Johnson',
            role='member',
            status='active',
            is_active=True,
            is_verified=True,
            hashed_password=hashed_password,
            created_at=datetime.now(UTC) - timedelta(days=30),
        ),
        # Invited users (not verified yet)
        User(
            email='bob@example.com',
            name='Bob Wilson',
            role='member',
            status='invited',
            is_active=True,
            is_verified=False,
            hashed_password=hashed_password,
            created_at=datetime.now(UTC) - timedelta(days=2),
        ),
        User(
            email='alice@example.com',
            name='Alice Cooper',
            role='member',
            status='invited',
            is_active=True,
            is_verified=False,
            hashed_password=hashed_password,
            created_at=datetime.now(UTC) - timedelta(days=1),
        ),
        # Suspended user
        User(
            email='suspended@example.com',
            name='Suspended User',
            role='member',
            status='suspended',
            is_active=False,
            is_verified=True,
            hashed_password=hashed_password,
            created_at=datetime.now(UTC) - timedelta(days=120),
        ),
        # Recently joined active member
        User(
            email='mike@example.com',
            name='Mike Chen',
            role='member',
            status='active',
            is_active=True,
            is_verified=True,
            hashed_password=hashed_password,
            created_at=datetime.now(UTC) - timedelta(days=7),
        ),
        # Another admin
        User(
            email='emma@example.com',
            name='Emma Davis',
            role='admin',
            status='active',
            is_active=True,
            is_superuser=False,
            is_verified=True,
            hashed_password=hashed_password,
            created_at=datetime.now(UTC) - timedelta(days=75),
        ),
    ]

    return users
