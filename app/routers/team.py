from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import get_current_active_user
from app.models.user import User as UserModel
from app.schemas.team import (
    TeamCreate,
    TeamInvite,
    TeamMemberResponse,
    TeamResponse,
)
from app.services import team_service

router = APIRouter()


@router.post('/', response_model=TeamResponse)
async def create_team(
    team: TeamCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: UserModel = Depends(get_current_active_user),
):
    return await team_service.create_team(db, team, current_user)


@router.get('/', response_model=list[TeamResponse])
async def get_user_teams(
    db: AsyncSession = Depends(get_async_session),
    current_user: UserModel = Depends(get_current_active_user),
):
    return await team_service.get_user_teams(db, current_user)


@router.post('/{team_id}/invite', response_model=TeamMemberResponse)
async def invite_to_team(
    team_id: int,
    invite: TeamInvite,
    db: AsyncSession = Depends(get_async_session),
    current_user: UserModel = Depends(get_current_active_user),
):
    return await team_service.invite_to_team(db, team_id, invite, current_user)


@router.get('/{team_id}/members', response_model=list[TeamMemberResponse])
async def get_team_members(
    team_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: UserModel = Depends(get_current_active_user),
):
    return await team_service.get_team_members(db, team_id, current_user)
