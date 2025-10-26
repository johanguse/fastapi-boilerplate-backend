"""Organization management routes."""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.session import get_async_session
from src.organizations.models import Organization, OrganizationMember
from src.organizations.schemas import OrganizationCreate
from src.organizations.service import (
    create_organization as create_organization_service,
)

from .cookie_utils import set_auth_cookie
from .request_utils import get_user_from_request

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get('/auth/organization')
async def list_organizations(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
) -> List[Dict[str, Any]]:
    """List user's organizations."""
    user = await get_user_from_request(request, session)
    result = await session.execute(
        select(Organization)
        .join(OrganizationMember)
        .where(OrganizationMember.user_id == user.id)  # type: ignore[arg-type]
    )
    organizations: List[Organization] = result.scalars().all()
    orgs = []
    for org in organizations:
        orgs.append({
            'id': str(org.id),
            'name': org.name,
            'slug': org.slug
            or (org.name or '').lower().replace(' ', '-')[:48],
            'logo': org.logo_url,
            'metadata': None,
            'createdAt': org.created_at.isoformat()
            if getattr(org, 'created_at', None)
            else None,
        })
    return orgs


@router.get('/auth/organization/list')
async def list_organizations_compat(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
) -> List[Dict[str, Any]]:
    """Better Auth plugin expects /auth/organization/list."""
    return await list_organizations(request, session)


