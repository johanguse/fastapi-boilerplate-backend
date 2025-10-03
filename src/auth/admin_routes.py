from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func, delete as sql_delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from src.auth.models import User
from src.auth.schemas import UserRead, UserCreate
from src.activity_log.models import ActivityLog
from src.common.pagination import CustomParams, Paginated
from src.common.session import get_async_session

router = APIRouter(prefix='/admin', tags=['admin'])


async def get_current_user_from_cookie(
    request: Request, db: AsyncSession = Depends(get_async_session)
) -> User:
    """Get current user from Better Auth cookie"""
    from src.auth.better_auth_compat import (
        _get_token_from_request,
        verify_better_auth_jwt,
    )

    token = _get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail='Not authenticated')

    payload = verify_better_auth_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail='Invalid token')

    user_id = int(payload['sub'])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail='User not found or inactive')

    return user


def require_admin(current_user: User = Depends(get_current_user_from_cookie)):
    """Dependency to check if user is admin"""
    if current_user.role != 'admin' and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail='Admin access required')
    return current_user


@router.get('/users', response_model=Paginated[UserRead])
async def list_all_users(
    params: CustomParams = Depends(),
    search: str = Query(None, description='Search by name or email'),
    role: str = Query(None, description='Filter by role'),
    db: AsyncSession = Depends(get_async_session),
    _admin: User = Depends(require_admin),
):
    """
    List all users with pagination and search (Admin only)
    """
    query = select(User)

    # Apply search filter
    if search:
        search_filter = f'%{search}%'
        query = query.where(
            (User.name.ilike(search_filter)) | (User.email.ilike(search_filter))
        )

    # Apply role filter
    if role:
        query = query.where(User.role == role)

    # Order by created_at descending
    query = query.order_by(User.created_at.desc())

    # Execute query with pagination
    result = await db.execute(
        query.limit(params.size).offset((params.page - 1) * params.size)
    )
    users = result.scalars().all()

    # Count total
    count_query = select(User)
    if search:
        search_filter = f'%{search}%'
        count_query = count_query.where(
            (User.name.ilike(search_filter))
            | (User.email.ilike(search_filter))
        )
    if role:
        count_query = count_query.where(User.role == role)

    total_result = await db.execute(count_query)
    total = len(total_result.scalars().all())

    # Calculate total pages
    pages = (total + params.size - 1) // params.size if total > 0 else 1

    return Paginated(
        items=[UserRead.model_validate(user) for user in users],
        total=total,
        page=params.page,
        size=params.size,
        pages=pages,
    )


@router.get('/users/{user_id}', response_model=UserRead)
async def get_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_async_session),
    _admin: User = Depends(require_admin),
):
    """
    Get user by ID (Admin only)
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail='User not found')

    return user


@router.get('/stats')
async def get_admin_stats(
    db: AsyncSession = Depends(get_async_session),
    _admin: User = Depends(require_admin),
):
    """
    Get admin statistics (Admin only)
    """
    # Total users
    total_users_result = await db.execute(select(User))
    total_users = len(total_users_result.scalars().all())

    # Verified users
    verified_users_result = await db.execute(
        select(User).where(User.is_verified == True)
    )
    verified_users = len(verified_users_result.scalars().all())

    # Active users
    active_users_result = await db.execute(
        select(User).where(User.is_active == True)
    )
    active_users = len(active_users_result.scalars().all())

    # Users by role
    admin_users_result = await db.execute(
        select(User).where(User.role == 'admin')
    )
    admin_users = len(admin_users_result.scalars().all())

    member_users_result = await db.execute(
        select(User).where(User.role == 'member')
    )
    member_users = len(member_users_result.scalars().all())

    return {
        'total_users': total_users,
        'verified_users': verified_users,
        'active_users': active_users,
        'admin_users': admin_users,
        'member_users': member_users,
    }


# User Management Schemas
class UserUpdateAdmin(BaseModel):
    """Schema for admin to update user"""
    name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None  # active, invited, suspended
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class UserInvite(BaseModel):
    """Schema for inviting a user"""
    email: EmailStr
    name: str
    role: str = 'member'
    status: str = 'invited'  # Default status for invited users


@router.patch('/users/{user_id}', response_model=UserRead)
async def update_user(
    user_id: int,
    user_update: UserUpdateAdmin,
    db: AsyncSession = Depends(get_async_session),
    _admin: User = Depends(require_admin),
):
    """
    Update user (Admin only)
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail='User not found')

    # Update fields
    if user_update.name is not None:
        user.name = user_update.name
    if user_update.role is not None:
        user.role = user_update.role
    if user_update.status is not None:
        user.status = user_update.status
        # Sync is_active with status
        user.is_active = user_update.status != 'suspended'
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
        # Sync status with is_active if status not explicitly set
        if user_update.status is None:
            user.status = 'active' if user_update.is_active else 'suspended'
    if user_update.is_verified is not None:
        user.is_verified = user_update.is_verified

    await db.commit()
    await db.refresh(user)

    return user


