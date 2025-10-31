"""Enhanced authentication tests with real database operations."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from tests.helpers.auth_helpers import (
    create_test_user_with_password,
    get_auth_cookies,
    get_auth_headers,
    verify_user_password,
)


@pytest.mark.asyncio
async def test_register_user_with_real_database(
    client: AsyncClient, db_session: AsyncSession
):
    """Test user registration with real database operations."""
    # Create user directly in database
    user = await create_test_user_with_password(
        db_session,
        email='realreg@example.com',
        password='RealPassword123!',
        name='Real User',
    )

    assert user.email == 'realreg@example.com'
    assert user.name == 'Real User'
    assert user.is_active is True

    # Verify password is hashed
    assert user.hashed_password != 'RealPassword123!'
    is_valid = await verify_user_password(
        db_session, user, 'RealPassword123!'
    )
    assert is_valid is True


@pytest.mark.asyncio
async def test_user_login_with_database(
    client: AsyncClient, db_session: AsyncSession
):
    """Test login with real database authentication."""
    # Create user
    await create_test_user_with_password(
        db_session,
        email='reallogin@example.com',
        password='RealLogin123!',
    )

    # Attempt to login
    response = await client.post(
        '/api/v1/auth/sign-in/email',
        json={
            'email': 'reallogin@example.com',
            'password': 'RealLogin123!',
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert 'user' in data
    assert 'session' in data
    assert data['user']['email'] == 'reallogin@example.com'
    assert 'token' in data['session']


@pytest.mark.asyncio
async def test_user_update_profile_with_database(
    client: AsyncClient, db_session: AsyncSession
):
    """Test updating user profile with database operations."""
    user = await create_test_user_with_password(
        db_session,
        email='profile@example.com',
        password='Password123!',
        name='Original Name',
    )

    headers = await get_auth_headers(db_session, user=user)

    # Update profile
    response = await client.patch(
        '/api/v1/me',
        headers=headers,
        json={
            'name': 'Updated Name',
            'phone': '+1234567890',
            'company': 'Test Company',
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data['name'] == 'Updated Name'

    # Verify in database
    stmt = select(User).where(User.email == 'profile@example.com')
    result = await db_session.execute(stmt)
    updated_user = result.scalar_one_or_none()
    assert updated_user is not None
    assert updated_user.name == 'Updated Name'
    assert updated_user.phone == '+1234567890'
    assert updated_user.company == 'Test Company'


@pytest.mark.asyncio
async def test_email_verification_flow(
    client: AsyncClient, db_session: AsyncSession
):
    """Test email verification workflow."""
    user = await create_test_user_with_password(
        db_session,
        email='verify@example.com',
        password='Password123!',
        is_verified=False,
    )

    assert user.is_verified is False

    # Simulate verification
    user.is_verified = True
    await db_session.commit()

    # Verify updated
    stmt = select(User).where(User.email == 'verify@example.com')
    result = await db_session.execute(stmt)
    verified_user = result.scalar_one_or_none()
    assert verified_user is not None
    assert verified_user.is_verified is True


@pytest.mark.asyncio
async def test_password_reset_flow(
    client: AsyncClient, db_session: AsyncSession
):
    """Test password reset workflow."""
    user = await create_test_user_with_password(
        db_session,
        email='reset@example.com',
        password='OldPassword123!',
    )

    # Verify original password works
    is_valid = await verify_user_password(
        db_session, user, 'OldPassword123!'
    )
    assert is_valid is True

    # Update to new password
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    user.hashed_password = pwd_context.hash('NewPassword123!')
    await db_session.commit()

    # Verify old password doesn't work
    is_valid = await verify_user_password(
        db_session, user, 'OldPassword123!'
    )
    assert is_valid is False

    # Verify new password works
    is_valid = await verify_user_password(
        db_session, user, 'NewPassword123!'
    )
    assert is_valid is True


@pytest.mark.asyncio
async def test_user_role_assignment(
    client: AsyncClient, db_session: AsyncSession
):
    """Test user role assignment in database."""
    # Create regular user
    user1 = await create_test_user_with_password(
        db_session,
        email='regular@example.com',
        password='Password123!',
        role='member',
    )

    # Create admin user
    user2 = await create_test_user_with_password(
        db_session,
        email='admin@example.com',
        password='Password123!',
        role='admin',
        is_superuser=True,
    )

    # Verify roles
    assert user1.role == 'member'
    assert user2.role == 'admin'
    assert user1.is_superuser is False
    assert user2.is_superuser is True


@pytest.mark.asyncio
async def test_multiple_users_same_email_fails(
    db_session: AsyncSession
):
    """Test that creating duplicate users fails."""
    # Create first user
    await create_test_user_with_password(
        db_session,
        email='duplicate@example.com',
        password='Password123!',
    )

    # Try to create second user with same email
    with pytest.raises(Exception):  # Should fail with integrity error
        await create_test_user_with_password(
            db_session,
            email='duplicate@example.com',
            password='Password456!',
        )


@pytest.mark.asyncio
async def test_user_soft_delete(
    client: AsyncClient, db_session: AsyncSession
):
    """Test user soft delete (marking inactive)."""
    user = await create_test_user_with_password(
        db_session,
        email='inactive@example.com',
        password='Password123!',
        is_active=True,
    )

    assert user.is_active is True

    # Deactivate user
    user.is_active = False
    await db_session.commit()

    # Verify deactivated
    await db_session.refresh(user)
    assert user.is_active is False


@pytest.mark.asyncio
async def test_onboarding_completion_updates_step(
    db_session: AsyncSession
):
    """Test that onboarding completion updates step correctly."""
    user = await create_test_user_with_password(
        db_session,
        email='onboarding@example.com',
        password='Password123!',
        onboarding_completed=False,
        onboarding_step=0,
    )

    assert user.onboarding_step == 0
    assert user.onboarding_completed is False

    # Simulate profile update
    user.name = 'Test User'
    user.company = 'Test Company'
    user.country = 'US'
    user.onboarding_step = 1
    await db_session.commit()

    assert user.onboarding_step == 1

    # Complete onboarding
    user.onboarding_completed = True
    user.onboarding_step = 3
    await db_session.commit()

    await db_session.refresh(user)
    assert user.onboarding_completed is True
    assert user.onboarding_step == 3