@router.post('/auth/organization')
async def create_organization(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """Create organization."""
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    name = (payload or {}).get('name')
    slug = (payload or {}).get('slug')
    if not name:
        raise HTTPException(
            status_code=400,
            detail={
                'error': 'INVALID_INPUT',
                'message': 'name is required',
            },
        )

    user = await get_user_from_request(request, session)
    db_org = await create_organization_service(
        session, OrganizationCreate(name=name, slug=slug), user
    )

    org = {
        'id': str(db_org.id),
        'name': db_org.name,
        'slug': db_org.slug
        or (db_org.name or '').lower().replace(' ', '-')[:48],
        'logo': db_org.logo_url,
        'metadata': None,
        'createdAt': db_org.created_at.isoformat()
        if getattr(db_org, 'created_at', None)
        else None,
    }
    set_auth_cookie(response, key='ba_active_org', value=org['id'], path='/')
    return org


@router.post('/auth/organization/create')
async def create_organization_alias(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """Alias for /auth/organization."""
    return await create_organization(request, response, session)


@router.post('/auth/organization/set-active')
async def set_active_organization(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """Set the active organization."""
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    org_id = (payload or {}).get('organizationId')
    if not org_id:
        raise HTTPException(
            status_code=400,
            detail={
                'error': 'INVALID_INPUT',
                'message': 'organizationId is required',
            },
        )

    user = await get_user_from_request(request, session)
    try:
        org_id_int = int(str(org_id))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={
                'error': 'INVALID_INPUT',
                'message': 'organizationId must be an integer',
            },
        )

    result = await session.execute(
        select(Organization.id)
        .join(OrganizationMember)
        .where(
            Organization.id == org_id_int,  # type: ignore[arg-type]
            OrganizationMember.user_id == user.id,  # type: ignore[arg-type]
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=404,
            detail={
                'error': 'NOT_FOUND',
                'message': 'Organization not found',
            },
        )

    set_auth_cookie(response, key='ba_active_org', value=str(org_id_int), path='/')
    return {'success': True, 'activeOrganizationId': str(org_id_int)}


@router.get('/auth/organization/{org_id}')
async def get_organization(
    org_id: int,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """Get a specific organization."""
    user = await get_user_from_request(request, session)

    result = await session.execute(
        select(Organization)
        .join(OrganizationMember)
        .where(
            Organization.id == org_id, OrganizationMember.user_id == user.id  # type: ignore[arg-type]
        )
    )
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=404,
            detail={'error': 'NOT_FOUND', 'message': 'Organization not found'},
        )

    return {
        'id': str(organization.id),
        'name': organization.name,
        'slug': organization.slug
        or (organization.name or '').lower().replace(' ', '-')[:48],
        'logo': organization.logo_url,
        'metadata': None,
        'createdAt': organization.created_at.isoformat()
        if getattr(organization, 'created_at', None)
        else None,
    }


@router.put('/auth/organization/{org_id}')
async def update_organization(
    org_id: int,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """Update organization."""
    user = await get_user_from_request(request, session)

    try:
        payload = await request.json()
    except Exception:
        payload = {}

    result = await session.execute(
        select(Organization, OrganizationMember.role)
        .join(OrganizationMember)
        .where(
            Organization.id == org_id,  # type: ignore[arg-type]
            OrganizationMember.user_id == user.id,  # type: ignore[arg-type]
            OrganizationMember.role.in_(['owner', 'admin']),  # type: ignore[arg-type]
        )
    )
    org_and_role = result.first()

    if not org_and_role:
        raise HTTPException(
            status_code=404,
            detail={
                'error': 'NOT_FOUND',
                'message': 'Organization not found or insufficient permissions',
            },
        )

    organization = org_and_role[0]

    if 'name' in payload:
        organization.name = payload['name']
    if 'slug' in payload:
        organization.slug = payload['slug']
    if 'logo' in payload:
        organization.logo_url = payload['logo']

    await session.commit()
    await session.refresh(organization)

    return {
        'id': str(organization.id),
        'name': organization.name,
        'slug': organization.slug
        or (organization.name or '').lower().replace(' ', '-')[:48],
        'logo': organization.logo_url,
        'metadata': None,
        'createdAt': organization.created_at.isoformat()
        if getattr(organization, 'created_at', None)
        else None,
    }


@router.delete('/auth/organization/{org_id}')
async def delete_organization(
    org_id: int,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """Delete organization."""
    user = await get_user_from_request(request, session)

    result = await session.execute(
        select(Organization, OrganizationMember.role)
        .join(OrganizationMember)
        .where(
            Organization.id == org_id,  # type: ignore[arg-type]
            OrganizationMember.user_id == user.id,  # type: ignore[arg-type]
            OrganizationMember.role == 'owner',  # type: ignore[arg-type]
        )
    )
    org_and_role = result.first()

    if not org_and_role:
        raise HTTPException(
            status_code=404,
            detail={
                'error': 'NOT_FOUND',
                'message': 'Organization not found or only owners can delete organizations',
            },
        )

    organization = org_and_role[0]

    await session.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id  # type: ignore[arg-type]
        )
    )
    await session.execute(
        OrganizationMember.__table__.delete().where(
            OrganizationMember.organization_id == org_id  # type: ignore[arg-type]
        )
    )

    await session.delete(organization)
    await session.commit()

    return {'success': True, 'message': 'Organization deleted successfully'}


# Stub endpoints for Better Auth compatibility
@router.get('/auth/organization/list-members')
async def list_members_endpoint(request: Request) -> Dict[str, List[Any]]:
    """List organization members - stub for compatibility."""
    return {'members': []}


@router.post('/auth/organization/remove-member')
async def remove_member_endpoint(request: Request) -> Dict[str, bool]:
    """Remove organization member - stub for compatibility."""
    return {'success': True}


@router.post('/auth/organization/update-member-role')
async def update_member_role_endpoint(request: Request) -> Dict[str, bool]:
    """Update member role - stub for compatibility."""
    return {'success': True}


@router.get('/auth/organization/list-invitations')
async def list_invitations_endpoint(request: Request) -> List[Any]:
    """List invitations - stub for compatibility."""
    return []


@router.get('/auth/organization/list-user-invitations')
async def list_user_invitations_endpoint(request: Request) -> List[Any]:
    """List user invitations - stub for compatibility."""
    return []


@router.post('/auth/organization/invite-member')
async def invite_member_endpoint(request: Request) -> Dict[str, bool]:
    """Invite member - stub for compatibility."""
    return {'success': True}


@router.post('/auth/organization/accept-invitation')
async def accept_invitation_endpoint(request: Request) -> Dict[str, bool]:
    """Accept invitation - stub for compatibility."""
    return {'success': True}


@router.post('/auth/organization/reject-invitation')
async def reject_invitation_endpoint(request: Request) -> Dict[str, bool]:
    """Reject invitation - stub for compatibility."""
    return {'success': True}


@router.post('/auth/organization/cancel-invitation')
async def cancel_invitation_endpoint(request: Request) -> Dict[str, bool]:
    """Cancel invitation - stub for compatibility."""
    return {'success': True}
