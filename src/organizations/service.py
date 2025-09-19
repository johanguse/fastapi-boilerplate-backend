from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.activity_log import service as activity_log
from src.auth.models import User
from src.common.config import settings
from src.common.monitoring import time_operation
from src.organizations.models import (
    Organization,
    OrganizationInvitation,
    OrganizationMember,
)
from src.organizations.schemas import OrganizationCreate, OrganizationInvite
from src.utils.email import send_invitation_email


@time_operation("create_organization")
async def create_organization(
    db: AsyncSession, org: OrganizationCreate, current_user: User
) -> Organization:
    if not current_user.is_active:
        raise HTTPException(403, "Inactive users can't create organizations")

    existing = await db.execute(
        select(Organization).filter(Organization.name == org.name)
    )
    if existing.scalar():
        raise HTTPException(409, 'Organization name already exists')

    # Enforce per-user limit, reuse max_teams as max_organizations
    result = await db.execute(
        select(Organization)
        .join(OrganizationMember)
        .filter(OrganizationMember.user_id == current_user.id)
    )
    user_orgs = result.scalars().all()
    if len(user_orgs) >= current_user.max_teams:
        raise HTTPException(403, 'Organization creation limit reached')

    db_org = Organization(name=org.name, slug=org.slug, logo_url=org.logo_url)
    db.add(db_org)
    await db.commit()
    await db.refresh(db_org)

    # Add the creator as an admin of the organization
    db_member = OrganizationMember(
        organization_id=db_org.id, user_id=current_user.id, role='admin'
    )
    db.add(db_member)
    await db.commit()

    await activity_log.log_activity(
        db,
        {
            'action': 'org_created',
            'description': f"Organization '{org.name}' created",
            'user': {'id': current_user.id},
            'team_id': db_org.id,  # kept for backward compat in activity service
            'project_id': 0,  # System project
            'action_type': 'organization',
        },
    )
    return db_org


async def get_organization(
    db: AsyncSession, organization_id: int
) -> Organization:
    result = await db.execute(
        select(Organization).filter(Organization.id == organization_id)
    )
    return result.scalar_one_or_none()


@time_operation("get_user_organizations")
async def get_user_organizations(
    db: AsyncSession, user: User
) -> list[Organization]:
    result = await db.execute(
        select(Organization)
        .join(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
    )
    return result.scalars().all()


async def is_org_admin(
    db: AsyncSession, org: Organization, user: User
) -> bool:
    result = await db.execute(
        select(OrganizationMember).filter(
            OrganizationMember.organization_id == org.id,
            OrganizationMember.user_id == user.id,
            OrganizationMember.role == 'admin',
        )
    )
    return result.scalar_one_or_none() is not None


async def is_org_member(
    db: AsyncSession, organization_id: int, user: User
) -> bool:
    result = await db.execute(
        select(OrganizationMember).filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user.id,
        )
    )
    return result.scalar_one_or_none() is not None


@time_operation("invite_to_organization")
async def invite_to_organization(
    db: AsyncSession,
    organization_id: int,
    invite: OrganizationInvite,
    current_user: User,
) -> OrganizationInvitation:
    org = await get_organization(db, organization_id)
    if not org:
        raise HTTPException(404, 'Organization not found')

    if not await is_org_admin(db, org, current_user):
        raise HTTPException(403, 'Admin privileges required')

    invitation = OrganizationInvitation(
        organization_id=organization_id,
        email=invite.email,
        role=invite.role,
        invited_by_id=current_user.id,
    )
    db.add(invitation)
    await db.commit()

    # Send invitation email
    await send_invitation_email(
        invite.email,
        current_user.email,
        org.name,
        settings.FRONTEND_URL,
    )

    await activity_log.log_activity(
        db,
        {
            'action': 'org_invite_sent',
            'description': f'Invited {invite.email} to organization {org.name}',
            'user': {'id': current_user.id},
            'team_id': org.id,
            'project_id': 0,
            'action_type': 'organization',
            'metadata': {'invite_email': invite.email, 'role': invite.role},
        },
    )
    return invitation
