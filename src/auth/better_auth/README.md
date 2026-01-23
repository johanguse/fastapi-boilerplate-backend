# Better Auth Compatibility Layer

This module provides a Better Auth-compatible API layer for the FastAPI Users backend.

## Structure

The module has been refactored into a more maintainable structure:

```
better_auth/
├── __init__.py                 # Main module entry point
├── router.py                   # Combined router for all endpoints
├── models.py                   # Pydantic models for requests/responses
├── jwt_utils.py                # JWT token creation and verification
├── cookie_utils.py             # Cookie management utilities
├── request_utils.py            # Request parsing and user extraction
├── auth_routes.py              # Authentication endpoints (sign-in, sign-up, session)
├── organization_routes.py      # Organization management endpoints
└── oauth_routes.py             # OAuth social login endpoints
```

## Features

### Authentication (`auth_routes.py`)
- `POST /auth/sign-in/email` - Email/password sign in
- `POST /auth/sign-up/email` - Email/password registration
- `POST /auth/sign-out` - Sign out (clears cookies)
- `GET /auth/session` - Get current session
- `GET /auth/get-session` - Alias for session endpoint
- `POST /auth/forgot-password` - Request password reset
- `POST /auth/reset-password` - Reset password with token

### Organizations (`organization_routes.py`)
- `GET /auth/organization` - List user's organizations
- `GET /auth/organization/list` - Alias for list
- `POST /auth/organization` - Create organization
- `POST /auth/organization/create` - Alias for create
- `POST /auth/organization/set-active` - Set active organization
- `GET /auth/organization/{org_id}` - Get organization details
- `PUT /auth/organization/{org_id}` - Update organization
- `DELETE /auth/organization/{org_id}` - Delete organization
- Stub endpoints for members and invitations (compatibility)

### OAuth (`oauth_routes.py`)
- `GET /auth/oauth/{provider}/authorize` - Get OAuth authorization URL
- `GET /auth/oauth/{provider}/callback` - Handle OAuth callback
- `POST /auth/oauth/{provider}/link` - Link OAuth to existing account
- `GET /auth/oauth/{provider}/link-callback` - Handle OAuth link callback
- `POST /auth/oauth/{provider}/unlink` - Unlink OAuth account
- `GET /auth/oauth/providers` - List available OAuth providers

Supported providers: Google, GitHub, Microsoft, Apple

## Utilities

### JWT Utils (`jwt_utils.py`)
- `create_better_auth_jwt(user)` - Create JWT token
- `verify_better_auth_jwt(token)` - Verify and decode JWT token

### Cookie Utils (`cookie_utils.py`)
- `set_auth_cookie(response, key, value, path)` - Set secure cookie
- `delete_auth_cookie(response, key, path)` - Delete cookie

### Request Utils (`request_utils.py`)
- `get_token_from_request(request)` - Extract JWT from request
- `get_user_from_request(request, session)` - Get authenticated user

## Usage

```python
from src.auth.better_auth import router

app.include_router(router)
```

The router automatically includes all authentication, organization, and OAuth endpoints.

## Type Ignore Comments

SQLAlchemy column comparisons use operator overloading that Pylance doesn't fully understand. These are marked with `# type: ignore[arg-type]` comments to suppress false positives while maintaining type safety for the rest of the codebase.
