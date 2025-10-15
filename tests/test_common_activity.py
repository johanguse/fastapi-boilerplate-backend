import pytest

pytest.skip(
    'deprecated duplicate; moved to tests/common', allow_module_level=True
)

from pydantic import BaseModel  # noqa: E402
from sqlalchemy import text  # noqa: E402

from src.common.activity import ActivityLogData, log_activity  # noqa: E402


class DummyUser(BaseModel):
    id: int


@pytest.mark.asyncio
async def test_log_activity_persists(db_session):
    # Create a simple user row in DB compatible with ActivityLog FK
    # Using the real User model may require hashing/fields; we can insert via raw SQL
    await db_session.execute(
        text(
            """
            INSERT INTO users (
                email,
                hashed_password,
                is_active,
                role,
                created_at,
                is_superuser,
                is_verified,
                max_teams
            )
            VALUES (
                'act@test.com',
                'x',
                true,
                'member',
                now(),
                false,
                false,
                3
            )
            RETURNING id
            """
        )
    )
    await db_session.commit()

    res = await db_session.execute(
        text("SELECT id FROM users WHERE email='act@test.com'")
    )
    user_id = res.fetchone()[0]

    user = DummyUser(id=user_id)
    data = ActivityLogData(action='test', description='did something')

    activity = await log_activity(db_session, user, data)
    assert activity.id is not None
    assert activity.user_id == user_id
    assert activity.action == 'test'
    assert activity.description == 'did something'
