"""Business logic for invitations and email verification."""

from datetime import UTC, datetime, timedelta
from typing import Optional

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.invitations.email_service import (
    send_email_verification,
    send_team_invitation,
)
from src.invitations.models import EmailVerificationToken, TeamInvitation
from src.organizations.models import Organization, OrganizationMember


async def create_email_verification_token(
    db: AsyncSession,
    user: User,
    base_url: str,
    background_tasks: BackgroundTasks,
) -> EmailVerificationToken:
    """Create and send email verification token."""
    # Create token
    token = EmailVerificationToken(
        user_id=user.id,
        email=user.email,
        expires_at=datetime.now(UTC) + timedelta(hours=24),
    )
    db.add(token)
    await db.commit()
    await db.refresh(token)

    # Send email
    verification_link = f'{base_url}/verify-email?token={token.token}'
    await send_email_verification(
        email=user.email,
        name=user.name or 'User',
        verification_link=verification_link,
        background_tasks=background_tasks,
    )

    return token


async def verify_email_token(db: AsyncSession, token_str: str) -> User:
    """Verify email token and mark user as verified."""
    result = await db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token == token_str
        )
    )
    token = result.scalar_one_or_none()

    if not token:
        raise HTTPException(404, 'Invalid verification token')

    if not token.is_valid():
        raise HTTPException(400, 'Token has expired or been used')

    # Mark token as used
    token.used_at = datetime.now(UTC)

    # Mark user as verified
    user_result = await db.execute(
        select(User).where(User.id == token.user_id)
    )
    user = user_result.scalar_one()
    user.is_verified = True

    await db.commit()
    return user


async def create_team_invitation(
    db: AsyncSession,
    organization_id: int,
    email: str,
    role: str,
    invited_by: User,
    message: Optional[str],
    base_url: str,
    background_tasks: BackgroundTasks,
) -> TeamInvitation:
    """Create and send team invitation."""
    # Check if user already member
    existing_user = await db.execute(select(User).where(User.email == email))
    user = existing_user.scalar_one_or_none()

    if user:
        existing_member = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user.id,
            )
        )
        if existing_member.scalar_one_or_none():
            raise HTTPException(400, 'User is already a member')

    # Check for existing pending invitation
    existing_invite = await db.execute(
        select(TeamInvitation).where(
            TeamInvitation.organization_id == organization_id,
            TeamInvitation.email == email,
            TeamInvitation.status == 'pending',
        )
    )
    if existing_invite.scalar_one_or_none():
        raise HTTPException(400, 'Invitation already sent')

    # Get organization
    org_result = await db.execute(
        select(Organization).where(Organization.id == organization_id)
    )
    organization = org_result.scalar_one()

    # Create invitation
    invitation = TeamInvitation(
        organization_id=organization_id,
        invited_by_id=invited_by.id,
        email=email,
        role=role,
        message=message,
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    # Send email
    invitation_link = f'{base_url}/accept-invitation?token={invitation.token}'
    await send_team_invitation(
        email=email,
        invited_by_name=invited_by.name or invited_by.email,
        organization_name=organization.name,
        invitation_link=invitation_link,
        role=role,
        message=message,
        background_tasks=background_tasks,
    )

    return invitation


async def accept_team_invitation(
    db: AsyncSession, token: str, user: User
) -> OrganizationMember:
    """Accept team invitation and add user to organization."""
    result = await db.execute(
        select(TeamInvitation).where(TeamInvitation.token == token)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(404, 'Invalid invitation')

    if not invitation.is_pending():
        raise HTTPException(400, 'Invitation is no longer valid')

    if invitation.email != user.email:
        raise HTTPException(403, 'This invitation is for a different email')

    # Add user to organization
    member = OrganizationMember(
        organization_id=invitation.organization_id,
        user_id=user.id,
        role=invitation.role,
    )
    db.add(member)

    # Update invitation
    invitation.status = 'accepted'
    invitation.accepted_at = datetime.now(UTC)
    invitation.accepted_by_id = user.id

    await db.commit()
    await db.refresh(member)

    return member


async def decline_team_invitation(
    db: AsyncSession, token: str, user: Optional[User] = None
) -> TeamInvitation:
    """Decline team invitation."""
    result = await db.execute(
        select(TeamInvitation).where(TeamInvitation.token == token)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(404, 'Invalid invitation')

    if not invitation.is_pending():
        raise HTTPException(400, 'Invitation is no longer valid')

    if user and invitation.email != user.email:
        raise HTTPException(403, 'This invitation is for a different email')

    # Update invitation
    invitation.status = 'declined'
    invitation.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(invitation)

    return invitation


async def cancel_team_invitation(
    db: AsyncSession, invitation_id: int, organization_id: int
) -> TeamInvitation:
    """Cancel a pending invitation."""
    result = await db.execute(
        select(TeamInvitation).where(
            TeamInvitation.id == invitation_id,
            TeamInvitation.organization_id == organization_id,
        )
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(404, 'Invitation not found')

    if invitation.status != 'pending':
        raise HTTPException(400, 'Only pending invitations can be cancelled')

    invitation.status = 'expired'
    invitation.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(invitation)

    return invitation
