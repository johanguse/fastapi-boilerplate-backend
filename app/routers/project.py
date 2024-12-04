from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import get_current_active_user
from app.models.user import User as UserModel
from app.schemas.project import (
    Project,
    ProjectCreate,
    ProjectUpdate,
)
from app.services import project_service

router = APIRouter()


@router.post('/', response_model=Project)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: UserModel = Depends(get_current_active_user),
):
    return await project_service.create_project(db, project, current_user)


@router.get('/', response_model=list[Project])
async def get_projects(
    db: AsyncSession = Depends(get_async_session),
    current_user: UserModel = Depends(get_current_active_user),
):
    return await project_service.get_projects(db, current_user)


@router.get('/{project_id}', response_model=Project)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: UserModel = Depends(get_current_active_user),
):
    project = await project_service.get_project(db, project_id, current_user)
    if project is None:
        raise HTTPException(status_code=404, detail='Project not found')
    return project


@router.put('/{project_id}', response_model=Project)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: UserModel = Depends(get_current_active_user),
):
    updated_project = await project_service.update_project(
        db, project_id, project_update, current_user
    )
    if updated_project is None:
        raise HTTPException(status_code=404, detail='Project not found')
    return updated_project


@router.delete('/{project_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: UserModel = Depends(get_current_active_user),
):
    deleted = await project_service.delete_project(
        db, project_id, current_user
    )
    if not deleted:
        raise HTTPException(status_code=404, detail='Project not found')
