from fastapi import APIRouter, Depends
from fastapi_pagination import paginate
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.common.pagination import CustomParams, Paginated
from src.common.security import get_current_active_user
from src.common.session import get_async_session
from src.organizations.schemas import (
    OrganizationCreate,
    OrganizationInvite,
    OrganizationMemberResponse,
    OrganizationResponse,
)
from src.organizations.service import (
    create_organization,
    get_user_organizations,
    invite_to_organization,
)

router = APIRouter()


@router.post('/', response_model=OrganizationResponse)
async def create_new_organization(
    org: OrganizationCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    return await create_organization(db, org, current_user)


@router.get('/', response_model=Paginated[OrganizationResponse])
async def get_organizations(
    params: CustomParams = Depends(),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    orgs = await get_user_organizations(db, current_user)
    return paginate(orgs, params)


@router.post(
    '/{organization_id}/invite', response_model=OrganizationMemberResponse
)
async def invite_member(
    organization_id: int,
    invite: OrganizationInvite,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    return await invite_to_organization(
        db, organization_id, invite, current_user
    )
