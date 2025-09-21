import logging
from typing import Optional

from fastapi import HTTPException
from fastapi_pagination import Page, paginate
from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.auth.schemas import UserUpdate
from src.common.pagination import CustomParams

logger = logging.getLogger(__name__)


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get a user by email (case-insensitive)"""
    normalized_email = email.strip().lower()
    result = await db.execute(
        select(User).filter(User.normalized_email == normalized_email)
    )
    return result.scalar_one_or_none()


async def get_users(
    db: AsyncSession,
    params: CustomParams,
    search: Optional[str] = None,
) -> Page[User]:
    """Get paginated list of users with optional search"""
    query = select(User).order_by(User.created_at.desc())

    if search:
        query = query.filter(
            or_(
                User.name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
            )
        )

    return await paginate(db, query, params)


async def update_user(
    db: AsyncSession,
    user_id: int,
    user_update: UserUpdate,
) -> Optional[User]:
    """Update a user's profile"""
    user = await db.get(User, user_id)
    if not user:
        return None

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    try:
        db.add(user)
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f'User update failed: {str(e)}')
        raise HTTPException(status_code=400, detail='Database update error')
    await db.refresh(user)
    return user
