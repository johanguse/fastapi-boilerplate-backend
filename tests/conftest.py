from typing import Any, AsyncGenerator, Dict

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Import all models to ensure proper mapper initialization
from src.common.config import settings
from src.common.session import get_async_session
from src.main import app
from tests.test_helpers import (
    create_test_auth_token,
    create_test_organization_raw,
    create_test_project_raw,
    create_test_user_raw,
)

# Explicitly ignore deprecated/duplicate-named test modules to avoid import mismatches
collect_ignore = [
    'tests/organizations/test_service.py',
    'tests/payments/test_service.py',
    'tests/test_services_projects.py',
]


def _make_engine():
    """Create a per-test async engine tied to the current event loop.

    Using NullPool prevents cross-loop leaks from pooled connections and avoids
    asyncpg cancellations after the loop is closed.
    """
    return create_async_engine(
        settings.DATABASE_URL.replace(
            'postgresql://', 'postgresql+asyncpg://'
        ),
        echo=False,
        pool_pre_ping=True,
        pool_recycle=300,
        poolclass=NullPool,
    )


@pytest_asyncio.fixture(autouse=True)
async def clean_test_data():
    """Clean test data after each test using a short-lived engine/session."""
    # Run test
    yield
    # Cleanup phase
    engine = _make_engine()
    try:
        async_session_factory = sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        async with async_session_factory() as session:
            try:
                # Delete all test users created during tests (those with @example.com)
                await session.execute(
                    text(
                        "DELETE FROM users WHERE email LIKE '%@example.com'"
                    )
                )
                # Also delete the hardcoded test emails
                await session.execute(
                    text(
                        "DELETE FROM users WHERE email IN ('test@example.com', 'new@example.com', 'act@test.com')"
                    )
                )
                await session.commit()
            except Exception:
                await session.rollback()
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(scope='function')
async def init_db():
    # No need to create/drop tables in PostgreSQL - they should already exist
    # We'll just clean up test data after tests
    yield


@pytest_asyncio.fixture
async def async_session(init_db) -> AsyncGenerator[AsyncSession, None]:
    """Create a new per-test engine and session to avoid cross-loop issues."""
    engine = _make_engine()
    async_session_factory = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    session = async_session_factory()
    try:
        yield session
    finally:
        # best-effort rollback and close
        try:
            await session.rollback()
        except Exception:
            pass
        try:
            await session.close()
        finally:
            await engine.dispose()


# Back-compat for legacy tests expecting a `db_session` fixture name
@pytest_asyncio.fixture
async def db_session(
    async_session: AsyncSession,
) -> AsyncGenerator[AsyncSession, None]:
    yield async_session


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
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url='http://test'
        ) as ac:
            yield ac
    finally:
        # Always clear overrides, even if there's an exception
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(async_session: AsyncSession) -> Dict[str, Any]:
    """Create a test user using raw SQL."""
    return await create_test_user_raw(async_session)


@pytest_asyncio.fixture
async def authenticated_client(
    client: AsyncClient, test_user: Dict[str, Any], async_session: AsyncSession
) -> AsyncClient:
    """Return a client with an authentication token in headers."""
    # Ensure the test_user fixture has run and the user exists for token creation
    # The test_user fixture already returns a dict with id and email
    user_id = test_user['id']
    email = test_user['email']

    token = await create_test_auth_token(user_id=user_id, email=email)
    client.headers['Authorization'] = f'Bearer {token}'
    return client


@pytest_asyncio.fixture
async def test_organization(
    async_session: AsyncSession, test_user: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a test organization using raw SQL."""
    return await create_test_organization_raw(async_session, test_user['id'])


@pytest_asyncio.fixture
async def test_project(
    async_session: AsyncSession, test_organization: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a test project using raw SQL."""
    return await create_test_project_raw(
        async_session, test_organization['id']
    )
