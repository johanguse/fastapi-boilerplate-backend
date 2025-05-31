from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.auth.schemas import UserRead, UserUpdate
from src.auth.service import get_user_by_email, get_users, update_user
from src.auth.users import current_active_user
from src.common.pagination import CustomParams, Paginated
from src.common.session import get_async_session

router = APIRouter(tags=['users'])


@router.get('/me', response_model=UserRead)
async def get_current_user(
    current_user: User = Depends(current_active_user),
):
    """
    Get current user profile
    """
    return current_user


@router.patch('/me', response_model=UserRead)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Update current user profile
    """
    return await update_user(db, current_user.id, user_update)


@router.get('/users', response_model=Paginated[UserRead])
async def list_users(
    params: CustomParams = Depends(),
    search: str = Query(None, description='Search by name or email'),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """
    List users with pagination and search
    """
    return await get_users(db, params, search)


@router.get('/users/{email}', response_model=UserRead)
async def get_user_profile(
    email: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """
    Get user profile by email
    """
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    return user
