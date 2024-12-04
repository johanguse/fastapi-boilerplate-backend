from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


def create_project(db: Session, project: ProjectCreate):
    db_project = Project(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def get_project(db: Session, project_id: int):
    return db.query(Project).filter(Project.id == project_id).first()


def update_project(
    db: Session, project: Project, project_update: ProjectUpdate
):
    for key, value in project_update.dict(exclude_unset=True).items():
        setattr(project, key, value)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project: Project):
    db.delete(project)
    db.commit()


def get_team_projects(db: Session, team_id: int):
    return db.query(Project).filter(Project.team_id == team_id).all()
