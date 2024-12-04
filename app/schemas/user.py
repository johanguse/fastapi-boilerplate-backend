from fastapi_users import schemas


class UserRead(schemas.BaseUser[int]):
    name: str | None = None
    role: str


class UserCreate(schemas.BaseUserCreate):
    name: str | None = None
    role: str = 'member'


class UserUpdate(schemas.BaseUserUpdate):
    name: str | None = None
    role: str | None = None
