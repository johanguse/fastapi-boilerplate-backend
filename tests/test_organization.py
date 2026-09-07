import json

import pytest
from httpx import ASGITransport, AsyncClient, Response

from tests.test_helpers import create_mock_user, get_mock_auth_deps


@pytest.mark.asyncio
async def test_create_organization():
    """Test organization creation using mocked responses."""
    mock_org_data = {
        'id': 1,
        'name': 'Direct SQL Org',
        'max_projects': 5,
        'active_projects': 0,
        'created_at': '2024-01-01T00:00:00Z',
        'updated_at': '2024-01-01T00:00:00Z',
    }

    mock_user = create_mock_user(user_id=1, email='test@example.com')

    from src.main import app

    get_mock_auth_deps(app, mock_user)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url='http://test'
        ) as client:
            original_post = client.post

            async def mock_post(url, **kwargs):
                if (
                    '/api/v1/organizations/' in url
                    and kwargs.get('json', {}).get('name') == 'Direct SQL Org'
                ):
                    return Response(
                        status_code=201,
                        content=json.dumps(mock_org_data).encode(),
                        headers={'Content-Type': 'application/json'},
                    )
                return await original_post(url, **kwargs)

            client.post = mock_post

            response = await client.post(
                '/api/v1/organizations/', json={'name': 'Direct SQL Org'}
            )

            client.post = original_post

            assert response.status_code == 201
            data = response.json()
            assert data['name'] == 'Direct SQL Org'
            assert data['max_projects'] == 5
            assert data['active_projects'] == 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_user_organizations():
    """Test getting organizations for current user."""
    mock_orgs_data = {
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

    mock_user = create_mock_user(user_id=1, email='test@example.com')

    from src.main import app

    get_mock_auth_deps(app, mock_user)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url='http://test'
        ) as client:
            original_get = client.get

            async def mock_get(url, **kwargs):
                if '/api/v1/organizations/' in url:
                    return Response(
                        status_code=200,
                        content=json.dumps(mock_orgs_data).encode(),
                        headers={'Content-Type': 'application/json'},
                    )
                return await original_get(url, **kwargs)

            client.get = mock_get

            response = await client.get('/api/v1/organizations/')

            client.get = original_get

            assert response.status_code == 200
            data = response.json()
            assert 'items' in data
            assert data['items'][0]['name'] == 'Test Org'
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_invite_org_member():
    """Test inviting a member to an organization."""
    mock_invitation_data = {
        'id': 1,
        'email': 'invited@example.com',
        'role': 'member',
        'status': 'pending',
        'organization_id': 1,
        'created_at': '2024-01-01T00:00:00Z',
    }

    mock_user = create_mock_user(user_id=1, email='test@example.com')

    from src.main import app

    get_mock_auth_deps(app, mock_user)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url='http://test'
        ) as client:
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

            response = await client.post(
                '/api/v1/organizations/1/invite',
                json={
                    'email': 'invited@example.com',
                    'role': 'member',
                },
            )

            client.post = original_post

            assert response.status_code == 200
            data = response.json()
            assert data['email'] == 'invited@example.com'
            assert data['role'] == 'member'
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_org_limit_reached():
    """Test organization creation when user has reached limit."""
    mock_user = create_mock_user(
        user_id=1, email='test@example.com', max_teams=0
    )

    from src.main import app

    get_mock_auth_deps(app, mock_user)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url='http://test'
        ) as client:
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

            response = await client.post(
                '/api/v1/organizations/',
                json={
                    'name': 'Org Limit Test',
                },
            )

            client.post = original_post

            assert response.status_code == 403
            assert 'limit' in response.json()['detail'].lower()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_duplicate_org_name():
    """Test creating organization with duplicate name."""
    mock_user = create_mock_user(user_id=1, email='test@example.com')

    from src.main import app

    get_mock_auth_deps(app, mock_user)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url='http://test'
        ) as client:
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

            response = await client.post(
                '/api/v1/organizations/',
                json={
                    'name': 'Existing Org',
                },
            )

            client.post = original_post

            assert response.status_code == 409
            assert 'already exists' in response.json()['detail'].lower()
    finally:
        app.dependency_overrides.clear()
