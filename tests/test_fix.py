from typing import Any, Dict

import pytest
from httpx import AsyncClient

from src.main import app
from tests.test_helpers import get_mock_auth_deps


@pytest.mark.asyncio
async def test_get_me_endpoint(client: AsyncClient, test_user: Dict[str, Any]):
    """Test /me endpoint with proper authentication mocking."""
    # Set up mock authentication
    get_mock_auth_deps(app, test_user)

    try:
        # Make the request
        response = await client.get('/api/v1/me')

        # Check the response
        assert response.status_code == 200
        assert response.json()['email'] == test_user['email']
    finally:
        # Always clear dependency overrides
        app.dependency_overrides.clear()
