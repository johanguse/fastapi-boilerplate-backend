"""
Manual test script to verify our authentication fix.
Run this directly with: python -m tests.manual_test
"""

import asyncio

from httpx import AsyncClient

from src.auth.users import current_active_user
from src.main import app


async def test_me_endpoint():
    """Test the /me endpoint with a mocked user."""

    # Create a Mock User class to avoid SQLAlchemy initialization issues
    class MockUser:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    # Create a mock user
    mock_user = MockUser(
        id=1,
        email='test@example.com',
        name='Test User',
        is_active=True,
        is_verified=True,
        is_superuser=False,
        role='member',
        max_teams=5,
    )

    # Define the override function
    async def override_current_active_user():
        return mock_user

    # Override the dependency
    app.dependency_overrides[current_active_user] = (
        override_current_active_user
    )

    try:
        # Create a test client
        async with AsyncClient(app=app, base_url='http://test') as client:
            # Make the request
            response = await client.get('/api/v1/me')

            # Print the results
            print(f'Status code: {response.status_code}')
            if response.status_code == 200:
                print(f'Response: {response.json()}')
                print('Test PASSED!')
            else:
                print(f'Error: {response.text}')
                print('Test FAILED!')
    finally:
        # Clear dependency override
        app.dependency_overrides.pop(current_active_user, None)


if __name__ == '__main__':
    asyncio.run(test_me_endpoint())
