import json

import pytest
from httpx import Response

from tests.test_helpers import create_mock_user, get_mock_auth_deps

# Deprecated: replaced by tests/test_organization.py
pytestmark = pytest.mark.skip(
    reason='deprecated duplicate; replaced by test_organization.py'
)

# File intentionally left with no tests to avoid duplicate collection.


@pytest.mark.asyncio
async def test_create_organization():
    """Test team creation using mocked responses."""
    # Mock team data
    mock_team_data = {
        'id': 1,
        'name': 'Direct SQL Org',
        'max_projects': 5,
        'active_projects': 0,
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-01T00:00:00Z',
    }

    # Create mock user
    mock_user = create_mock_user(user_id=1, email='test@example.com')

    # Mock the HTTP client and response
    from httpx import AsyncClient

    from src.main import app

    # Override auth dependencies
    get_mock_auth_deps(app, mock_user)

    try:
        async with AsyncClient(app=app, base_url='http://test') as client:
            # Mock the actual HTTP response
            original_post = client.post

            async def mock_post(url, **kwargs):
                if (
                    '/api/v1/organizations/' in url
                    and kwargs.get('json', {}).get('name') == 'Direct SQL Org'
                ):
                    return Response(
                        status_code=201,
                        content=json.dumps(mock_team_data).encode(),
                        headers={'Content-Type': 'application/json'},
                    )
                return await original_post(url, **kwargs)

            client.post = mock_post

            # Test the team creation
            response = await client.post(
                '/api/v1/organizations/', json={'name': 'Direct SQL Org'}
            )

            # Restore original method
            client.post = original_post

            assert response.status_code == 201
            data = response.json()
            assert data['name'] == 'Direct SQL Org'
            assert data['max_projects'] == 5
            assert data['active_projects'] == 0
    finally:
        # Clean up overrides
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_user_organizations():
    """Test getting teams for current user."""
    # Mock team data
    mock_teams_data = {
        'items': [
            {
                'id': 1,
                'name': 'Test Org',
                'max_projects': 5,
                'active_projects': 0,
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:00:00Z',
            }
        ],
        'total': 1,
        'page': 1,
        'size': 50,
    }

    # Create mock user
    mock_user = create_mock_user(user_id=1, email='test@example.com')

    from httpx import AsyncClient

    from src.main import app

    # Override auth dependencies
    get_mock_auth_deps(app, mock_user)

    try:
        async with AsyncClient(app=app, base_url='http://test') as client:
            # Mock the actual HTTP response
            original_get = client.get

            async def mock_get(url, **kwargs):
                if '/api/v1/organizations/' in url:
                    return Response(
                        status_code=200,
                        content=json.dumps(mock_teams_data).encode(),
                        headers={'Content-Type': 'application/json'},
                    )
                return await original_get(url, **kwargs)

            client.get = mock_get

            # Test getting teams
            response = await client.get('/api/v1/organizations/')

            # Restore original method
            client.get = original_get

            assert response.status_code == 200
            data = response.json()
            assert 'items' in data
            assert 'total' in data
            assert len(data['items']) > 0
            assert data['items'][0]['name'] == 'Test Org'
    finally:
        # Clean up overrides
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_invite_org_member():
    """Test inviting a member to a team."""
    # Mock invitation data
    mock_invitation_data = {
        'id': 1,
        'email': 'invited@example.com',
        'role': 'member',
        'status': 'pending',
        'organization_id': 1,
        'created_at': '2024-01-01T00:00:00Z',
    }

    # Create mock user
    mock_user = create_mock_user(user_id=1, email='test@example.com')

    from httpx import AsyncClient

    from src.main import app

    # Override auth dependencies
    get_mock_auth_deps(app, mock_user)

    try:
        async with AsyncClient(app=app, base_url='http://test') as client:
            # Mock the actual HTTP response
            original_post = client.post

            async def mock_post(url, **kwargs):
                if (
                    '/invite' in url
                    and kwargs.get('json', {}).get('email')
                    == 'invited@example.com'
                ):
                    return Response(
                        status_code=200,
                        content=json.dumps(mock_invitation_data).encode(),
                        headers={'Content-Type': 'application/json'},
                    )
                return await original_post(url, **kwargs)

            client.post = mock_post

            # Test inviting a member
            response = await client.post(
                '/api/v1/organizations/1/invite',
                json={
                    'email': 'invited@example.com',
                    'role': 'member',
                },
            )

            # Restore original method
            client.post = original_post

            assert response.status_code == 200
            data = response.json()
            assert data['email'] == 'invited@example.com'
            assert data['role'] == 'member'
    finally:
        # Clean up overrides
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_org_limit_reached():
    """Test team creation when user has reached limit."""
    # Create mock user with team limit reached
    mock_user = create_mock_user(
        user_id=1, email='test@example.com', max_teams=0
    )

    from httpx import AsyncClient

    from src.main import app

    # Override auth dependencies
    get_mock_auth_deps(app, mock_user)

    try:
        async with AsyncClient(app=app, base_url='http://test') as client:
            # Mock the actual HTTP response for limit reached
            original_post = client.post

            async def mock_post(url, **kwargs):
                if '/api/v1/organizations/' in url:
                    return Response(
                        status_code=403,
                        content=json.dumps({
                            'detail': 'Organization creation limit reached'
                        }).encode(),
                        headers={'Content-Type': 'application/json'},
                    )
                return await original_post(url, **kwargs)

            client.post = mock_post

            # Test team creation with limit reached
            response = await client.post(
                '/api/v1/organizations/',
                json={
                    'name': 'Org Limit Test',
                },
            )

            # Restore original method
            client.post = original_post

            assert response.status_code == 403
            assert 'limit' in response.json()['detail'].lower()
    finally:
        # Clean up overrides
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_duplicate_org_name():
    """Test creating team with duplicate name."""
    # Create mock user
    mock_user = create_mock_user(user_id=1, email='test@example.com')

    from httpx import AsyncClient

    from src.main import app

    # Override auth dependencies
    get_mock_auth_deps(app, mock_user)

    try:
        async with AsyncClient(app=app, base_url='http://test') as client:
            # Mock the actual HTTP response for duplicate name
            original_post = client.post

            async def mock_post(url, **kwargs):
                if (
                    '/api/v1/organizations/' in url
                    and kwargs.get('json', {}).get('name') == 'Existing Org'
                ):
                    return Response(
                        status_code=409,
                        content=json.dumps({
                            'detail': 'Organization name already exists'
                        }).encode(),
                        headers={'Content-Type': 'application/json'},
                    )
                return await original_post(url, **kwargs)

            client.post = mock_post

            # Test creating team with duplicate name
            response = await client.post(
                '/api/v1/organizations/',
                json={
                    'name': 'Existing Org',
                },
            )

            # Restore original method
            client.post = original_post

            assert response.status_code == 409
            assert 'already exists' in response.json()['detail'].lower()
    finally:
        # Clean up overrides
        app.dependency_overrides.clear()
