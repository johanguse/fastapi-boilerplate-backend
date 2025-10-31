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
from src.common.session import get_async_session


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

        verified, updated_password_hash = self.password_helper.verify_and_update(
            credentials.password, user.hashed_password
        )
        if not verified:
            return None
        
        # Update password hash to a more robust one if needed
        if updated_password_hash is not None:
            user.hashed_password = updated_password_hash
            await self.user_db.update(user)

        # Skip the is_verified check - allow unverified users to login
        # They will see the email verification banner in the UI
        return user
    
    # Allow unverified users to login - verification is optional
    # They'll see a banner in the UI to verify their email
    async def on_after_login(
        self,
        user: User,
        request: Optional[Request] = None,
        response = None,
    ):
        """Override to skip email verification check on login."""
        if request:
            from src.activity_log.service import log_activity

            await log_activity(
                request.state.db,
                action='user_logged_in',
                description=f'User {user.email} logged in',
                user=user,
                team_id=0,
                project_id=0,
                action_type='auth',
                ip_address=request.client.host,
                user_agent=request.headers.get('user-agent'),
            )

    @staticmethod
    async def on_after_register(user: User, request: Optional[Request] = None):
        if request:
            from src.activity_log.service import log_activity  # Moved import

            await log_activity(
                request.state.db,
                {
                    'action': 'user_registered',
                    'description': f'User {user.email} registered',
                    'user': user,
                    'team_id': 0,
                    'project_id': 0,
                    'action_type': 'system',
                },
            )

    @staticmethod
    async def on_after_forgot_password(
        user: User, token: str, request: Optional[Request] = None
    ):
        if request:
            from src.activity_log.service import log_activity  # Moved import

            await log_activity(
                request.state.db,
                action='password_reset_requested',
                description=f'Password reset requested for {user.email}',
                user=user,
                team_id=0,
                project_id=0,
                action_type='auth',
            )

    @staticmethod
    async def on_after_verify(user: User, request: Optional[Request] = None):
        if request:
            from src.activity_log.service import log_activity  # Moved import

            await log_activity(
                request.state.db,
                action='email_verified',
                description=f'User {user.email} verified email',
                user=user,
                team_id=0,
                project_id=0,
                action_type='auth',
            )


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
