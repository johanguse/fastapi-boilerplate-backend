from src.auth.service import AuthService
from httpx import AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession


class TestAuth:
    """Test authentication endpoints."""

    @pytest.mark.asyncio
    async def test_register_user(self, client: AsyncClient):
        """Test user registration."""
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "name": "Test User",
        }

        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["name"] == user_data["name"]
        assert data["is_active"] is True
        assert data["is_verified"] is False
        assert "id" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test registration with duplicate email."""
        # Create a user first
        await AuthService.create_user(
            db=db_session,
            email="test@example.com",
            password="password123",
            name="Existing User",
        )

        user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "name": "Test User",
        }

        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful login."""
        # Create a user first
        user = await AuthService.create_user(
            db=db_session,
            email="test@example.com",
            password="password123",
            name="Test User",
        )
        user.is_active = True
        await db_session.commit()

        login_data = {"email": "test@example.com", "password": "password123"}

        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials."""
        login_data = {"email": "nonexistent@example.com", "password": "wrongpassword"}

        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_current_user(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test getting current user profile."""
        # Create and login user
        user = await AuthService.create_user(
            db=db_session,
            email="test@example.com",
            password="password123",
            name="Test User",
        )
        user.is_active = True
        await db_session.commit()

        # Login to get token
        login_data = {"email": "test@example.com", "password": "password123"}
        login_response = await client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]

        # Get current user
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"

    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without token."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 403  # No authorization header
