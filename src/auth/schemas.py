from typing import Optional

from fastapi_users import schemas
from pydantic import BaseModel


class UserRead(schemas.BaseUser[int]):
    name: Optional[str] = None
    role: str


class UserCreate(schemas.BaseUserCreate):
    name: Optional[str] = None
    role: str = 'member'


class UserUpdate(BaseModel):
    name: str | None = None
    # Explicitly list updatable fields
    # DO NOT include: email, is_active, roles, etc

    class Config:
        extra = 'forbid'  # Prevent unexpected fields
