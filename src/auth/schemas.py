from datetime import datetime
from typing import Optional

from fastapi_users import schemas
from pydantic import BaseModel, EmailStr


class UserRead(schemas.BaseUser[int]):
    """User read schema with all profile fields."""
    id: int
    email: EmailStr
    name: Optional[str] = None
    role: str = 'member'
    status: str = 'active'
    created_at: datetime
    updated_at: Optional[datetime] = None
    max_teams: int = 3

    # OAuth fields
    oauth_provider: Optional[str] = None
    oauth_provider_id: Optional[str] = None
    avatar_url: Optional[str] = None

    # Profile fields
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    bio: Optional[str] = None
    website: Optional[str] = None

    # Onboarding tracking
    onboarding_completed: bool = False
    onboarding_step: int = 0


class UserCreate(schemas.BaseUserCreate):
    """User creation schema."""
    name: Optional[str] = None


class UserUpdate(schemas.BaseUserUpdate):
    """User update schema."""
    name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    bio: Optional[str] = None
    website: Optional[str] = None


class OnboardingProfileUpdate(BaseModel):
    """Schema for updating user profile during onboarding."""
    name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    bio: Optional[str] = None
    website: Optional[str] = None


class OnboardingStepUpdate(BaseModel):
    """Schema for updating onboarding step."""
    step: int
    completed: bool = False


class OnboardingComplete(BaseModel):
    """Schema for completing onboarding."""
    completed: bool = True


class OTPSendRequest(BaseModel):
    """Schema for sending OTP code."""
    email: EmailStr


class OTPVerifyRequest(BaseModel):
    """Schema for verifying OTP code."""
    email: EmailStr
    code: str
    name: Optional[str] = None


class OTPResponse(BaseModel):
    """Schema for OTP operation responses."""
    success: bool
    message: str
    user_exists: Optional[bool] = None
