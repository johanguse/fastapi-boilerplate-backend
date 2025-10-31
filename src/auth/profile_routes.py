"""
User profile management routes including image upload.
"""
import logging
import uuid
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.common.config import settings
from src.common.session import get_async_session
from src.common.security import get_current_active_user
from src.utils.storage import delete_file_from_r2, upload_file_to_r2

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/users', tags=['users'])


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile."""

    name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    company: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=200)


class UserProfileResponse(BaseModel):
    """Schema for user profile response."""

    id: int
    email: str
    name: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    status: str

    class Config:
        from_attributes = True


@router.get('/me', response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
):
    """Get current user's profile."""
    return current_user


@router.patch('/me', response_model=UserProfileResponse)
async def update_current_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Update current user's profile."""
    try:
        # Update only provided fields
        update_data = profile_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(current_user, field, value)

        await session.commit()
        await session.refresh(current_user)

        return current_user

    except Exception as e:
        await session.rollback()
        logger.error(f'Error updating user profile: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail='Failed to update profile',
        )


@router.post('/me/upload-image')
async def upload_user_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Upload user profile image to R2 storage."""
    try:
        # Validate file type
        if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f'Unsupported file type. Allowed types: {", ".join(settings.ALLOWED_IMAGE_TYPES)}',
            )

        # Validate file size (read first 5MB + 1 byte to check if exceeds limit)
        max_size = 5 * 1024 * 1024  # 5MB
        contents = await file.read(max_size + 1)
        if len(contents) > max_size:
            raise HTTPException(
                status_code=400,
                detail='File size exceeds 5MB limit',
            )

        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if file.filename else 'jpg'
        unique_filename = f'avatars/{current_user.id}/{uuid.uuid4()}.{file_extension}'

        # Upload to R2
        file_url = await upload_file_to_r2(
            contents,
            unique_filename,
            file.content_type,
        )

        if not file_url:
            raise HTTPException(
                status_code=500,
                detail='Failed to upload image',
            )

        # Delete old avatar if exists
        if current_user.avatar_url:
            try:
                # Extract filename from URL
                old_filename = current_user.avatar_url.split('/')[-1]
                if old_filename.startswith('avatars/'):
                    await delete_file_from_r2(old_filename)
            except Exception as e:
                logger.warning(f'Failed to delete old avatar: {str(e)}')

        # Update user's avatar_url
        current_user.avatar_url = file_url
        await session.commit()
        await session.refresh(current_user)

        return {
            'url': file_url,
            'message': 'Profile image uploaded successfully',
        }

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f'Error uploading profile image: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail='Failed to upload image',
        )


@router.delete('/me/image')
async def delete_user_profile_image(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Delete user's profile image."""
    try:
        if not current_user.avatar_url:
            raise HTTPException(
                status_code=404,
                detail='No profile image found',
            )

        # Extract filename from URL and delete from R2
        try:
            filename = current_user.avatar_url.split('/')[-1]
            await delete_file_from_r2(filename)
        except Exception as e:
            logger.warning(f'Failed to delete image from R2: {str(e)}')

        # Clear avatar_url from database
        current_user.avatar_url = None
        await session.commit()

        return {
            'message': 'Profile image deleted successfully',
        }

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f'Error deleting profile image: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail='Failed to delete image',
        )
