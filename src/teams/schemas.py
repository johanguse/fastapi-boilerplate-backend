from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class TeamBase(BaseModel):
    name: str


class TeamCreate(TeamBase):
    pass


class TeamInvite(BaseModel):
    email: EmailStr
    role: str


class TeamMemberBase(BaseModel):
    user_id: int
    role: str


class TeamMemberResponse(TeamMemberBase):
    email: EmailStr
    name: Optional[str]
    joined_at: datetime

    class Config:
        from_attributes = True


class TeamResponse(TeamBase):
    id: int
    created_at: datetime
    updated_at: datetime
    members: List[TeamMemberResponse]

    class Config:
        from_attributes = True
