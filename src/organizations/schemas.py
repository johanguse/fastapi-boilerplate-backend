from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class OrganizationBase(BaseModel):
    name: str
    slug: Optional[str] = None
    logo_url: Optional[str] = None
    description: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationInvite(BaseModel):
    email: EmailStr
    role: str


class OrganizationMemberBase(BaseModel):
    user_id: int
    role: str


class OrganizationMemberResponse(OrganizationMemberBase):
    email: EmailStr
    name: Optional[str]
    joined_at: datetime

    class Config:
        from_attributes = True


class OrganizationResponse(OrganizationBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    max_projects: int
    active_projects: int
    members: List[OrganizationMemberResponse] = []

    class Config:
        from_attributes = True
