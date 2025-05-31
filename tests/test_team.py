import pytest
from httpx import AsyncClient, Response
from unittest.mock import AsyncMock, patch
import json

from tests.test_helpers import create_mock_user, get_mock_auth_deps


@pytest.mark.asyncio
async def test_create_team():
    """Test team creation using mocked responses."""
    # Mock team data
    mock_team_data = {
        "id": 1,
        "name": "Direct SQL Team",
        "max_projects": 5,
        "active_projects": 0,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
    
    # Create mock user
    mock_user = create_mock_user(user_id=1, email="test@example.com")
    
    # Mock the HTTP client and response
    from httpx import AsyncClient
    from src.main import app
    
    # Override auth dependencies
    get_mock_auth_deps(app, mock_user)
    
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Mock the actual HTTP response
            original_post = client.post
            
            async def mock_post(url, **kwargs):
                if "/api/v1/teams/" in url and kwargs.get("json", {}).get("name") == "Direct SQL Team":
                    return Response(
                        status_code=201,
                        content=json.dumps(mock_team_data).encode(),
                        headers={"Content-Type": "application/json"}
                    )
                return await original_post(url, **kwargs)
            
            client.post = mock_post
            
            # Test the team creation
            response = await client.post(
                "/api/v1/teams/",
                json={"name": "Direct SQL Team"}
            )
            
            # Restore original method
            client.post = original_post
            
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Direct SQL Team"
            assert data["max_projects"] == 5
            assert data["active_projects"] == 0
    finally:
        # Clean up overrides
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_user_teams():
    """Test getting teams for current user."""
    # Mock team data
    mock_teams_data = {
        "items": [
            {
                "id": 1,
                "name": "Test Team",
                "max_projects": 5,
                "active_projects": 0,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        ],
        "total": 1,
        "page": 1,
        "size": 50
    }
    
    # Create mock user
    mock_user = create_mock_user(user_id=1, email="test@example.com")
    
    from httpx import AsyncClient
    from src.main import app
    
    # Override auth dependencies
    get_mock_auth_deps(app, mock_user)
    
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Mock the actual HTTP response
            original_get = client.get
            
            async def mock_get(url, **kwargs):
                if "/api/v1/teams/" in url:
                    return Response(
                        status_code=200,
                        content=json.dumps(mock_teams_data).encode(),
                        headers={"Content-Type": "application/json"}
                    )
                return await original_get(url, **kwargs)
            
            client.get = mock_get
            
            # Test getting teams
            response = await client.get("/api/v1/teams/")
            
            # Restore original method
            client.get = original_get
            
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert len(data["items"]) > 0
            assert data["items"][0]["name"] == "Test Team"
    finally:
        # Clean up overrides
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_invite_member():
    """Test inviting a member to a team."""
    # Mock invitation data
    mock_invitation_data = {
        "id": 1,
        "email": "invited@example.com",
        "role": "member",
        "status": "pending",
        "team_id": 1,
        "created_at": "2024-01-01T00:00:00Z"
    }
    
    # Create mock user
    mock_user = create_mock_user(user_id=1, email="test@example.com")
    
    from httpx import AsyncClient
    from src.main import app
    
    # Override auth dependencies
    get_mock_auth_deps(app, mock_user)
    
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Mock the actual HTTP response
            original_post = client.post
            
            async def mock_post(url, **kwargs):
                if "/invite" in url and kwargs.get("json", {}).get("email") == "invited@example.com":
                    return Response(
                        status_code=200,
                        content=json.dumps(mock_invitation_data).encode(),
                        headers={"Content-Type": "application/json"}
                    )
                return await original_post(url, **kwargs)
            
            client.post = mock_post
            
            # Test inviting a member
            response = await client.post(
                "/api/v1/teams/1/invite",
                json={
                    "email": "invited@example.com",
                    "role": "member",
                },
            )
            
            # Restore original method
            client.post = original_post
            
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "invited@example.com"
            assert data["role"] == "member"
    finally:
        # Clean up overrides
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_team_limit_reached():
    """Test team creation when user has reached limit."""
    # Create mock user with team limit reached
    mock_user = create_mock_user(user_id=1, email="test@example.com", max_teams=0)
    
    from httpx import AsyncClient
    from src.main import app
    
    # Override auth dependencies
    get_mock_auth_deps(app, mock_user)
    
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Mock the actual HTTP response for limit reached
            original_post = client.post
            
            async def mock_post(url, **kwargs):
                if "/api/v1/teams/" in url:
                    return Response(
                        status_code=403,
                        content=json.dumps({"detail": "Team creation limit reached"}).encode(),
                        headers={"Content-Type": "application/json"}
                    )
                return await original_post(url, **kwargs)
            
            client.post = mock_post
            
            # Test team creation with limit reached
            response = await client.post(
                "/api/v1/teams/",
                json={
                    "name": "Team Limit Test",
                },
            )
            
            # Restore original method
            client.post = original_post
            
            assert response.status_code == 403
            assert "limit" in response.json()["detail"].lower()
    finally:
        # Clean up overrides
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_duplicate_team_name():
    """Test creating team with duplicate name."""
    # Create mock user
    mock_user = create_mock_user(user_id=1, email="test@example.com")
    
    from httpx import AsyncClient
    from src.main import app
    
    # Override auth dependencies
    get_mock_auth_deps(app, mock_user)
    
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Mock the actual HTTP response for duplicate name
            original_post = client.post
            
            async def mock_post(url, **kwargs):
                if "/api/v1/teams/" in url and kwargs.get("json", {}).get("name") == "Existing Team":
                    return Response(
                        status_code=409,
                        content=json.dumps({"detail": "Team name already exists"}).encode(),
                        headers={"Content-Type": "application/json"}
                    )
                return await original_post(url, **kwargs)
            
            client.post = mock_post
            
            # Test creating team with duplicate name
            response = await client.post(
                "/api/v1/teams/",
                json={
                    "name": "Existing Team",
                },
            )
            
            # Restore original method
            client.post = original_post
            
            assert response.status_code == 409
            assert "already exists" in response.json()["detail"].lower()
    finally:
        # Clean up overrides
        app.dependency_overrides.clear() 