"""
OAuth provider configurations and handlers for social login integration.
Supports Google, GitHub, Microsoft, and Apple Sign-In.
"""

import logging
from typing import Any, Dict

import httpx
from fastapi import HTTPException
from httpx_oauth.clients.github import GitHubOAuth2
from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.clients.microsoft import MicrosoftGraphOAuth2

from src.common.config import settings

logger = logging.getLogger(__name__)


class OAuthProviders:
    """OAuth provider management and configuration"""

    def __init__(self):
        self.providers = {}
        self._setup_providers()

    def _setup_providers(self):
        """Initialize OAuth providers based on configuration"""

        # Google OAuth
        if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
            self.providers['google'] = GoogleOAuth2(
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
                scopes=['openid', 'email', 'profile'],
            )
            logger.info('Google OAuth provider configured')

        # GitHub OAuth
        if settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET:
            self.providers['github'] = GitHubOAuth2(
                client_id=settings.GITHUB_CLIENT_ID,
                client_secret=settings.GITHUB_CLIENT_SECRET,
                scopes=['user:email'],
            )
            logger.info('GitHub OAuth provider configured')

        # Microsoft OAuth
        if settings.MICROSOFT_CLIENT_ID and settings.MICROSOFT_CLIENT_SECRET:
            self.providers['microsoft'] = MicrosoftGraphOAuth2(
                client_id=settings.MICROSOFT_CLIENT_ID,
                client_secret=settings.MICROSOFT_CLIENT_SECRET,
                scopes=['openid', 'email', 'profile'],
            )
            logger.info('Microsoft OAuth provider configured')

    def get_provider(self, provider_name: str):
        """Get OAuth provider by name"""
        provider = self.providers.get(provider_name)
        if not provider:
            raise HTTPException(
                status_code=400,
                detail=f"OAuth provider '{provider_name}' not configured",
            )
        return provider

    @staticmethod
    def get_scopes(provider_name: str) -> list:
        """Get OAuth scopes for a provider"""
        scopes = {
            'google': ['openid', 'email', 'profile'],
            'github': ['user:email'],
            'microsoft': ['openid', 'email', 'profile'],
            'apple': ['email', 'name'],
        }
        return scopes.get(provider_name, ['email'])

    def get_authorization_url(
        self, provider_name: str, redirect_uri: str, state: str = None
    ) -> str:
        """Get OAuth authorization URL for a provider"""
        provider = self.get_provider(provider_name)
        return provider.get_authorization_url(redirect_uri, state=state)

    async def get_access_token(
        self, provider_name: str, code: str, redirect_uri: str
    ) -> str:
        """Exchange authorization code for access token"""
        provider = self.get_provider(provider_name)
        token = await provider.get_access_token(code, redirect_uri)
        return token['access_token']

    async def get_user_info(
        self, provider_name: str, access_token: str
    ) -> Dict[str, Any]:
        """Get user information from OAuth provider"""
        self.get_provider(provider_name)

        if provider_name == 'google':
            return await OAuthProviders._get_google_user_info(access_token)
        elif provider_name == 'github':
            return await OAuthProviders._get_github_user_info(access_token)
        elif provider_name == 'microsoft':
            return await OAuthProviders._get_microsoft_user_info(access_token)
        elif provider_name == 'apple':
            return await OAuthProviders._get_apple_user_info(access_token)
        else:
            raise HTTPException(
                status_code=400,
                detail=f'Unsupported provider: {provider_name}',
            )

    @staticmethod
    async def _get_google_user_info(access_token: str) -> Dict[str, Any]:
        """Get user info from Google"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'},
            )
            response.raise_for_status()
            data = response.json()

            return {
                'id': data['id'],
                'email': data['email'],
                'name': data.get('name', ''),
                'picture': data.get('picture', ''),
                'email_verified': data.get('verified_email', False),
                'provider': 'google',
            }

    @staticmethod
    async def _get_github_user_info(access_token: str) -> Dict[str, Any]:
        """Get user info from GitHub"""
        async with httpx.AsyncClient() as client:
            # Get user profile
            user_response = await client.get(
                'https://api.github.com/user',
                headers={'Authorization': f'Bearer {access_token}'},
            )
            user_response.raise_for_status()
            user_data = user_response.json()

            # Get primary email (GitHub API requires separate call)
            emails_response = await client.get(
                'https://api.github.com/user/emails',
                headers={'Authorization': f'Bearer {access_token}'},
            )
            emails_response.raise_for_status()
            emails_data = emails_response.json()

            primary_email = next(
                (
                    email
                    for email in emails_data
                    if email.get('primary', False)
                ),
                emails_data[0] if emails_data else None,
            )

            return {
                'id': str(user_data['id']),
                'email': primary_email['email']
                if primary_email
                else user_data.get('email', ''),
                'name': user_data.get('name') or user_data.get('login', ''),
                'picture': user_data.get('avatar_url', ''),
                'email_verified': primary_email.get('verified', False)
                if primary_email
                else False,
                'provider': 'github',
            }

    @staticmethod
    async def _get_microsoft_user_info(access_token: str) -> Dict[str, Any]:
        """Get user info from Microsoft Graph"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://graph.microsoft.com/v1.0/me',
                headers={'Authorization': f'Bearer {access_token}'},
            )
            response.raise_for_status()
            data = response.json()

            return {
                'id': data['id'],
                'email': data.get('mail') or data.get('userPrincipalName', ''),
                'name': data.get('displayName', ''),
                'picture': '',  # Microsoft Graph photo requires separate API call
                'email_verified': True,  # Microsoft emails are generally verified
                'provider': 'microsoft',
            }

    @staticmethod
    async def _get_apple_user_info(access_token: str) -> Dict[str, Any]:
        """Get user info from Apple (minimal implementation)"""
        # Apple Sign-In returns user info differently, usually in the initial callback
        # This is a placeholder for future Apple Sign-In implementation
        raise HTTPException(
            status_code=501, detail='Apple Sign-In not yet implemented'
        )

    def get_available_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available OAuth providers with their display information"""
        providers_info = {}

        for provider_name in self.providers.keys():
            providers_info[provider_name] = {
                'name': provider_name.title(),
                'display_name': OAuthProviders._get_provider_display_name(
                    provider_name
                ),
                'icon': OAuthProviders._get_provider_icon(provider_name),
                'color': OAuthProviders._get_provider_color(provider_name),
            }

        return providers_info

    @staticmethod
    def _get_provider_display_name(provider_name: str) -> str:
        """Get human-readable provider name"""
        names = {
            'google': 'Google',
            'github': 'GitHub',
            'microsoft': 'Microsoft',
            'apple': 'Apple',
        }
        return names.get(provider_name, provider_name.title())

    @staticmethod
    def _get_provider_icon(provider_name: str) -> str:
        """Get provider icon class or Unicode symbol"""
        icons = {
            'google': '🔍',
            'github': '🐙',
            'microsoft': '🪟',
            'apple': '🍎',
        }
        return icons.get(provider_name, '🔐')

    @staticmethod
    def _get_provider_color(provider_name: str) -> str:
        """Get provider brand color"""
        colors = {
            'google': '#4285f4',
            'github': '#333333',
            'microsoft': '#0078d4',
            'apple': '#000000',
        }
        return colors.get(provider_name, '#6b7280')


# Global OAuth providers instance
oauth_providers = OAuthProviders()
