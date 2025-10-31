"""Comprehensive tests for onboarding routes and functionality."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.organizations.models import Organization, OrganizationMember
from tests.helpers.auth_helpers import (
    create_test_user_with_password,
    get_auth_headers,
)


@pytest.mark.asyncio
async def test_get_onboarding_status_no_profile(
    client: AsyncClient, db_session: AsyncSession
):
    """Test getting onboarding status for user without profile."""
    user = await create_test_user_with_password(
        db_session,
        email='onboarding1@example.com',
        password='TestPassword123!',
        onboarding_completed=False,
        onboarding_step=0,
    )

    headers = await get_auth_headers(
        db_session, user=user, email='onboarding1@example.com'
    )

    response = await client.get(
        '/api/v1/onboarding/status',
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data['onboarding_completed'] is False
    assert data['onboarding_step'] == 0
    assert data['has_organization'] is False
    assert data['profile_complete'] is False
    assert data['next_step'] == 'profile'


@pytest.mark.asyncio
async def test_get_onboarding_status_with_profile(
    client: AsyncClient, db_session: AsyncSession
):
    """Test getting onboarding status for user with complete profile."""
    user = await create_test_user_with_password(
        db_session,
        email='onboarding2@example.com',
        password='TestPassword123!',
        name='Test User',
        onboarding_completed=False,
        onboarding_step=1,
    )

    # Set profile fields
    user.company = 'Test Company'
    user.country = 'US'
    await db_session.commit()

    headers = await get_auth_headers(
        db_session, user=user, email='onboarding2@example.com'
    )

    response = await client.get(
        '/api/v1/onboarding/status',
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data['profile_complete'] is True
    assert data['next_step'] == 'organization'


@pytest.mark.asyncio
async def test_update_onboarding_profile(
    client: AsyncClient, db_session: AsyncSession
):
    """Test updating user profile during onboarding."""
    user = await create_test_user_with_password(
        db_session,
        email='onboarding3@example.com',
        password='TestPassword123!',
        name=None,  # No name initially
        onboarding_step=0,
    )

    headers = await get_auth_headers(
        db_session, user=user, email='onboarding3@example.com'
    )

    response = await client.patch(
        '/api/v1/onboarding/profile',
        headers=headers,
        json={
            'name': 'New Name',
            'company': 'Test Company',
            'country': 'US',
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert data['user']['name'] == 'New Name'
    assert data['user']['company'] == 'Test Company'
    assert data['user']['country'] == 'US'
    assert data['user']['onboarding_step'] == 1

    # Verify in database
    await db_session.refresh(user)
    assert user.name == 'New Name'
    assert user.company == 'Test Company'
    assert user.country == 'US'
    assert user.onboarding_step == 1


@pytest.mark.asyncio
async def test_create_onboarding_organization(
    client: AsyncClient, db_session: AsyncSession
):
    """Test creating organization during onboarding."""
    user = await create_test_user_with_password(
        db_session,
        email='onboarding4@example.com',
        password='TestPassword123!',
        name='Test User',
        company='Test Company',
        country='US',
        onboarding_step=1,
    )

    headers = await get_auth_headers(
        db_session, user=user, email='onboarding4@example.com'
    )

    response = await client.post(
        '/api/v1/onboarding/organization',
        headers=headers,
        json={
            'name': 'My Organization',
            'slug': 'my-org',
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert data['organization']['name'] == 'My Organization'
    assert data['organization']['slug'] == 'my-org'
    assert data['onboarding_step'] == 2

    # Verify organization was created
    result = await db_session.execute(
        select(Organization).where(Organization.slug == 'my-org')
    )
    org = result.scalar_one_or_none()
    assert org is not None
    assert org.name == 'My Organization'

    # Verify user is member
    result = await db_session.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org.id,
            OrganizationMember.user_id == user.id,
        )
    )
    member = result.scalar_one_or_none()
    assert member is not None


@pytest.mark.asyncio
async def test_create_onboarding_organization_auto_name(
    client: AsyncClient, db_session: AsyncSession
):
    """Test creating organization with auto-generated name."""
    user = await create_test_user_with_password(
        db_session,
        email='onboarding5@example.com',
        password='TestPassword123!',
        name='John Doe',
        company='ACME Corp',
        country='US',
        onboarding_step=1,
    )

    headers = await get_auth_headers(
        db_session, user=user, email='onboarding5@example.com'
    )

    response = await client.post(
        '/api/v1/onboarding/organization',
        headers=headers,
        json={},  # Empty body, should use company name
    )

    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert data['organization']['name'] == "ACME Corp's Organization"


@pytest.mark.asyncio
async def test_update_onboarding_step(
    client: AsyncClient, db_session: AsyncSession
):
    """Test updating onboarding step."""
    user = await create_test_user_with_password(
        db_session,
        email='onboarding6@example.com',
        password='TestPassword123!',
        onboarding_step=1,
    )

    headers = await get_auth_headers(
        db_session, user=user, email='onboarding6@example.com'
    )

    response = await client.patch(
        '/api/v1/onboarding/step',
        headers=headers,
        json={
            'step': 2,
            'completed': False,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert data['onboarding_step'] == 2
    assert data['onboarding_completed'] is False

    # Verify in database
    await db_session.refresh(user)
    assert user.onboarding_step == 2
    assert user.onboarding_completed is False


@pytest.mark.asyncio
async def test_complete_onboarding(
    client: AsyncClient, db_session: AsyncSession
):
    """Test completing onboarding."""
    user = await create_test_user_with_password(
        db_session,
        email='onboarding7@example.com',
        password='TestPassword123!',
        onboarding_step=2,
        onboarding_completed=False,
    )

    headers = await get_auth_headers(
        db_session, user=user, email='onboarding7@example.com'
    )

    response = await client.post(
        '/api/v1/onboarding/complete',
        headers=headers,
        json={
            'skipped': False,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert data['onboarding_completed'] is True
    assert data['onboarding_step'] == 3

    # Verify in database
    await db_session.refresh(user)
    assert user.onboarding_completed is True
    assert user.onboarding_step == 3


@pytest.mark.asyncio
async def test_onboarding_status_with_organization(
    client: AsyncClient, db_session: AsyncSession
):
    """Test getting onboarding status when user has organization."""
    user = await create_test_user_with_password(
        db_session,
        email='onboarding8@example.com',
        password='TestPassword123!',
        name='Test User',
        company='Test Company',
        country='US',
        onboarding_step=2,
    )

    headers = await get_auth_headers(
        db_session, user=user, email='onboarding8@example.com'
    )

    # Create an organization for the user
    response = await client.post(
        '/api/v1/onboarding/organization',
        headers=headers,
        json={
            'name': 'My Org',
        },
    )
    assert response.status_code == 200

    # Get onboarding status
    response = await client.get(
        '/api/v1/onboarding/status',
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data['has_organization'] is True
    assert data['next_step'] == 'complete'


@pytest.mark.asyncio
async def test_onboarding_flow_complete(
    client: AsyncClient, db_session: AsyncSession
):
    """Test complete onboarding flow from start to finish."""
    # 1. Create user
    user = await create_test_user_with_password(
        db_session,
        email='onboarding9@example.com',
        password='TestPassword123!',
        onboarding_step=0,
    )

    headers = await get_auth_headers(
        db_session, user=user, email='onboarding9@example.com'
    )

    # 2. Check initial status
    response = await client.get('/api/v1/onboarding/status', headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data['onboarding_step'] == 0
    assert data['next_step'] == 'profile'

    # 3. Update profile
    response = await client.patch(
        '/api/v1/onboarding/profile',
        headers=headers,
        json={
            'name': 'Complete User',
            'company': 'Complete Company',
            'country': 'CA',
        },
    )
    assert response.status_code == 200
    assert response.json()['user']['onboarding_step'] == 1

    # 4. Create organization
    response = await client.post(
        '/api/v1/onboarding/organization',
        headers=headers,
        json={
            'name': 'Complete Organization',
        },
    )
    assert response.status_code == 200
    assert response.json()['onboarding_step'] == 2

    # 5. Complete onboarding
    response = await client.post(
        '/api/v1/onboarding/complete',
        headers=headers,
        json={'skipped': False},
    )
    assert response.status_code == 200
    assert response.json()['onboarding_completed'] is True

    # 6. Verify final status
    response = await client.get('/api/v1/onboarding/status', headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data['onboarding_completed'] is True
    assert data['onboarding_step'] == 3
    assert data['has_organization'] is True
    assert data['profile_complete'] is True

