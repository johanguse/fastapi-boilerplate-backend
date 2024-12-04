from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, IntegerIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_session
from app.models.user import User


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    @staticmethod
    async def on_after_register(user: User, request: Request | None = None):
        print(f'User {user.id} has registered.')

    @staticmethod
    async def on_after_forgot_password(
        user: User, token: str, request: Request | None = None
    ):
        print(
            f'User {user.id} has forgot their password. Reset token: {token}'
        )

    @staticmethod
    async def on_after_request_verify(
        user: User, token: str, request: Request | None = None
    ):
        print(
            f'Verification requested for user {user.id}. Verification token: {token}'
        )


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_user_db),
):
    yield UserManager(user_db)


bearer_transport = BearerTransport(
    tokenUrl=f'{settings.API_V1_STR}/auth/jwt/login'
)


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.SECRET_KEY, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name='jwt',
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# Add this line to set a custom scheme name
auth_backend.name = 'JWT'

fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
