"""
Better Auth compatibility layer for FastAPI Users backend.
Provides Better Auth endpoints that work with existing FastAPI Users authentication.
"""
import jwt
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from urllib.parse import urlparse

from src.auth.models import User
from src.auth.users import get_user_manager, UserManager
from src.auth.schemas import UserCreate
from src.common.config import settings
from src.common.session import get_async_session
from src.organizations.models import Organization, OrganizationMember
from src.organizations.schemas import OrganizationCreate
from src.organizations.service import create_organization as create_organization_service

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Constants
INVALID_CREDENTIALS_MSG = "Invalid email or password"

# Better Auth compatible models
class EmailSignInRequest(BaseModel):
    email: EmailStr
    password: str
    callbackURL: Optional[str] = None

class EmailSignUpRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    callbackURL: Optional[str] = None

class AuthResponse(BaseModel):
    user: Dict[str, Any]
    session: Dict[str, Any]

class ErrorResponse(BaseModel):
    error: str
    message: str

def create_better_auth_jwt(user: User) -> str:
    """Create a JWT token in Better Auth format but compatible with FastAPI Users"""
    payload = {
        "sub": str(user.id),  # Subject (user ID)
        "email": user.email,
        "name": getattr(user, 'name', user.email.split('@')[0]),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(seconds=settings.JWT_LIFETIME_SECONDS),
        "aud": ["fastapi-users:auth"],  # Keep FastAPI Users audience for compatibility
        "iss": "better-auth-compat",   # Better Auth compatible issuer
    }
    
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.ALGORITHM)

def verify_better_auth_jwt(token: str) -> Optional[Dict[str, Any]]:
    """Verify Better Auth JWT token"""
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.ALGORITHM],
            audience=["fastapi-users:auth"]
        )
        return payload
    except jwt.InvalidTokenError:
        return None

def _get_token_from_request(request: Request) -> Optional[str]:
    """Extract JWT from Authorization header or fallback to session cookie."""
    # Bearer token first
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    # Fallback to cookie set by this compat layer
    cookie_token = request.cookies.get("ba_session")
    if cookie_token:
        return cookie_token
    return None

def _cookie_options() -> Dict[str, Any]:
    """Derive cookie security options from FRONTEND_URL.

    - secure=True when FRONTEND_URL is https
    - samesite=None (sent as 'none') when secure, else 'lax'
    - domain set to FRONTEND_URL hostname when not localhost
    """
    frontend = settings.FRONTEND_URL or ""
    secure = frontend.startswith("https")
    samesite = "none" if secure else "lax"
    domain: Optional[str] = None
    try:
        parsed = urlparse(frontend)
        host = parsed.hostname
        if host and host not in ("localhost", "127.0.0.1"):
            domain = host
    except Exception:
        domain = None
    return {"secure": secure, "samesite": samesite, "domain": domain}

def _set_cookie(response: Response, key: str, value: str, path: str = "/") -> None:
    opts = _cookie_options()
    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        secure=opts["secure"],
        samesite=opts["samesite"],
        path=path,
        domain=opts["domain"],
    )

def _delete_cookie(response: Response, key: str, path: str = "/") -> None:
    opts = _cookie_options()
    response.delete_cookie(key=key, path=path, domain=opts["domain"])

async def _get_user_from_request(request: Request, session: AsyncSession) -> User:
    token = _get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="No valid session")
    payload = verify_better_auth_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = int(payload["sub"])  # type: ignore[index]
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user

