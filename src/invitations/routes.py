"""API routes for invitations and email verification."""

from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.common.rate_limiter import EMAIL_LIMIT, ORG_LIMIT, limiter
from src.common.security import get_current_active_user, get_current_user
from src.common.session import get_async_session
from src.invitations.models import TeamInvitation
from src.invitations.schemas import (
    InvitationListResponse,
    TeamInvitationCreate,
    TeamInvitationResponse,
)
from src.invitations.service import (
    accept_team_invitation,
    cancel_team_invitation,
    create_email_verification_token,
    create_team_invitation,
    decline_team_invitation,
    verify_email_token,
)
from src.organizations.service import get_organization, is_org_admin

router = APIRouter()


@router.post('/verify-email/resend')
@limiter.limit(EMAIL_LIMIT)  # 10 requests per hour
async def resend_verification_email(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Resend email verification."""
    if current_user.is_verified:
        raise HTTPException(400, 'Email already verified')
    
    base_url = str(request.base_url).rstrip('/')
    await create_email_verification_token(
        db, current_user, base_url, background_tasks
    )
    
    return {'message': 'Verification email sent'}


@router.post('/verify-email/{token}')
@limiter.limit(EMAIL_LIMIT)  # 10 requests per hour
async def verify_email(
    request: Request,  # Required for rate limiter
    token: str,
    db: AsyncSession = Depends(get_async_session),
):
    """Verify email with token."""
    user = await verify_email_token(db, token)
    return {'message': 'Email verified successfully', 'email': user.email}


@router.post(
    '/organizations/{organization_id}/invitations',
    response_model=TeamInvitationResponse,
)
@limiter.limit(EMAIL_LIMIT)  # 10 requests per hour - prevent invitation spam
async def invite_team_member(
    organization_id: int,
    invitation_data: TeamInvitationCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Invite a new team member to organization."""
    organization = await get_organization(db, organization_id)
    if not organization:
        raise HTTPException(404, 'Organization not found')
    
    if not await is_org_admin(db, organization, current_user):
        raise HTTPException(403, 'Only admins can invite team members')
    
    base_url = str(request.base_url).rstrip('/')
    invitation = await create_team_invitation(
        db,
        organization_id,
        invitation_data.email,
        invitation_data.role,
        current_user,
        invitation_data.message,
        base_url,
        background_tasks,
    )
    
    return invitation


@router.post('/invitations/{token}/accept')
@limiter.limit(ORG_LIMIT)  # 30 requests per minute
async def accept_invitation(
    request: Request,  # Required for rate limiter
    token: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Accept team invitation."""
    member = await accept_team_invitation(db, token, current_user)
    return {
        'message': 'Invitation accepted',
        'organization_id': member.organization_id,
    }


@router.post('/invitations/{token}/decline')
@limiter.limit(ORG_LIMIT)  # 30 requests per minute
async def decline_invitation(
    request: Request,  # Required for rate limiter
    token: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Decline team invitation."""
    invitation = await decline_team_invitation(db, token, current_user)
    return {'message': 'Invitation declined'}


@router.get(
    '/organizations/{organization_id}/invitations',
    response_model=List[InvitationListResponse],
)
async def list_invitations(
    organization_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """List all pending invitations for an organization."""
    organization = await get_organization(db, organization_id)
    if not organization:
        raise HTTPException(404, 'Organization not found')
    
    if not await is_org_admin(db, organization, current_user):
        raise HTTPException(403, 'Only admins can view invitations')
    
    result = await db.execute(
        select(TeamInvitation)
        .where(
            TeamInvitation.organization_id == organization_id,
            TeamInvitation.status == 'pending',
        )
        .order_by(TeamInvitation.created_at.desc())
    )
    invitations = result.scalars().all()
    
    # Format response
    response = []
    for inv in invitations:
        response.append(
            InvitationListResponse(
                id=inv.id,
                email=inv.email,
                role=inv.role,
                status=inv.status,
                message=inv.message,
                invited_by_name=inv.invited_by.name or inv.invited_by.email,
                expires_at=inv.expires_at,
                created_at=inv.created_at,
            )
        )
    
    return response


@router.delete('/organizations/{organization_id}/invitations/{invitation_id}')
@limiter.limit(ORG_LIMIT)  # 30 requests per minute
async def cancel_invitation(
    request: Request,  # Required for rate limiter
    organization_id: int,
    invitation_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Cancel a pending invitation."""
    organization = await get_organization(db, organization_id)
    if not organization:
        raise HTTPException(404, 'Organization not found')
    
    if not await is_org_admin(db, organization, current_user):
        raise HTTPException(403, 'Only admins can cancel invitations')
    
    await cancel_team_invitation(db, invitation_id, organization_id)
    return {'message': 'Invitation cancelled'}
