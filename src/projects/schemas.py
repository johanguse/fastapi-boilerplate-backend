from typing import Optional

from src.common.schemas import BaseSchema, TimestampMixin


class ProjectBase(BaseSchema):
    """Base schema for Project"""

    name: str
    description: Optional[str] = None

    model_config = {
        'json_schema_extra': {
            'example': {
                'name': 'My Project',
                'description': 'A sample project',
            }
        }
    }


class ProjectCreate(ProjectBase):
    """Schema for creating a Project"""

    team_id: int


class ProjectUpdate(ProjectBase):
    """Schema for updating a Project"""

    pass


class Project(ProjectBase, TimestampMixin):
    """Schema for Project response"""

    id: int
    team_id: int