@router.post("/auth/sign-in/email", response_model=AuthResponse)
async def sign_in_email(
    request: EmailSignInRequest,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
    user_manager: UserManager = Depends(get_user_manager)
):
    """Better Auth compatible email sign in"""
    try:
        logger.info(f"Sign-in attempt for email: {request.email}")

        # Get user by email - FastAPI Users raises UserNotExists if not found
        try:
            user = await user_manager.get_by_email(request.email)
            logger.info(f"User found: {user.email}, active: {user.is_active}")
        except Exception:
            logger.warning(f"User not found: {request.email}")
            raise HTTPException(status_code=400, detail={"error": "INVALID_CREDENTIALS", "message": INVALID_CREDENTIALS_MSG})

        # Verify password
        try:
            valid_password = user_manager.password_helper.verify_and_update(request.password, user.hashed_password)
            logger.info(f"Password verification result: {valid_password[0] if valid_password else False}")
            if not valid_password or not valid_password[0]:
                logger.warning(f"Invalid password for user: {request.email}")
                raise HTTPException(status_code=400, detail={"error": "INVALID_CREDENTIALS", "message": INVALID_CREDENTIALS_MSG})
        except HTTPException:
            raise
        except Exception:
            logger.exception("Password verification error")
            raise HTTPException(status_code=400, detail={"error": "INVALID_CREDENTIALS", "message": INVALID_CREDENTIALS_MSG})

        if not user.is_active:
            logger.warning(f"Inactive user attempted login: {request.email}")
            raise HTTPException(status_code=400, detail={"error": "USER_INACTIVE", "message": "User account is inactive"})

        # Create Better Auth compatible JWT
        token = create_better_auth_jwt(user)

        response_data = AuthResponse(
            user={
                "id": str(user.id),
                "email": user.email,
                "name": getattr(user, 'name', user.email.split('@')[0]),
                "emailVerified": user.is_verified,
                "createdAt": user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
                "updatedAt": user.updated_at.isoformat() if hasattr(user, 'updated_at') and user.updated_at else None,
            },
            session={
                "token": token,
                "expiresAt": (datetime.now(timezone.utc) + timedelta(seconds=settings.JWT_LIFETIME_SECONDS)).isoformat(),
            }
        )

        # Set HTTP-only cookie for session persistence (secure/samesite set dynamically)
        _set_cookie(response, key="ba_session", value=token)
        logger.info(f"Successful login for: {request.email}")
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in sign_in_email: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail={"error": "SIGN_IN_FAILED", "message": f"Authentication failed: {str(e)}"})

@router.post("/auth/sign-up/email", response_model=AuthResponse)
async def sign_up_email(
    request: EmailSignUpRequest,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
    user_manager: UserManager = Depends(get_user_manager)
):
    """Better Auth compatible email sign up"""
    try:
        logger.info(f"Sign-up attempt for email: {request.email}")

        # Check if user already exists - if found, error
        try:
            _ = await user_manager.get_by_email(request.email)
            logger.warning(f"User already exists: {request.email}")
            raise HTTPException(status_code=400, detail={"error": "USER_EXISTS", "message": "User with this email already exists"})
        except Exception:
            # Expected path: user not found
            pass

        # Create user using FastAPI Users
        user_create = UserCreate(
            email=request.email,
            password=request.password,
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        if request.name and hasattr(User, 'name'):
            user_create.name = request.name
        user = await user_manager.create(user_create)

        # Create Better Auth compatible JWT
        token = create_better_auth_jwt(user)

        resp = AuthResponse(
            user={
                "id": str(user.id),
                "email": user.email,
                "name": getattr(user, 'name', request.name or user.email.split('@')[0]),
                "emailVerified": user.is_verified,
                "createdAt": user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
                "updatedAt": user.updated_at.isoformat() if hasattr(user, 'updated_at') and user.updated_at else None,
            },
            session={
                "token": token,
                "expiresAt": (datetime.now(timezone.utc) + timedelta(seconds=settings.JWT_LIFETIME_SECONDS)).isoformat(),
            }
        )

        # Set HTTP-only cookie for session persistence (secure/samesite set dynamically)
        _set_cookie(response, key="ba_session", value=token)
        return resp
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in sign_up_email", exc_info=True)
        raise HTTPException(status_code=400, detail={"error": "SIGN_UP_FAILED", "message": str(e)})

@router.post("/auth/sign-out")
async def sign_out(response: Response):
    """Better Auth compatible sign out"""
    # For JWT-based auth, we just return success
    # Token invalidation would happen on the frontend
    # Clear cookie
    _delete_cookie(response, key="ba_session", path="/")
    _delete_cookie(response, key="ba_active_org", path="/")
    return {"success": True}

@router.get("/auth/session")
async def get_session(
    request: Request,
    session: AsyncSession = Depends(get_async_session)
):
    """Get current session information"""
    # Get token from Authorization header or cookie
    token = _get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="No valid session")
    payload = verify_better_auth_jwt(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Get user from database
    user_id = int(payload["sub"])
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    # Include active org in session response
    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": getattr(user, 'name', user.email.split('@')[0]),
            "emailVerified": user.is_verified,
            "createdAt": user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
            "updatedAt": user.updated_at.isoformat() if hasattr(user, 'updated_at') and user.updated_at else None,
        },
        "session": {
            "token": token,
            "expiresAt": datetime.fromtimestamp(payload["exp"], tz=timezone.utc).isoformat(),
            # Read "active" selections from cookies only
            "activeOrganizationId": request.cookies.get("ba_active_org"),
        }
    }

