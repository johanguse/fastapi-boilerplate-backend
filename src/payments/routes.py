from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.users import current_active_user
from src.common.session import get_async_session
from src.payments.schemas import PlanResponse
from src.payments.service import create_checkout_session, get_available_plans
from src.teams.service import get_team, is_team_owner

router = APIRouter()


@router.get('/plans', response_model=Page[PlanResponse])
async def list_plans():
    return await get_available_plans()


@router.post('/{team_id}/subscribe')
async def create_subscription(
    team_id: int,
    price_id: str,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(current_active_user),
):
    team = await get_team(db, team_id)
    if not await is_team_owner(db, team, user):
        raise HTTPException(403, 'Only team owners can subscribe')

    checkout_url = await create_checkout_session(db, team, price_id)
    return {'checkout_url': checkout_url}
