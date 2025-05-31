from fastapi import APIRouter, Depends, status
from fastapi_pagination import paginate
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.common.exceptions import NotFoundError, PermissionError
from src.common.pagination import CustomParams, Paginated
from src.common.security import get_current_active_user
from src.common.session import get_async_session
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
