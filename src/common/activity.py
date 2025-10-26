from typing import Any, Optional, cast

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.activity_log.models import ActivityLog
from src.auth.models import User


class ActivityLogData(BaseModel):
    """Data required for logging an activity."""

    action: str
    description: str
    project_id: Optional[int] = None
    organization_id: Optional[int] = None
    ip_address: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


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
    # Build values using DB column names, omitting None values so nullable
    # fields are left to defaults and to keep INSERT column list minimal.
    values: dict[str, Any] = {
        'action': data.action,
        'action_type': 'OTHER',
        'description': data.description,
        'user_id': user.id,
    }
    if data.ip_address is not None:
        values['ip_address'] = data.ip_address
    if data.metadata is not None:
        values['metadata'] = data.metadata
    if data.project_id is not None:
        values['project_id'] = data.project_id
    if data.organization_id is not None:
        values['organization_id'] = data.organization_id

    # Dynamically construct a minimal INSERT with only provided columns.
    cols = ', '.join(values.keys())
    params = ', '.join(f':{k}' for k in values.keys())
    stmt = text(
        f'INSERT INTO {ActivityLog.__tablename__} ({cols}) VALUES ({params}) RETURNING id'
    )
    result = await db.execute(stmt, values)
    new_id = result.scalar_one()

    await db.commit()

    # Return a lightweight object to avoid ORM SELECTs that may reference
    # columns not present in legacy schemas (e.g., organization_id).
    from types import SimpleNamespace
    return cast(ActivityLog, SimpleNamespace(
        id=new_id,
        user_id=values.get('user_id'),
        action=values.get('action'),
        description=values.get('description'),
    ))
