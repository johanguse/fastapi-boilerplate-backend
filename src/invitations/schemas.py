"""Pydantic schemas for invitations."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class TeamInvitationCreate(BaseModel):
    """Schema for creating a team invitation."""

    email: EmailStr
    role: str = Field(
        default='member', pattern='^(owner|admin|member|viewer)$'
    )
    message: Optional[str] = Field(None, max_length=500)


class TeamInvitationResponse(BaseModel):
    """Response schema for team invitation."""

    id: int
    organization_id: int
    email: str
    role: str
    status: str
    message: Optional[str] = None
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class EmailVerificationRequest(BaseModel):
    """Request to resend email verification."""

    pass


class AcceptInvitationRequest(BaseModel):
    """Request to accept invitation."""

    token: str


class InvitationListResponse(BaseModel):
    """Response for list of invitations."""

    id: int
    email: str
    role: str
    status: str
    message: Optional[str]
    invited_by_name: str
    expires_at: datetime
    created_at: datetime
