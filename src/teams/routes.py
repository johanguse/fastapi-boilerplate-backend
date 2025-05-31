from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.auth.users import current_active_user
from src.common.pagination import CustomParams, Paginated, paginate
from src.common.security import get_current_active_user
from src.common.session import get_async_session
from src.teams.schemas import (
    TeamCreate,
    TeamInvite,
    TeamMemberResponse,
    TeamResponse,
)
from src.teams.service import create_team, get_user_teams, invite_to_team

router = APIRouter()


@router.post('/', response_model=TeamResponse)
async def create_new_team(
    team: TeamCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    # Verify user has team creation privileges
    if not current_user.can_create_teams:
        raise HTTPException(403, 'Insufficient privileges')
    return await create_team(db, team, current_user)


@router.get('/', response_model=Paginated[TeamResponse])
async def get_teams(
    params: CustomParams = Depends(),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    teams = await get_user_teams(db, current_user)
    return paginate(teams, params)


@router.post('/{team_id}/invite', response_model=TeamMemberResponse)
async def invite_member(
    team_id: int,
    invite: TeamInvite,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    return await invite_to_team(db, team_id, invite, current_user)
