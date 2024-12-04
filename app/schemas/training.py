from datetime import datetime

from pydantic import BaseModel

from app.models.training import ModelStatus


class TrainingDataCreate(BaseModel):
    project_id: int
    file_name: str
    content_type: str


class TrainingDataInDB(BaseModel):
    id: int
    project_id: int
    file_url: str
    status: ModelStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TrainingResponse(BaseModel):
    status: str
    file_url: str
