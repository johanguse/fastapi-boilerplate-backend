from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import get_current_active_user
from app.models.user import User as UserModel
from app.schemas.blog import BlogPost, BlogPostCreate, BlogPostUpdate
from app.services import blog_service

router = APIRouter()


@router.post('/', response_model=BlogPost)
async def create_blog_post(
    post: BlogPostCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: UserModel = Depends(get_current_active_user),
):
    return await blog_service.create_blog_post(db, post, current_user)


@router.get('/', response_model=list[BlogPost])
async def get_blog_posts(
    db: AsyncSession = Depends(get_async_session),
):
    return await blog_service.get_blog_posts(db)


@router.get('/{post_id}', response_model=BlogPost)
async def get_blog_post(
    post_id: int,
    db: AsyncSession = Depends(get_async_session),
):
    return await blog_service.get_blog_post(db, post_id)


@router.put('/{post_id}', response_model=BlogPost)
async def update_blog_post(
    post_id: int,
    post: BlogPostUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: UserModel = Depends(get_current_active_user),
):
    return await blog_service.update_blog_post(db, post_id, post, current_user)


@router.delete('/{post_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_blog_post(
    post_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: UserModel = Depends(get_current_active_user),
):
    await blog_service.delete_blog_post(db, post_id, current_user)
