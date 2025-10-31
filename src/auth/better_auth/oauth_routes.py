"""OAuth social login routes."""

import logging
import secrets
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.auth.oauth_providers import oauth_providers
from src.auth.schemas import UserCreate
from src.auth.users import UserManager, get_user_manager
from src.common.config import settings
from src.common.security import get_current_active_user
from src.common.session import get_async_session

from .jwt_utils import create_better_auth_jwt

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/auth/oauth/{provider}/authorize')
async def oauth_authorize(
    provider: str, request: Request, redirect_url: Optional[str] = None
) -> Dict[str, str]:
    """Get OAuth authorization URL for the specified provider."""
    oauth_provider = await oauth_providers.get_provider(provider)
    if not oauth_provider:
        raise HTTPException(
            status_code=400,
            detail={
                'error': 'INVALID_PROVIDER',
                'message': f"OAuth provider '{provider}' is not supported",
            },
        )

    if redirect_url:
        if not hasattr(request, 'session'):
            request.session = {}  # type: ignore[attr-defined]
        request.session['oauth_redirect_url'] = redirect_url  # type: ignore[index]

    authorization_url = await oauth_provider.get_authorization_url(
        redirect_uri=f'{str(request.base_url)}auth/oauth/{provider}/callback',
        scope=oauth_providers.get_scopes(provider),
    )

    return {'authorization_url': authorization_url}


async def _handle_existing_user(
    user: User, provider: str, user_info: Dict[str, Any], session: AsyncSession
) -> User:
    """Handle OAuth callback for existing user."""
    if user.oauth_provider and user.oauth_provider != provider:
        raise HTTPException(
            status_code=400,
            detail={
                'error': 'OAUTH_ACCOUNT_CONFLICT',
                'message': f'This email is already linked to {user.oauth_provider}. Please use {user.oauth_provider} to sign in or unlink that account first.',
            },
        )
    elif not user.oauth_provider:
        user.oauth_provider = provider
        user.oauth_provider_id = user_info['id']
        if user_info.get('avatar_url') and not user.avatar_url:
            user.avatar_url = user_info['avatar_url']
        if user_info.get('name') and not user.name:
            user.name = user_info['name']
        if user_info.get('email_verified') and not user.is_verified:
            user.is_verified = True
        await session.commit()
    else:
        user.oauth_provider_id = user_info['id']
        if user_info.get('avatar_url'):
            user.avatar_url = user_info['avatar_url']
        if user_info.get('name'):
            user.name = user_info['name']
        await session.commit()
    return user


async def _create_new_oauth_user(
    provider: str, user_info: Dict[str, Any], session: AsyncSession
) -> User:
    """Create new user from OAuth provider."""
    user_manager: UserManager = get_user_manager()  # type: ignore[assignment]
    user_create = UserCreate(
        email=user_info['email'],
        password=secrets.token_urlsafe(32),
        name=user_info.get('name', ''),
        is_verified=user_info.get('email_verified', True),
    )
    user = await user_manager.create(user_create, safe=False)

    user.oauth_provider = provider
    user.oauth_provider_id = user_info['id']
    if user_info.get('avatar_url'):
        user.avatar_url = user_info['avatar_url']
    await session.commit()
    return user


@router.get('/auth/oauth/{provider}/callback')
async def oauth_callback(
    provider: str,
    request: Request,
    code: str,
    state: Optional[str] = None,
    session: AsyncSession = Depends(get_async_session),
) -> RedirectResponse:
    """Handle OAuth callback and create/login user."""
    oauth_provider = await oauth_providers.get_provider(provider)
    if not oauth_provider:
        raise HTTPException(
            status_code=400,
            detail={
                'error': 'INVALID_PROVIDER',
                'message': f"OAuth provider '{provider}' is not supported",
            },
        )

    try:
        token = await oauth_provider.get_access_token(
            code,
            redirect_uri=f'{str(request.base_url)}auth/oauth/{provider}/callback',
        )

        user_info = await oauth_providers.get_user_info(
            provider, token['access_token']
        )

        result = await session.execute(
            select(User).where(User.email == user_info['email'])  # type: ignore[arg-type]
        )
        user = result.scalar_one_or_none()

        if user:
            user = await _handle_existing_user(
                user, provider, user_info, session
            )
        else:
            user = await _create_new_oauth_user(provider, user_info, session)

        access_token = create_better_auth_jwt(user)

        redirect_url = '/dashboard'
        if (
            hasattr(request, 'session')
            and 'oauth_redirect_url' in request.session  # type: ignore[operator]
        ):
            redirect_url = request.session['oauth_redirect_url']  # type: ignore[index]
            del request.session['oauth_redirect_url']  # type: ignore[attr-defined]

        response = RedirectResponse(url=redirect_url, status_code=303)
        response.set_cookie(
            key='access_token',
            value=access_token,
            max_age=30 * 24 * 60 * 60,
            httponly=True,
            secure=True,
            samesite='lax',
        )

        return response

    except Exception as e:
        logging.error(f'OAuth callback failed for {provider}: {str(e)}')
        raise HTTPException(
            status_code=400,
            detail={
                'error': 'OAUTH_CALLBACK_FAILED',
                'message': f'OAuth callback failed: {str(e)}',
            },
        )


