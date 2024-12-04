import uuid

from sqlalchemy.orm import Session

from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.training import ModelStatus, TrainingData
from app.models.user import User
from app.schemas.training import TrainingDataCreate
from app.services import activity_log_service
from app.utils.storage import upload_file_to_r2


async def store_training_data(
    db: Session,
    data: TrainingDataCreate,
    file_content: bytes,
    user: User,
    ip_address: str,
):
    # Generate a unique file name
    file_extension = data.file_name.split('.')[-1]
    unique_filename = f'{uuid.uuid4()}.{file_extension}'

    # Upload file to R2
    file_url = upload_file_to_r2(
        file_content, unique_filename, data.content_type
    )

    if not file_url:
        raise ValueError('Failed to upload file to R2')

    # Store metadata in database
    db_data = TrainingData(
        project_id=data.project_id,
        file_url=file_url,
        status=ModelStatus.TRAINING,
    )
    db.add(db_data)
    db.commit()
    db.refresh(db_data)

    # Log the activity
    activity_log_service.log_activity(
        db,
        data.project_id,
        user,
        f'Uploaded training data: {unique_filename}',
        ip_address,
    )

    return db_data


async def get_model_status(
    db: Session, project_id: int, user: User, ip_address: str
):
    training_data = (
        db.query(TrainingData)
        .filter(TrainingData.project_id == project_id)
        .order_by(TrainingData.created_at.desc())
        .first()
    )
    if not training_data:
        raise ValueError('No training data found for this project')

    # Log the activity
    activity_log_service.log_activity(
        db,
        project_id,
        user,
        f'Checked model status: {training_data.status.value}',
        ip_address,
    )

    return training_data.status.value, training_data.file_url


def is_team_member(db: Session, team: Team, user: User) -> bool:
    team_member = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team.id, TeamMember.user_id == user.id)
        .first()
    )
    return team_member is not None
