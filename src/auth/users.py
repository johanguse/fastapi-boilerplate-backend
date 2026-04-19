from typing import Optional

from fastapi import Depends, Request
from fastapi.security import HTTPBearer
from fastapi_users import BaseUserManager, FastAPIUsers, IntegerIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.exceptions import UserNotExists
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.common.config import settings
from src.common.session import async_session_factory, get_async_session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = settings.JWT_SECRET
    verification_token_secret = settings.JWT_SECRET

    # Override to allow unverified users to login
    # Email verification is optional - users will see a banner to verify
    async def authenticate(self, credentials):
        """
        Authenticate a user. Allow login regardless of verification status.
        Override the default behavior which blocks unverified users.
        """
        try:
            user = await self.get_by_email(credentials.username)
        except UserNotExists:
            # Run the hasher to mitigate timing attack
            # Inspired from Django: https://code.djangoproject.com/ticket/20760
            self.password_helper.hash(credentials.password)
            return None

        verified, updated_password_hash = (
            self.password_helper.verify_and_update(
                credentials.password, user.hashed_password
            )
        )
        if not verified:
            return None

        # Update password hash to a more robust one if needed
        # fastapi-users 13+ requires update(user, update_dict)
        if updated_password_hash is not None:
            await self.user_db.update(
                user, {"hashed_password": updated_password_hash}
            )

        # Skip the is_verified check - allow unverified users to login
        # They will see the email verification banner in the UI
        return user

    async def on_after_login(
        self,
        user: User,
        request: Optional[Request] = None,
        response=None,
    ):
        try:
            from src.activity_log.service import log_activity

            async with async_session_factory() as db:
                await log_activity(
                    db,
                    {
                        'action': 'user_logged_in',
                        'description': f'User {user.email} logged in',
                        'user': {'id': user.id},
                        'team_id': None,
                        'project_id': None,
                        'action_type': 'auth',
                        'ip_address': (
                            request.client.host
                            if request and request.client
                            else None
                        ),
                        'user_agent': (
                            request.headers.get('user-agent')
                            if request
                            else None
                        ),
                    },
                )
        except Exception:
            pass

    @staticmethod
    async def on_after_register(user: User, request: Optional[Request] = None):
        try:
            from src.activity_log.service import log_activity

            async with async_session_factory() as db:
                await log_activity(
                    db,
                    {
                        'action': 'user_registered',
                        'description': f'User {user.email} registered',
                        'user': {'id': user.id},
                        'team_id': None,
                        'project_id': None,
                        'action_type': 'system',
                    },
                )
        except Exception:
            pass

    @staticmethod
    async def on_after_forgot_password(
        user: User, token: str, request: Optional[Request] = None
    ):
        try:
            from src.activity_log.service import log_activity

            async with async_session_factory() as db:
                await log_activity(
                    db,
                    {
                        'action': 'password_reset_requested',
                        'description': (
                            f'Password reset requested for {user.email}'
                        ),
                        'user': {'id': user.id},
                        'team_id': None,
                        'project_id': None,
                        'action_type': 'auth',
                    },
                )
        except Exception:
            pass

    @staticmethod
    async def on_after_verify(user: User, request: Optional[Request] = None):
        try:
            from src.activity_log.service import log_activity

            async with async_session_factory() as db:
                await log_activity(
                    db,
                    {
                        'action': 'email_verified',
                        'description': f'User {user.email} verified email',
                        'user': {'id': user.id},
                        'team_id': None,
                        'project_id': None,
                        'action_type': 'auth',
                    },
                )
        except Exception:
            pass


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_user_db),
):
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl='/api/v1/auth/jwt/login')


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=settings.JWT_SECRET,
        lifetime_seconds=3600,
        token_audience=['fastapi-users:auth'],
    )


auth_backend = AuthenticationBackend(
    name='jwt',
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# Create FastAPI Users instance without users router
fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)

# Security scheme for Swagger
security = HTTPBearer()

__all__ = ['fastapi_users', 'current_active_user', 'security']