@router.post('/auth/oauth/{provider}/link')
async def link_oauth_account(
    provider: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, str]:
    """Link OAuth account to existing user account."""
    oauth_provider = await oauth_providers.get_provider(provider)
    if not oauth_provider:
        raise HTTPException(
            status_code=400,
            detail={
                'error': 'INVALID_PROVIDER',
                'message': f"OAuth provider '{provider}' is not supported",
            },
        )

    authorization_url = await oauth_provider.get_authorization_url(
        redirect_uri=f'{str(request.base_url)}auth/oauth/{provider}/link-callback',
        scope=oauth_providers.get_scopes(provider),
    )

    return {'authorization_url': authorization_url}


@router.get('/auth/oauth/{provider}/link-callback')
async def oauth_link_callback(
    provider: str,
    request: Request,
    code: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> RedirectResponse:
    """Handle OAuth link callback."""
    oauth_provider = await oauth_providers.get_provider(provider)
    if not oauth_provider:
        raise HTTPException(
            status_code=400,
            detail={
                'error': 'INVALID_PROVIDER',
                'message': f"OAuth provider '{provider}' is not supported",
            },
        )

    try:
        token = await oauth_provider.get_access_token(
            code,
            redirect_uri=f'{str(request.base_url)}auth/oauth/{provider}/link-callback',
        )

        user_info = await oauth_providers.get_user_info(
            provider, token['access_token']
        )

        result = await session.execute(
            select(User).where(
                User.oauth_provider == provider,  # type: ignore[arg-type]
                User.oauth_provider_id == user_info['id'],  # type: ignore[arg-type]
            )
        )
        existing_user = result.scalar_one_or_none()

        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=400,
                detail={
                    'error': 'OAUTH_ACCOUNT_LINKED',
                    'message': 'This OAuth account is already linked to another user',
                },
            )

        current_user.oauth_provider = provider
        current_user.oauth_provider_id = user_info['id']
        if user_info.get('avatar_url') and not current_user.avatar_url:
            current_user.avatar_url = user_info['avatar_url']

        await session.commit()

        return RedirectResponse(url='/settings/account', status_code=303)

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f'OAuth link failed for {provider}: {str(e)}')
        raise HTTPException(
            status_code=400,
            detail={
                'error': 'OAUTH_LINK_FAILED',
                'message': f'OAuth account linking failed: {str(e)}',
            },
        )


@router.post('/auth/oauth/{provider}/unlink')
async def unlink_oauth_account(
    provider: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """Unlink OAuth account from user."""
    if (
        not hasattr(current_user, 'hashed_password')
        or not current_user.hashed_password
    ) and current_user.oauth_provider == provider:
        raise HTTPException(
            status_code=400,
            detail={
                'error': 'CANNOT_UNLINK_ONLY_AUTH',
                'message': 'Cannot unlink the only authentication method. Set a password first.',
            },
        )

    if current_user.oauth_provider == provider:
        current_user.oauth_provider = None
        current_user.oauth_provider_id = None
        await session.commit()

        return {
            'success': True,
            'message': f'{provider.title()} account unlinked successfully',
        }
    else:
        raise HTTPException(
            status_code=400,
            detail={
                'error': 'OAUTH_NOT_LINKED',
                'message': f'No {provider.title()} account is linked to this user',
            },
        )


@router.get('/auth/oauth/providers')
async def get_oauth_providers() -> Dict[str, Any]:
    """Get list of available OAuth providers."""
    return {
        'providers': [
            {
                'id': 'google',
                'name': 'Google',
                'enabled': bool(
                    settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET
                ),
            },
            {
                'id': 'github',
                'name': 'GitHub',
                'enabled': bool(
                    settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET
                ),
            },
            {
                'id': 'microsoft',
                'name': 'Microsoft',
                'enabled': bool(
                    settings.MICROSOFT_CLIENT_ID
                    and settings.MICROSOFT_CLIENT_SECRET
                ),
            },
            {
                'id': 'apple',
                'name': 'Apple',
                'enabled': bool(
                    settings.APPLE_CLIENT_ID and settings.APPLE_CLIENT_SECRET
                ),
            },
        ]
    }
