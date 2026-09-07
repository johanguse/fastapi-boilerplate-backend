import pytest

from src.common.config import settings
from src.common.security import get_current_active_user, get_current_user
from tests.test_helpers import create_test_auth_token, create_test_user_raw


@pytest.mark.asyncio
async def test_get_current_user_with_fastapi_users_token(async_session):
    # Arrange: create a user and a FastAPI Users-compatible token
    user = await create_test_user_raw(
        async_session, email='fausers_unique1@example.com'
    )
    token = await create_test_auth_token(
        user_id=user['id'], email=user['email']
    )

    # Act
    db_user = await get_current_user(token=token, db=async_session)

    # Assert
    assert db_user is not None
    assert str(db_user.email) == user['email']


@pytest.mark.asyncio
async def test_get_current_active_user_inactive_raises():
    # Arrange: a minimal user-like object with is_active=False
    class DummyUser:
        is_active = False

    # Act & Assert
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await get_current_active_user(current_user=DummyUser())
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_get_current_user_with_invalid_token_returns_401(
    async_session, monkeypatch
):
    # Ensure Better Auth doesn't interfere; test FastAPI Users path failure
    monkeypatch.setattr(settings, 'BETTER_AUTH_ENABLED', False, raising=False)
    invalid_token = 'not-a-valid-jwt'

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=invalid_token, db=async_session)
    assert exc.value.status_code == 401
