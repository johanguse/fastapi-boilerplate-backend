from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from fastapi_pagination import paginate
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import uuid

from src.auth.models import User
from src.common.config import settings
from src.common.pagination import CustomParams, Paginated
from src.common.security import get_current_active_user
from src.common.session import get_async_session
from src.common.streaming import (
    CSVStreamer,
    DatabaseStreamer,
    JSONStreamer,
    create_csv_streaming_response,
    create_json_streaming_response,
)
from src.organizations.models import Organization
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
from src.utils.storage import delete_file_from_r2, upload_file_to_r2

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post('/', response_model=OrganizationResponse)
async def create_new_organization(
    org: OrganizationCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    created = await create_organization(db, org, current_user)
    # Avoid lazy-loading members during response serialization (async context issue)
    return {
        'id': created.id,
        'name': created.name,
        'slug': created.slug,
        'logo_url': created.logo_url,
        'description': created.description,
        'created_at': created.created_at,
        'updated_at': created.updated_at,
        'max_projects': created.max_projects,
        'active_projects': created.active_projects,
        'members': [],
    }


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
            db, query, {'user_id': current_user.id}, batch_size=500
        ):
            yield row

    generator = JSONStreamer.stream_json_array(stream_organizations())
    return create_json_streaming_response(generator, 'organizations.json')


@router.get('/export/csv')
async def export_organizations_csv(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
) -> StreamingResponse:
    """
    Export all user organizations as streaming CSV.
    Memory-efficient export for large datasets.
    """
    headers = [
        'ID',
        'Name',
        'Slug',
        'Created At',
        'Updated At',
        'Max Projects',
    ]

    async def stream_organization_rows():
        query = """
            SELECT o.id, o.name, o.slug, o.created_at, o.updated_at, o.max_projects
            FROM organizations o
            JOIN organization_members om ON o.id = om.organization_id
            WHERE om.user_id = :user_id
            ORDER BY o.created_at DESC
        """

        async for row in DatabaseStreamer.stream_query_results(
            db, query, {'user_id': current_user.id}, batch_size=500
        ):
            yield [
                str(row['id']),
                row['name'] or '',
                row['slug'] or '',
                str(row['created_at']) if row['created_at'] else '',
                str(row['updated_at']) if row['updated_at'] else '',
                str(row['max_projects']) if row['max_projects'] else '0',
            ]

    generator = CSVStreamer.stream_csv(headers, stream_organization_rows())
    return create_csv_streaming_response(generator, 'organizations.csv')


@router.post('/{organization_id}/upload-logo')
async def upload_organization_logo(
    organization_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Upload organization logo to R2 storage."""
    try:
        # Get organization and verify user has access
        from sqlalchemy import select
        result = await db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        organization = result.scalar_one_or_none()

        if not organization:
            raise HTTPException(
                status_code=404,
                detail='Organization not found',
            )

        # Verify user is a member (you may want to check for admin/owner role)
        from src.organizations.models import OrganizationMember
        member_result = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == current_user.id,
            )
        )
        member = member_result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=403,
                detail='You do not have access to this organization',
            )

        # Validate file type
        if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f'Unsupported file type. Allowed types: {", ".join(settings.ALLOWED_IMAGE_TYPES)}',
            )

        # Validate file size
        max_size = 5 * 1024 * 1024  # 5MB
        contents = await file.read(max_size + 1)
        if len(contents) > max_size:
            raise HTTPException(
                status_code=400,
                detail='File size exceeds 5MB limit',
            )

        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if file.filename else 'jpg'
        unique_filename = f'logos/{organization_id}/{uuid.uuid4()}.{file_extension}'

        # Upload to R2
        file_url = await upload_file_to_r2(
            contents,
            unique_filename,
            file.content_type,
        )

        if not file_url:
            raise HTTPException(
                status_code=500,
                detail='Failed to upload logo',
            )

        # Delete old logo if exists
        if organization.logo_url:
            try:
                old_filename = organization.logo_url.split('/')[-1]
                if old_filename.startswith('logos/'):
                    await delete_file_from_r2(old_filename)
            except Exception as e:
                logger.warning(f'Failed to delete old logo: {str(e)}')

        # Update organization's logo_url
        organization.logo_url = file_url
        await db.commit()
        await db.refresh(organization)

        return {
            'url': file_url,
            'message': 'Organization logo uploaded successfully',
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f'Error uploading organization logo: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail='Failed to upload logo',
        )


@router.delete('/{organization_id}/logo')
async def delete_organization_logo(
    organization_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Delete organization logo."""
    try:
        # Get organization and verify access
        from sqlalchemy import select
        result = await db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        organization = result.scalar_one_or_none()

        if not organization:
            raise HTTPException(
                status_code=404,
                detail='Organization not found',
            )

        # Verify user is a member
        from src.organizations.models import OrganizationMember
        member_result = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == current_user.id,
            )
        )
        member = member_result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=403,
                detail='You do not have access to this organization',
            )

        if not organization.logo_url:
            raise HTTPException(
                status_code=404,
                detail='No logo found for this organization',
            )

        # Delete from R2
        try:
            filename = organization.logo_url.split('/')[-1]
            await delete_file_from_r2(filename)
        except Exception as e:
            logger.warning(f'Failed to delete logo from R2: {str(e)}')

        # Clear logo_url from database
        organization.logo_url = None
        await db.commit()

        return {
            'message': 'Organization logo deleted successfully',
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f'Error deleting organization logo: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail='Failed to delete logo',
        )