@router.delete('/users/{user_id}')
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_session),
    _admin: User = Depends(require_admin),
):
    """
    Delete user (Admin only)
    """
    # Prevent admin from deleting themselves
    if _admin.id == user_id:
        raise HTTPException(
            status_code=400,
            detail='Cannot delete your own account'
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail='User not found')

    await db.delete(user)
    await db.commit()

    return {'success': True, 'message': 'User deleted successfully'}


@router.post('/users/invite', response_model=UserRead)
async def invite_user(
    invite: UserInvite,
    db: AsyncSession = Depends(get_async_session),
    _admin: User = Depends(require_admin),
):
    """
    Invite a new user (Admin only)
    Creates user account with temporary password
    """
    from src.auth.users import get_user_manager
    import secrets

    # Check if user already exists
    existing_result = await db.execute(
        select(User).where(User.email == invite.email)
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail='User with this email already exists'
        )

    # Create user with random password (they'll need to reset)
    temp_password = secrets.token_urlsafe(16)
    user_manager = get_user_manager()
    
    user_create = UserCreate(
        email=invite.email,
        password=temp_password,
        name=invite.name,
        role=invite.role,
        is_active=True,
        is_verified=False,
    )
    
    user = await user_manager.create(user_create, safe=False)
    
    # Set status to 'invited'
    user.status = 'invited'
    await db.commit()
    await db.refresh(user)
    
    # TODO: Send invitation email with password reset link
    # For now, just return the created user
    
    return user


@router.get('/analytics/overview')
async def get_analytics_overview(
    db: AsyncSession = Depends(get_async_session),
    _admin: User = Depends(require_admin),
):
    """
    Get analytics overview for reports dashboard (Admin only)
    """
    from datetime import datetime, timedelta
    from src.organizations.models import Organization
    from src.subscriptions.models import CustomerSubscription, BillingHistory
    from src.activity_log.models import ActivityLog
    
    # Date ranges
    now = datetime.now()
    last_30_days = now - timedelta(days=30)
    last_7_days = now - timedelta(days=7)
    
    # Users analytics
    total_users = await db.scalar(select(func.count(User.id)))
    new_users_30d = await db.scalar(
        select(func.count(User.id)).where(User.created_at >= last_30_days)
    )
    new_users_7d = await db.scalar(
        select(func.count(User.id)).where(User.created_at >= last_7_days)
    )
    
    # Organizations analytics
    total_orgs = await db.scalar(select(func.count(Organization.id)))
    
    # Subscriptions analytics
    active_subs = await db.scalar(
        select(func.count(CustomerSubscription.id)).where(
            CustomerSubscription.status == 'active'
        )
    )
    
    # Revenue analytics (from billing history)
    total_revenue_result = await db.execute(
        select(func.sum(BillingHistory.amount)).where(
            BillingHistory.status == 'paid'
        )
    )
    total_revenue = total_revenue_result.scalar() or 0
    
    revenue_30d_result = await db.execute(
        select(func.sum(BillingHistory.amount)).where(
            BillingHistory.status == 'paid',
            BillingHistory.paid_at >= last_30_days
        )
    )
    revenue_30d = revenue_30d_result.scalar() or 0
    
    # Activity logs
    total_activities = await db.scalar(select(func.count(ActivityLog.id)))
    
    return {
        'users': {
            'total': total_users or 0,
            'new_last_30_days': new_users_30d or 0,
            'new_last_7_days': new_users_7d or 0,
        },
        'organizations': {
            'total': total_orgs or 0,
        },
        'subscriptions': {
            'active': active_subs or 0,
        },
        'revenue': {
            'total': total_revenue,
            'last_30_days': revenue_30d,
            'currency': 'usd',
        },
        'activity': {
            'total_events': total_activities or 0,
        },
    }


