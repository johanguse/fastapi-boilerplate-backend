from typing import Optional

from fastapi import HTTPException
from fastapi_pagination import paginate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.activity_log import service as activity_log
from src.auth.models import User
from src.common.config import settings
from src.common.pagination import CustomParams, Paginated
from src.teams.models import Invitation, Team, TeamMember  # Use ORM models
from src.teams.schemas import TeamCreate, TeamInvite
from src.utils.email import send_invitation_email


async def create_team(
    db: AsyncSession, team: TeamCreate, current_user: User
) -> Team:
    if not current_user.is_active:
        raise HTTPException(403, "Inactive users can't create teams")

    existing = await db.execute(select(Team).filter(Team.name == team.name))
    if existing.scalar():
        raise HTTPException(409, 'Team name already exists')

    user_teams = await get_user_teams(db, current_user)
    if len(user_teams) >= current_user.max_teams:
        raise HTTPException(403, 'Team creation limit reached')

    db_team = Team(name=team.name)
    db.add(db_team)
    await db.commit()
    await db.refresh(db_team)

    # Add the creator as an admin of the team
    db_team_member = TeamMember(
        team_id=db_team.id, user_id=current_user.id, role='admin'
    )
    db.add(db_team_member)
    await db.commit()

    await activity_log.log_activity(
        db,
        action='team_created',
        description=f"Team '{team.name}' created",
        user=current_user,
        team_id=db_team.id,
        project_id=0,  # System project
        action_type='team',
    )
    return db_team


async def get_team(db: AsyncSession, team_id: int) -> Team:
    result = await db.execute(select(Team).filter(Team.id == team_id))
    return result.scalar_one_or_none()


async def get_user_teams(
    db: AsyncSession, user: User, params: CustomParams
) -> Paginated[Team]:
    result = await db.execute(
        select(Team).join(TeamMember).filter(TeamMember.user_id == user.id)
    )
    teams = result.scalars().all()
    return paginate(teams, params)


async def is_team_admin(db: AsyncSession, team: Team, user: User) -> bool:
    result = await db.execute(
        select(TeamMember).filter(
            TeamMember.team_id == team.id,
            TeamMember.user_id == user.id,
            TeamMember.role == 'admin',
        )
    )
    return result.scalar_one_or_none() is not None


async def is_team_member(db: AsyncSession, team_id: int, user: User) -> bool:
    result = await db.execute(
        select(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user.id,
        )
    )
    return result.scalar_one_or_none() is not None


async def is_team_owner(db: AsyncSession, team: Team, user: User) -> bool:
    result = await db.execute(
        select(TeamMember).filter(
            TeamMember.team_id == team.id,
            TeamMember.user_id == user.id,
            TeamMember.role == 'owner',
        )
    )
    return result.scalar_one_or_none() is not None


async def invite_to_team(
    db: AsyncSession,
    team_id: int,
    invite: TeamInvite,
    current_user: User,
) -> TeamMember:
    team = await get_team(db, team_id)
    if not team:
        raise HTTPException(404, 'Team not found')

    if not await is_team_admin(db, team, current_user):
        raise HTTPException(403, 'Admin privileges required')

    invitation = Invitation(
        team_id=team_id,
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
        team.name,
        settings.FRONTEND_URL,
    )

    await activity_log.log_activity(
        db,
        action='team_invite_sent',
        description=f'Invited {invite.email} to team {team.name}',
        user=current_user,
        team_id=team.id,
        project_id=0,
        action_type='team',
        metadata={'invite_email': invite.email, 'role': invite.role},
    )
    return invitation


async def delete_team(db: AsyncSession, team_id: int, current_user: User):
    team = await get_team(db, team_id)
    if not await is_team_owner(db, team, current_user):
        raise HTTPException(403, 'Only team owners can delete teams')


async def get_team_by_stripe_id(
    db: AsyncSession, stripe_customer_id: str
) -> Optional[Team]:
    result = await db.execute(
        select(Team).filter(Team.stripe_customer_id == stripe_customer_id)
    )
    return result.scalar_one_or_none()
