from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.common.exceptions import NotFoundError, PermissionError
from src.organizations.service import get_organization, is_org_member
from src.projects.models import Project
from src.projects.schemas import ProjectCreate, ProjectUpdate

MAX_PRO_PROJECTS = 5
MAX_BUSINESS_PROJECTS = 20


async def create_project(
    db: AsyncSession, project: ProjectCreate, current_user: User
) -> Project:
    """Create a new project"""
    # Verify organization membership
    if not await is_org_member(db, project.organization_id, current_user):
        raise PermissionError('User is not a member of this organization')

    team = await get_organization(db, project.organization_id)

    if team.plan_name == 'starter' and team.active_projects >= 1:
        raise HTTPException(403, 'Starter plan limited to 1 project')

    if team.plan_name == 'pro' and team.active_projects >= MAX_PRO_PROJECTS:
        raise HTTPException(403, 'Pro plan limited to 5 projects')

    if (
        team.plan_name == 'business'
        and team.active_projects >= MAX_BUSINESS_PROJECTS
    ):
        raise HTTPException(403, 'Business plan limited to 20 projects')

    # Create project
    db_project = Project(
        name=project.name,
        description=project.description,
        organization_id=project.organization_id,
    )
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)

    team.active_projects += 1
    await db.commit()

    return db_project


async def get_project(
    db: AsyncSession, project_id: int, current_user: User
) -> Project:
    """Get a project by ID"""
    result = await db.execute(select(Project).filter(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise NotFoundError('Project not found')

    # Verify organization membership
    if not await is_org_member(db, project.organization_id, current_user):
        raise PermissionError('User is not a member of this organization')

    return project


async def get_projects(db: AsyncSession, current_user: User) -> list[Project]:
    """Get all projects for teams the user is a member of"""
    from src.organizations.models import OrganizationMember

    result = await db.execute(
        select(Project)
        .join(Project.organization)
        .join(
            OrganizationMember,
            OrganizationMember.organization_id == Project.organization_id,
        )
        .filter(OrganizationMember.user_id == current_user.id)
    )
    return result.scalars().all()


async def update_project(
    db: AsyncSession,
    project_id: int,
    project_update: ProjectUpdate,
    current_user: User,
) -> Project:
    """Update a project"""
    project = await get_project(db, project_id, current_user)

    # Update fields
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def delete_project(
    db: AsyncSession, project_id: int, current_user: User
) -> None:
    """Delete a project"""
    project = await get_project(db, project_id, current_user)
    await db.delete(project)
    await db.commit()
