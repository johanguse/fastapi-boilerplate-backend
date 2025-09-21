from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from fastapi_pagination import paginate
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.common.exceptions import NotFoundError, PermissionError
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
from src.projects.schemas import Project, ProjectCreate, ProjectUpdate
from src.projects.service import (
    create_project,
    delete_project,
    get_project,
    get_projects,
    update_project,
)

router = APIRouter()


@router.post('/', response_model=Project)
async def create_new_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    return await create_project(db, project, current_user)


@router.get('/', response_model=Paginated[Project])
async def list_projects(
    params: CustomParams = Depends(),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    projects = await get_projects(db, current_user)
    return paginate(projects, params)


@router.get('/{project_id}', response_model=Project)
async def get_project_by_id(
    project_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    project = await get_project(db, project_id, current_user)
    if project is None:
        raise NotFoundError(detail='Project not found')
    return project


@router.put('/{project_id}', response_model=Project)
async def update_project_by_id(
    project_id: int,
    project_update: ProjectUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await update_project(
            db, project_id, project_update, current_user
        )
    except PermissionError as e:
        raise e
    except NotFoundError as e:
        raise e


@router.delete('/{project_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_by_id(
    project_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    try:
        await delete_project(db, project_id, current_user)
    except NotFoundError as e:
        raise e
    except PermissionError as e:
        raise e


@router.get('/export/json')
async def export_projects_json(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
) -> StreamingResponse:
    """
    Export all user projects as streaming JSON.
    Memory-efficient export for large project datasets.
    """

    async def stream_projects():
        query = """
            SELECT p.id, p.name, p.description, p.organization_id,
                   p.created_at, p.updated_at, o.name as organization_name
            FROM projects p
            JOIN organizations o ON p.organization_id = o.id
            JOIN organization_members om ON o.id = om.organization_id
            WHERE om.user_id = :user_id
            ORDER BY p.created_at DESC
        """

        async for row in DatabaseStreamer.stream_query_results(
            db, query, {'user_id': current_user.id}, batch_size=500
        ):
            yield row

    generator = JSONStreamer.stream_json_array(stream_projects())
    return create_json_streaming_response(generator, 'projects.json')


@router.get('/export/csv')
async def export_projects_csv(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
) -> StreamingResponse:
    """
    Export all user projects as streaming CSV.
    Efficient export for spreadsheet analysis.
    """
    headers = [
        'ID',
        'Name',
        'Description',
        'Organization',
        'Created At',
        'Updated At',
    ]

    async def stream_project_rows():
        query = """
            SELECT p.id, p.name, p.description, p.organization_id,
                   p.created_at, p.updated_at, o.name as organization_name
            FROM projects p
            JOIN organizations o ON p.organization_id = o.id
            JOIN organization_members om ON o.id = om.organization_id
            WHERE om.user_id = :user_id
            ORDER BY p.created_at DESC
        """

        async for row in DatabaseStreamer.stream_query_results(
            db, query, {'user_id': current_user.id}, batch_size=500
        ):
            yield [
                str(row['id']),
                row['name'] or '',
                row['description'] or '',
                row['organization_name'] or '',
                str(row['created_at']) if row['created_at'] else '',
                str(row['updated_at']) if row['updated_at'] else '',
            ]

    generator = CSVStreamer.stream_csv(headers, stream_project_rows())
    return create_csv_streaming_response(generator, 'projects.csv')
