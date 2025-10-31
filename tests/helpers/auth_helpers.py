"""Helper functions for authentication tests."""

import hashlib
from datetime import datetime, timezone
from typing import Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User


async def create_test_user_with_password(
    session: AsyncSession,
    email: str = 'test@example.com',
    password: str = 'Password123!',
    name: str = 'Test User',
    is_active: bool = True,
    is_verified: bool = True,
    is_superuser: bool = False,
    role: str = 'member',
    *,
    # Profile fields
    phone: Optional[str] = None,
    company: Optional[str] = None,
    job_title: Optional[str] = None,
    country: Optional[str] = None,
    bio: Optional[str] = None,
    website: Optional[str] = None,
    # Onboarding fields
    onboarding_completed: bool = False,
    onboarding_step: int = 0,
) -> User:
    """Create a test user with a hashed password.
    
    If a user with the given email already exists, it will be deleted first.
    
    Args:
        session: Database session
        email: User email
        password: Plain text password
        name: User name
        is_active: Whether user is active
        is_verified: Whether user email is verified
        is_superuser: Whether user is superuser
        role: User role
        
    Returns:
        Created user
    """
    # Check if user already exists and delete it
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        await session.delete(existing_user)
        await session.commit()
    
    # Hash the password using the same method as the app
    # FastAPI Users uses passlib for password hashing
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    hashed_password = pwd_context.hash(password)
    
    # Create user
    user = User(
        email=email,
        hashed_password=hashed_password,
        name=name,
        is_active=is_active,
        is_verified=is_verified,
        is_superuser=is_superuser,
        role=role,
        max_teams=5,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        # Profile
        phone=phone,
        company=company,
        job_title=job_title,
        country=country,
        bio=bio,
        website=website,
        # Onboarding
        onboarding_completed=onboarding_completed,
        onboarding_step=onboarding_step,
    )
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    return user


async def get_auth_headers(
    session: AsyncSession,
    user: Optional[User] = None,
    email: str = 'test@example.com',
    password: str = 'Password123!',
) -> Dict[str, str]:
    """Generate authentication headers for API requests.
    
    Args:
        session: Database session
        user: Optional existing user
        email: User email
        password: User password
        
    Returns:
        Dictionary with Authorization header
    """
    if user is None:
        # Get or create user
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user is None:
            user = await create_test_user_with_password(
                session, email=email, password=password
            )
    
    # Generate a JWT token
    from src.auth.better_auth.jwt_utils import create_better_auth_jwt
    
    token = create_better_auth_jwt(user)
    
    return {'Authorization': f'Bearer {token}'}


async def get_auth_cookies(
    session: AsyncSession,
    user: Optional[User] = None,
    email: str = 'test@example.com',
    password: str = 'Password123!',
) -> Dict[str, str]:
    """Generate authentication cookies for API requests.
    
    Args:
        session: Database session
        user: Optional existing user
        email: User email
        password: User password
        
    Returns:
        Dictionary with auth cookie
    """
    if user is None:
        # Get or create user
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user is None:
            user = await create_test_user_with_password(
                session, email=email, password=password
            )
    
    # Generate a JWT token
    from src.auth.better_auth.jwt_utils import create_better_auth_jwt
    
    token = create_better_auth_jwt(user)
    
    return {'ba_session': token}


async def verify_user_password(
    session: AsyncSession,
    user: User,
    password: str,
) -> bool:
    """Verify a user's password.
    
    Args:
        session: Database session
        user: User to verify
        password: Plain text password
        
    Returns:
        True if password is correct
    """
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    
    return pwd_context.verify(password, user.hashed_password)


def create_mock_oauth_provider_data(
    provider: str,
    user_data: Optional[Dict] = None,
) -> Dict:
    """Create mock OAuth provider response data.
    
    Args:
        provider: OAuth provider name (google, github, microsoft, apple)
        user_data: Optional custom user data
        
    Returns:
        Mock OAuth provider data
    """
    default_data = {
        'email': f'{provider}_user@example.com',
        'name': f'{provider.capitalize()} User',
        'id': f'{provider}_12345',
    }
    
    provider_specific = {
        'google': {
            'email': 'google_user@gmail.com',
            'name': 'Google User',
            'given_name': 'Google',
            'family_name': 'User',
            'picture': 'https://example.com/avatar.jpg',
        },
        'github': {
            'login': 'github_user',
            'name': 'GitHub User',
            'avatar_url': 'https://example.com/avatar.jpg',
        },
        'microsoft': {
            'mail': 'user@outlook.com',
            'displayName': 'Microsoft User',
            'jobTitle': 'Developer',
        },
        'apple': {
            'email': 'user@icloud.com',
            'name': {'firstName': 'Apple', 'lastName': 'User'},
        },
    }
    
    base_data = provider_specific.get(provider, default_data)
    
    if user_data:
        base_data.update(user_data)
    
    return base_data

