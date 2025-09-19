from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from fastapi_pagination import paginate
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.common.pagination import CustomParams, Paginated
from src.common.security import get_current_active_user
from src.common.session import get_async_session
from src.common.streaming import (
    JSONStreamer,
    CSVStreamer, 
    DatabaseStreamer,
    create_json_streaming_response,
    create_csv_streaming_response
)
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


@router.get('/export/json')
async def export_organizations_json(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
) -> StreamingResponse:
    """
    Export all user organizations as streaming JSON.
    Reduces memory usage by streaming results instead of loading all data at once.
    """
    async def stream_organizations():
        query = """
            SELECT o.id, o.name, o.slug, o.created_at, o.updated_at, o.max_projects
            FROM organizations o
            JOIN organization_members om ON o.id = om.organization_id
            WHERE om.user_id = :user_id
            ORDER BY o.created_at DESC
        """
        
        async for row in DatabaseStreamer.stream_query_results(
            db, query, {"user_id": current_user.id}, batch_size=500
        ):
            yield row
    
    generator = JSONStreamer.stream_json_array(stream_organizations())
    return create_json_streaming_response(generator, "organizations.json")


@router.get('/export/csv')
async def export_organizations_csv(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
) -> StreamingResponse:
    """
    Export all user organizations as streaming CSV.
    Memory-efficient export for large datasets.
    """
    headers = ["ID", "Name", "Slug", "Created At", "Updated At", "Max Projects"]
    
    async def stream_organization_rows():
        query = """
            SELECT o.id, o.name, o.slug, o.created_at, o.updated_at, o.max_projects
            FROM organizations o
            JOIN organization_members om ON o.id = om.organization_id
            WHERE om.user_id = :user_id
            ORDER BY o.created_at DESC
        """
        
        async for row in DatabaseStreamer.stream_query_results(
            db, query, {"user_id": current_user.id}, batch_size=500
        ):
            yield [
                str(row["id"]),
                row["name"] or "",
                row["slug"] or "",
                str(row["created_at"]) if row["created_at"] else "",
                str(row["updated_at"]) if row["updated_at"] else "",
                str(row["max_projects"]) if row["max_projects"] else "0"
            ]
    
    generator = CSVStreamer.stream_csv(headers, stream_organization_rows())
    return create_csv_streaming_response(generator, "organizations.csv")