@router.get('/analytics/users-growth')
async def get_users_growth(
    days: int = Query(30, description='Number of days to analyze'),
    db: AsyncSession = Depends(get_async_session),
    _admin: User = Depends(require_admin),
):
    """
    Get user growth data for charts (Admin only)
    """
    from datetime import datetime, timedelta
    
    now = datetime.now()
    start_date = now - timedelta(days=days)
    
    # Group users by day
    result = await db.execute(
        select(
            func.date(User.created_at).label('date'),
            func.count(User.id).label('count')
        )
        .where(User.created_at >= start_date)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
    )
    
    growth_data = [
        {
            'date': str(row.date),
            'count': row.count,
        }
        for row in result
    ]
    
    return {'data': growth_data}


@router.get('/analytics/revenue-chart')
async def get_revenue_chart(
    days: int = Query(30, description='Number of days to analyze'),
    db: AsyncSession = Depends(get_async_session),
    _admin: User = Depends(require_admin),
):
    """
    Get revenue data for charts (Admin only)
    """
    from datetime import datetime, timedelta
    from src.subscriptions.models import BillingHistory
    
    now = datetime.now()
    start_date = now - timedelta(days=days)
    
    # Group revenue by day
    result = await db.execute(
        select(
            func.date(BillingHistory.paid_at).label('date'),
            func.sum(BillingHistory.amount).label('revenue')
        )
        .where(
            BillingHistory.status == 'paid',
            BillingHistory.paid_at >= start_date
        )
        .group_by(func.date(BillingHistory.paid_at))
        .order_by(func.date(BillingHistory.paid_at))
    )
    
    revenue_data = [
        {
            'date': str(row.date),
            'revenue': row.revenue or 0,
        }
        for row in result
    ]
    
    return {'data': revenue_data, 'currency': 'usd'}


# Activity Logs Schema
class ActivityLogRead(BaseModel):
    id: int
    action: str
    action_type: str
    description: str
    action_metadata: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    user_id: Optional[int] = None
    organization_id: Optional[int] = None
    project_id: Optional[int] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None

    class Config:
        from_attributes = True


@router.get('/activity-logs', response_model=Paginated[ActivityLogRead])
async def list_activity_logs(
    params: CustomParams = Depends(),
    action_type: str = Query(None, description='Filter by action type'),
    user_id: int = Query(None, description='Filter by user ID'),
    organization_id: int = Query(None, description='Filter by organization ID'),
    db: AsyncSession = Depends(get_async_session),
    _admin: User = Depends(require_admin),
):
    """
    List activity logs with pagination and filters (Admin only)
    """
    from sqlalchemy.orm import selectinload
    
    # Build query with selectinload for better performance
    query = select(ActivityLog).options(selectinload(ActivityLog.user))

    # Apply filters
    if action_type:
        query = query.where(ActivityLog.action_type == action_type)
    if user_id:
        query = query.where(ActivityLog.user_id == user_id)
    if organization_id:
        query = query.where(ActivityLog.organization_id == organization_id)

    # Order by created_at descending (newest first)
    query = query.order_by(desc(ActivityLog.created_at))

    # Execute query with pagination
    result = await db.execute(
        query.limit(params.size).offset((params.page - 1) * params.size)
    )
    activity_logs = result.scalars().all()

    # Convert to ActivityLogRead objects
    logs = []
    for activity_log in activity_logs:
        log_dict = {
            'id': activity_log.id,
            'action': activity_log.action,
            'action_type': activity_log.action_type,
            'description': activity_log.description,
            'action_metadata': activity_log.action_metadata,
            'ip_address': activity_log.ip_address,
            'user_agent': activity_log.user_agent,
            'created_at': activity_log.created_at,
            'user_id': activity_log.user_id,
            'organization_id': activity_log.organization_id,
            'project_id': activity_log.project_id,
            'user_name': activity_log.user.name if activity_log.user else None,
            'user_email': activity_log.user.email if activity_log.user else None,
        }
        logs.append(ActivityLogRead(**log_dict))

    # Count total with optimized query
    count_query = select(func.count()).select_from(ActivityLog)
    if action_type:
        count_query = count_query.where(ActivityLog.action_type == action_type)
    if user_id:
        count_query = count_query.where(ActivityLog.user_id == user_id)
    if organization_id:
        count_query = count_query.where(
            ActivityLog.organization_id == organization_id
        )

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Calculate total pages
    pages = (total + params.size - 1) // params.size if total > 0 else 1

    return Paginated(
        items=logs,
        total=total,
        page=params.page,
        size=params.size,
        pages=pages,
    )
