from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.security import get_current_active_user
from src.common.session import get_async_session
from src.organizations.service import get_organization, is_org_admin
from src.payments.schemas import PlanResponse
from src.payments.service import create_checkout_session, get_available_plans

router = APIRouter()


@router.get('/plans', response_model=Page[PlanResponse])
async def list_plans():
    return await get_available_plans()


@router.post('/{organization_id}/subscribe')
async def create_subscription(
    organization_id: int,
    price_id: str,
    db: AsyncSession = Depends(get_async_session),
    user=Depends(get_current_active_user),
):
    org = await get_organization(db, organization_id)
    if not org:
        raise HTTPException(404, 'Organization not found')
    if not await is_org_admin(db, org, user):
        raise HTTPException(403, 'Only organization admins can subscribe')

    checkout_url = await create_checkout_session(db, org, price_id)
    return {'checkout_url': checkout_url}
