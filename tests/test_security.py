from datetime import UTC, datetime, timedelta

import jwt
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
async def test_get_current_user_with_better_auth_hs256(
    async_session, monkeypatch
):
    # Arrange: enable Better Auth HS256 path and create a user
    email = 'better-auth-unique2@example.com'
    await create_test_user_raw(async_session, email=email)

    monkeypatch.setattr(settings, 'BETTER_AUTH_ENABLED', True, raising=False)
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_ALGORITHM', 'HS256', raising=False
    )
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_SHARED_SECRET', 'shared-secret', raising=False
    )
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_AUDIENCE', 'test-aud', raising=False
    )
    monkeypatch.setattr(
        settings,
        'BETTER_AUTH_ISSUER',
        'https://issuer.example.com',
        raising=False,
    )
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_EMAIL_CLAIM', 'email', raising=False
    )
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_SUB_IS_EMAIL', True, raising=False
    )

    payload = {
        'sub': email,
        'email': email,
        'aud': settings.BETTER_AUTH_AUDIENCE,
        'iss': settings.BETTER_AUTH_ISSUER,
        'exp': datetime.now(UTC) + timedelta(minutes=30),
    }
    token = jwt.encode(
        payload, settings.BETTER_AUTH_SHARED_SECRET, algorithm='HS256'
    )

    # Act
    db_user = await get_current_user(token=token, db=async_session)

    # Assert
    assert db_user is not None
    assert str(db_user.email) == email


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


@pytest.mark.asyncio
async def test_get_current_user_better_auth_wrong_audience_401(
    async_session, monkeypatch
):
    # Arrange Better Auth HS256 but with wrong audience in token
    email = 'aud-mismatch@example.com'
    await create_test_user_raw(async_session, email=email)

    monkeypatch.setattr(settings, 'BETTER_AUTH_ENABLED', True, raising=False)
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_ALGORITHM', 'HS256', raising=False
    )
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_SHARED_SECRET', 'shared-secret', raising=False
    )
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_AUDIENCE', 'expected-aud', raising=False
    )
    monkeypatch.setattr(
        settings,
        'BETTER_AUTH_ISSUER',
        'https://issuer.example.com',
        raising=False,
    )
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_EMAIL_CLAIM', 'email', raising=False
    )
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_SUB_IS_EMAIL', True, raising=False
    )

    payload = {
        'sub': email,
        # Omit email intentionally; audience will be mismatched
        'aud': 'wrong-aud',
        'iss': settings.BETTER_AUTH_ISSUER,
        'exp': datetime.now(UTC) + timedelta(minutes=5),
    }
    token = jwt.encode(
        payload, settings.BETTER_AUTH_SHARED_SECRET, algorithm='HS256'
    )

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=token, db=async_session)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_better_auth_sub_only_success(
    async_session, monkeypatch
):
    # Arrange: user exists, token only has sub; SUB_IS_EMAIL True makes sub treated as email
    email = 'sub-only@example.com'
    await create_test_user_raw(async_session, email=email)

    monkeypatch.setattr(settings, 'BETTER_AUTH_ENABLED', True, raising=False)
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_ALGORITHM', 'HS256', raising=False
    )
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_SHARED_SECRET', 'shared-secret', raising=False
    )
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_AUDIENCE', 'test-aud', raising=False
    )
    monkeypatch.setattr(
        settings,
        'BETTER_AUTH_ISSUER',
        'https://issuer.example.com',
        raising=False,
    )
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_EMAIL_CLAIM', 'email', raising=False
    )
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_SUB_IS_EMAIL', True, raising=False
    )

    payload = {
        'sub': email,
        # No 'email' claim on purpose
        'aud': settings.BETTER_AUTH_AUDIENCE,
        'iss': settings.BETTER_AUTH_ISSUER,
        'exp': datetime.now(UTC) + timedelta(minutes=30),
    }
    token = jwt.encode(
        payload, settings.BETTER_AUTH_SHARED_SECRET, algorithm='HS256'
    )

    user = await get_current_user(token=token, db=async_session)
    assert user is not None
    assert str(user.email) == email