# Some Better Auth clients use `/auth/get-session`. Provide a compatible alias.
@router.get("/auth/get-session")
async def get_session_alias(
    request: Request,
    session: AsyncSession = Depends(get_async_session)
):
    return await get_session(request, session)

# Organization endpoints (DB-backed)
@router.get("/auth/organization")
async def list_organizations(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """List user's organizations"""
    user = await _get_user_from_request(request, session)
    result = await session.execute(
        select(Organization).join(OrganizationMember).where(OrganizationMember.user_id == user.id)
    )
    organizations: List[Organization] = result.scalars().all()
    orgs = []
    for org in organizations:
        orgs.append({
            "id": str(org.id),
            "name": org.name,
            "slug": org.slug or (org.name or "").lower().replace(" ", "-")[:48],
            "logo": org.logo_url,
            "metadata": None,
            "createdAt": org.created_at.isoformat() if getattr(org, "created_at", None) else None,
        })
    return orgs

@router.get("/auth/organization/list")
async def list_organizations_compat(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """Better Auth plugin expects /auth/organization/list. Return an array."""
    return await list_organizations(request, session)

@router.post("/auth/organization")
async def create_organization(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
):
    """Create organization"""
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    name = (payload or {}).get("name")
    slug = (payload or {}).get("slug")
    if not name:
        raise HTTPException(status_code=400, detail={
            "error": "INVALID_INPUT",
            "message": "name is required",
        })

    # Create organization in DB and add current user as admin
    user = await _get_user_from_request(request, session)
    db_org = await create_organization_service(session, OrganizationCreate(name=name, slug=slug), user)
    
    # Build Better Auth org-like response
    org = {
        "id": str(db_org.id),
        "name": db_org.name,
        "slug": db_org.slug or (db_org.name or "").lower().replace(" ", "-")[:48],
        "logo": db_org.logo_url,
        "metadata": None,
        "createdAt": db_org.created_at.isoformat() if getattr(db_org, "created_at", None) else None,
    }
    # Set active organization cookie
    _set_cookie(response, key="ba_active_org", value=org["id"], path="/")
    return org

@router.post("/auth/organization/create")
async def create_organization_alias(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
):
    """Alias for clients that call /auth/organization/create"""
    return await create_organization(request, response, session)

@router.post("/auth/organization/set-active")
async def set_active_organization(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
):
    """Set the active organization (compat endpoint).

    The Better Auth client expects a 200 response when switching organizations.
    Since we're using stateless JWTs here, we don't embed active org in the token.
    The frontend manages activeOrganization in its own store, so we just acknowledge.
    """
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    org_id = (payload or {}).get("organizationId")
    if not org_id:
        raise HTTPException(status_code=400, detail={
            "error": "INVALID_INPUT",
            "message": "organizationId is required",
        })
    
    # Validate the organization exists and the user is a member
    user = await _get_user_from_request(request, session)
    try:
        org_id_int = int(str(org_id))
    except ValueError:
        raise HTTPException(status_code=400, detail={
            "error": "INVALID_INPUT",
            "message": "organizationId must be an integer",
        })
    
    result = await session.execute(
        select(Organization.id).join(OrganizationMember).where(
            Organization.id == org_id_int, 
            OrganizationMember.user_id == user.id
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail={
            "error": "NOT_FOUND",
            "message": "Organization not found",
        })
    
    # Store active organization only in cookie
    _set_cookie(response, key="ba_active_org", value=str(org_id_int), path="/")
    return {"success": True, "activeOrganizationId": str(org_id_int)}

# Stub endpoints for Better Auth compatibility (not implemented in this simple structure)
@router.get("/auth/organization/list-members")
async def list_members_endpoint(request: Request):
    """List organization members - stub for compatibility"""
    return {"members": []}

@router.post("/auth/organization/remove-member")
async def remove_member_endpoint(request: Request):
    """Remove organization member - stub for compatibility"""
    return {"success": True}

@router.post("/auth/organization/update-member-role")
async def update_member_role_endpoint(request: Request):
    """Update member role - stub for compatibility"""
    return {"success": True}

@router.get("/auth/organization/list-invitations")
async def list_invitations_endpoint(request: Request):
    """List invitations - stub for compatibility"""
    return []

@router.get("/auth/organization/list-user-invitations")
async def list_user_invitations_endpoint(request: Request):
    """List user invitations - stub for compatibility"""
    return []

@router.post("/auth/organization/invite-member")
async def invite_member_endpoint(request: Request):
    """Invite member - stub for compatibility"""
    return {"success": True}

@router.post("/auth/organization/accept-invitation")
async def accept_invitation_endpoint(request: Request):
    """Accept invitation - stub for compatibility"""
    return {"success": True}

@router.post("/auth/organization/reject-invitation")
async def reject_invitation_endpoint(request: Request):
    """Reject invitation - stub for compatibility"""
    return {"success": True}

@router.post("/auth/organization/cancel-invitation")
async def cancel_invitation_endpoint(request: Request):
    """Cancel invitation - stub for compatibility"""
    return {"success": True}

@router.get("/auth/organization/{org_id}")
async def get_organization(
    org_id: int,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """Get a specific organization"""
    user = await _get_user_from_request(request, session)
    
    # Check if user is a member of this organization
    result = await session.execute(
        select(Organization).join(OrganizationMember).where(
            Organization.id == org_id,
            OrganizationMember.user_id == user.id
        )
    )
    organization = result.scalar_one_or_none()
    
    if not organization:
        raise HTTPException(status_code=404, detail={
            "error": "NOT_FOUND", 
            "message": "Organization not found"
        })
    
    return {
        "id": str(organization.id),
        "name": organization.name,
        "slug": organization.slug or (organization.name or "").lower().replace(" ", "-")[:48],
        "logo": organization.logo_url,
        "metadata": None,
        "createdAt": organization.created_at.isoformat() if getattr(organization, "created_at", None) else None,
    }

@router.put("/auth/organization/{org_id}")
async def update_organization(
    org_id: int,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """Update organization"""
    user = await _get_user_from_request(request, session)
    
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    
    # Check if user is an owner or admin of this organization
    result = await session.execute(
        select(Organization, OrganizationMember.role).join(OrganizationMember).where(
            Organization.id == org_id,
            OrganizationMember.user_id == user.id,
            OrganizationMember.role.in_(["owner", "admin"])
        )
    )
    org_and_role = result.first()
    
    if not org_and_role:
        raise HTTPException(status_code=404, detail={
            "error": "NOT_FOUND", 
            "message": "Organization not found or insufficient permissions"
        })
    
    organization = org_and_role[0]
    
    # Update fields
    if "name" in payload:
        organization.name = payload["name"]
    if "slug" in payload:
        organization.slug = payload["slug"]
    if "logo" in payload:
        organization.logo_url = payload["logo"]
    
    await session.commit()
    await session.refresh(organization)
    
    return {
        "id": str(organization.id),
        "name": organization.name,
        "slug": organization.slug or (organization.name or "").lower().replace(" ", "-")[:48],
        "logo": organization.logo_url,
        "metadata": None,
        "createdAt": organization.created_at.isoformat() if getattr(organization, "created_at", None) else None,
    }

@router.delete("/auth/organization/{org_id}")
async def delete_organization(
    org_id: int,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """Delete organization"""
    user = await _get_user_from_request(request, session)
    
    # Check if user is the owner of this organization
    result = await session.execute(
        select(Organization, OrganizationMember.role).join(OrganizationMember).where(
            Organization.id == org_id,
            OrganizationMember.user_id == user.id,
            OrganizationMember.role == "owner"
        )
    )
    org_and_role = result.first()
    
    if not org_and_role:
        raise HTTPException(status_code=404, detail={
            "error": "NOT_FOUND", 
            "message": "Organization not found or only owners can delete organizations"
        })
    
    organization = org_and_role[0]
    
    # Delete organization members first (due to foreign key constraints)
    await session.execute(
        select(OrganizationMember).where(OrganizationMember.organization_id == org_id)
    )
    await session.execute(
        OrganizationMember.__table__.delete().where(OrganizationMember.organization_id == org_id)
    )
    
    # Delete the organization
    await session.delete(organization)
    await session.commit()
    
    return {"success": True, "message": "Organization deleted successfully"}