from typing import Optional

from fastapi import HTTPException
from fastapi_pagination import Page, paginate
from sqlalchemy import desc, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.activity_log.models import ActivityLog
from src.common.pagination import CustomParams

# Remove the TYPE_CHECKING block since it's not used properly
# if TYPE_CHECKING:
#     pass


async def validate_org_exists(db: AsyncSession, organization_id: int):
    # ruff: noqa: PLC0415
    from src.organizations.service import get_organization

    if not await get_organization(db, organization_id):
        raise HTTPException(404, 'Organization not found')


async def validate_project_exists(db: AsyncSession, project_id: int):
    # ruff: noqa: PLC0415
    from src.projects.service import (
        get_project,  # Import locally to avoid circular imports
    )

    if not await get_project(db, project_id):
        raise HTTPException(404, 'Project not found')


async def log_activity(
    db: AsyncSession,
    log_data: dict,
) -> ActivityLog:
    """Create a new activity log entry using a data dictionary."""
    required_fields = ['action', 'description']
    if not all(field in log_data for field in required_fields):
        raise ValueError('Missing required log data fields')

    try:
        # Backward-compat: map team_id -> organization_id if provided
        org_id = log_data.get('organization_id') or log_data.get('team_id')
        activity = ActivityLog(
            action=log_data['action'],
            action_type=log_data.get('action_type', 'user'),
            description=log_data['description'],
            user_id=log_data.get('user', {}).get('id')
            if log_data.get('user')
            else None,
            organization_id=org_id,
            project_id=log_data.get('project_id'),
            action_metadata=log_data.get('metadata', {}),
            ip_address=log_data.get('ip_address'),
            user_agent=log_data.get('user_agent'),
        )
        db.add(activity)
        await db.commit()
        await db.refresh(activity)

        # Optional validations - skip if they fail to avoid blocking activity logging
        # These are just sanity checks; foreign key constraints will catch real issues
        try:
            if org_id:
                await validate_org_exists(db, org_id)
        except Exception:
            # Ignore validation errors - logging shouldn't fail if validation fails
            pass

        try:
            if log_data.get('project_id'):
                await validate_project_exists(db, log_data['project_id'])
        except Exception:
            # Ignore validation errors - logging shouldn't fail if validation fails
            pass

        return activity
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f'Failed to log activity: {str(e)}'
        )


async def get_activities(
    db: AsyncSession,
    params: CustomParams,
    team_id: Optional[int] = None,
    user_id: Optional[int] = None,
    action_type: Optional[str] = None,
) -> Page[ActivityLog]:
    """Get paginated activity logs with filters."""
    query = select(ActivityLog).order_by(desc(ActivityLog.created_at))

    if team_id:
        query = query.where(ActivityLog.organization_id == team_id)
    if user_id:
        query = query.where(ActivityLog.user_id == user_id)
    if action_type:
        query = query.where(ActivityLog.action_type == action_type)

    return await paginate(db, query, params)


async def get_activity_by_id(
    db: AsyncSession,
    activity_id: int,
) -> Optional[ActivityLog]:
    """Get a single activity log by ID."""
    result = await db.execute(
        select(ActivityLog).where(ActivityLog.id == activity_id)
    )
    return result.scalar_one_or_none()