@pytest.mark.asyncio
async def test_get_current_user_better_auth_wrong_issuer_401(
    async_session, monkeypatch
):
    # Arrange: HS256 token with wrong issuer
    email = 'issuer-mismatch@example.com'
    await create_test_user_raw(async_session, email=email)

    monkeypatch.setattr(settings, 'BETTER_AUTH_ENABLED', True, raising=False)
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_ALGORITHM', 'HS256', raising=False
    )
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_SHARED_SECRET', 'shared-secret', raising=False
    )
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_AUDIENCE', 'aud-issuer', raising=False
    )
    monkeypatch.setattr(
        settings,
        'BETTER_AUTH_ISSUER',
        'https://good-issuer.example.com',
        raising=False,
    )
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_EMAIL_CLAIM', 'email', raising=False
    )
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_SUB_IS_EMAIL', True, raising=False
    )

    payload = {
        'sub': email,
        'email': email,
        'aud': settings.BETTER_AUTH_AUDIENCE,
        # Wrong issuer provided here
        'iss': 'https://bad-issuer.example.com',
        'exp': datetime.now(UTC) + timedelta(minutes=5),
    }
    token = jwt.encode(
        payload, settings.BETTER_AUTH_SHARED_SECRET, algorithm='HS256'
    )

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=token, db=async_session)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_better_auth_expired_token_401(
    async_session, monkeypatch
):
    # Arrange: HS256 token that is already expired
    email = 'expired-token@example.com'
    await create_test_user_raw(async_session, email=email)

    monkeypatch.setattr(settings, 'BETTER_AUTH_ENABLED', True, raising=False)
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_ALGORITHM', 'HS256', raising=False
    )
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_SHARED_SECRET', 'shared-secret', raising=False
    )
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_AUDIENCE', 'aud-expired', raising=False
    )
    monkeypatch.setattr(
        settings,
        'BETTER_AUTH_ISSUER',
        'https://issuer.example.com',
        raising=False,
    )
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_EMAIL_CLAIM', 'email', raising=False
    )
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_SUB_IS_EMAIL', True, raising=False
    )

    payload = {
        'sub': email,
        'email': email,
        'aud': settings.BETTER_AUTH_AUDIENCE,
        'iss': settings.BETTER_AUTH_ISSUER,
        # Expired 10 minutes ago
        'exp': datetime.now(UTC) - timedelta(minutes=10),
    }
    token = jwt.encode(
        payload, settings.BETTER_AUTH_SHARED_SECRET, algorithm='HS256'
    )

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=token, db=async_session)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_better_auth_rs256_missing_jwks_returns_401(
    async_session, monkeypatch
):
    # Arrange: RS256 configured but JWKS URL missing -> decoder returns None -> 401
    monkeypatch.setattr(settings, 'BETTER_AUTH_ENABLED', True, raising=False)
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_ALGORITHM', 'RS256', raising=False
    )
    # Ensure JWKS URL is absent
    monkeypatch.setattr(settings, 'BETTER_AUTH_JWKS_URL', None, raising=False)

    # Use any invalid token that also fails FastAPI Users path
    token = 'rs256-no-jwks'

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=token, db=async_session)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_better_auth_prefers_email_when_sub_is_email_false(
    async_session, monkeypatch
):
    # Arrange: token has both email and sub but different values; when SUB_IS_EMAIL is False, email should be preferred
    email = 'preferred-email@example.com'
    wrong_sub_email = 'wrong-sub@example.com'
    await create_test_user_raw(async_session, email=email)

    monkeypatch.setattr(settings, 'BETTER_AUTH_ENABLED', True, raising=False)
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_ALGORITHM', 'HS256', raising=False
    )
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_SHARED_SECRET', 'shared-secret', raising=False
    )
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_AUDIENCE', 'aud-email-pref', raising=False
    )
    monkeypatch.setattr(
        settings,
        'BETTER_AUTH_ISSUER',
        'https://issuer.example.com',
        raising=False,
    )
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_EMAIL_CLAIM', 'email', raising=False
    )
    monkeypatch.setattr(
        settings, 'BETTER_AUTH_SUB_IS_EMAIL', False, raising=False
    )

    payload = {
        'sub': wrong_sub_email,
        'email': email,
        'aud': settings.BETTER_AUTH_AUDIENCE,
        'iss': settings.BETTER_AUTH_ISSUER,
        'exp': datetime.now(UTC) + timedelta(minutes=30),
    }
    token = jwt.encode(
        payload, settings.BETTER_AUTH_SHARED_SECRET, algorithm='HS256'
    )

    user = await get_current_user(token=token, db=async_session)
    assert user is not None
    assert str(user.email) == email
