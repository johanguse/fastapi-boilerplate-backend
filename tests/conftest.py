import asyncio
from typing import AsyncGenerator, Dict, Any

import pytest
import pytest_asyncio
from fastapi import Depends
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi_users.db import SQLAlchemyUserDatabase

# Import all models to ensure proper mapper initialization
from src.activity_log.models import ActivityLog
from src.auth.models import User
from src.auth.users import get_user_manager, UserManager
from src.auth.schemas import UserCreate
from src.common.config import settings
from src.common.database import Base
from src.common.session import get_async_session
from src.projects.models import Project
from src.teams.models import Team, TeamMember, Invitation
from src.main import app
from tests.test_helpers import create_test_user_raw, create_test_team_raw, create_test_project_raw, create_test_auth_token, create_mock_user, get_mock_auth_deps

# Create a separate test engine
test_engine = create_async_engine(
    settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://'),
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create the session factory
TestingSessionLocal = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(autouse=True)
async def clean_test_data():
    """Clean test data after each test."""
    async with TestingSessionLocal() as session:
        try:
            await session.execute(
                text("DELETE FROM users WHERE email IN ('test@example.com', 'new@example.com')")
            )
            await session.commit()
        except Exception:
            await session.rollback()
        finally:
            await session.close()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the event loop for each test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def init_db():
    # No need to create/drop tables in PostgreSQL - they should already exist
    # We'll just clean up test data after tests
    yield


@pytest_asyncio.fixture
async def async_session(init_db) -> AsyncGenerator[AsyncSession, None]:
    """Create a new session for each test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        await session.rollback()
        await session.close()


@pytest_asyncio.fixture
async def client(async_session) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with dependency overrides."""
    # Override the database session
    async def override_get_db():
        yield async_session

    # Apply the override
    app.dependency_overrides[get_async_session] = override_get_db
    
    # Create and yield the client
    try:
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    finally:
        # Always clear overrides, even if there's an exception
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(async_session: AsyncSession) -> Dict[str, Any]:
    """Create a test user using raw SQL."""
    return await create_test_user_raw(async_session)


@pytest_asyncio.fixture
async def authenticated_client(client: AsyncClient, test_user: Dict[str, Any], async_session: AsyncSession) -> AsyncClient:
    """Return a client with an authentication token in headers."""
    # Ensure the test_user fixture has run and the user exists for token creation
    # The test_user fixture already returns a dict with id and email
    user_id = test_user["id"]
    email = test_user["email"]

    token = await create_test_auth_token(user_id=user_id, email=email)
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest_asyncio.fixture
async def test_team(async_session: AsyncSession, test_user: Dict[str, Any]) -> Dict[str, Any]:
    """Create a test team using raw SQL."""
    return await create_test_team_raw(async_session, test_user["id"])


@pytest_asyncio.fixture
async def test_project(async_session: AsyncSession, test_team: Dict[str, Any]) -> Dict[str, Any]:
    """Create a test project using raw SQL."""
    return await create_test_project_raw(async_session, test_team["id"]) 