from datetime import UTC, datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.activity_log.models import ActivityLog
from src.auth.models import User


class ActivityLogData(BaseModel):
    """Data required for logging an activity."""

    action: str
    description: str
    project_id: Optional[int] = None
    team_id: Optional[int] = None
    ip_address: Optional[str] = None
    metadata: Optional[dict] = None


async def log_activity(
    db: AsyncSession,
    user: User,
    data: ActivityLogData,
) -> ActivityLog:
    """
    Log an activity performed by a user
    Args:
        db: Database session
        user: User performing the action
        data: Activity log data
    Returns:
        Created ActivityLog instance
    """
    activity = ActivityLog(
        user_id=user.id,
        action=data.action,
        description=data.description,
        project_id=data.project_id,
        team_id=data.team_id,
        ip_address=data.ip_address,
        metadata=data.metadata,
        created_at=datetime.now(UTC),
    )

    db.add(activity)
    await db.commit()
    await db.refresh(activity)

    return activity
