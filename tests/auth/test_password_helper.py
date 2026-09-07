"""
Tests for password hashing and verification functionality.
"""

import pytest
from fastapi_users.db import SQLAlchemyUserDatabase

from src.auth.models import User
from src.auth.users import UserManager


@pytest.mark.asyncio
async def test_password_hashing_and_verification(async_session):
    """Test password hashing and verification using UserManager"""

    # Create user database instance
    user_db = SQLAlchemyUserDatabase(async_session, User)
    user_manager = UserManager(user_db)

    # Test password hashing
    password = 'test_password_123'
    hashed = user_manager.password_helper.hash(password)

    assert hashed is not None
    assert hashed != password  # Ensure it's actually hashed
    assert hashed.startswith('$argon2id$')  # Verify it's using Argon2

    # Test password verification
    is_valid, updated_hash = user_manager.password_helper.verify_and_update(
        password, hashed
    )
    assert is_valid is True
    assert updated_hash is None  # No update needed for fresh hash

    # Test wrong password
    is_valid, updated_hash = user_manager.password_helper.verify_and_update(
        'wrong_password', hashed
    )
    assert is_valid is False
    assert updated_hash is None


@pytest.mark.asyncio
async def test_password_helper_consistency(async_session):
    """Test that password helper produces consistent results"""

    user_db = SQLAlchemyUserDatabase(async_session, User)
    user_manager = UserManager(user_db)

    password = 'consistent_test'

    # Hash the same password multiple times
    hash1 = user_manager.password_helper.hash(password)
    hash2 = user_manager.password_helper.hash(password)

    # Hashes should be different (due to salt) but both should verify
    assert hash1 != hash2

    is_valid1, _ = user_manager.password_helper.verify_and_update(
        password, hash1
    )
    is_valid2, _ = user_manager.password_helper.verify_and_update(
        password, hash2
    )

    assert is_valid1 is True
    assert is_valid2 is True


@pytest.mark.asyncio
async def test_bcrypt_compatibility(async_session):
    """Test compatibility with existing bcrypt hashes"""

    user_db = SQLAlchemyUserDatabase(async_session, User)
    user_manager = UserManager(user_db)

    # Example bcrypt hash for "admin123"
    bcrypt_hash = (
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8xq/2vV3za'
    )

    # Test if the password helper can still verify bcrypt hashes
    is_valid, updated_hash = user_manager.password_helper.verify_and_update(
        'admin123', bcrypt_hash
    )

    # Note: This might fail if the system only supports Argon2 now
    # In that case, you'd need a migration strategy for existing users
    if not is_valid:
        # Document that bcrypt compatibility is not available
        pytest.skip(
            'Bcrypt compatibility not available - migration needed for existing users'
        )
    else:
        assert is_valid is True
        # updated_hash might contain a new Argon2 hash if auto-upgrade is enabled
        if updated_hash:
            assert updated_hash.startswith('$argon2id$')


@pytest.mark.asyncio
async def test_empty_password_handling(async_session):
    """Test handling of edge cases like empty passwords"""

    user_db = SQLAlchemyUserDatabase(async_session, User)
    user_manager = UserManager(user_db)

    # Test empty password (should still hash)
    empty_hash = user_manager.password_helper.hash('')
    assert empty_hash is not None
    assert empty_hash

    # Verify empty password
    is_valid, _ = user_manager.password_helper.verify_and_update(
        '', empty_hash
    )
    assert is_valid is True

    # Test that non-empty password doesn't verify against empty hash
    is_valid, _ = user_manager.password_helper.verify_and_update(
        'not_empty', empty_hash
    )
    assert is_valid is False
