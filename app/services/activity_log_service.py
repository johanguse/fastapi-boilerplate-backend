from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog
from app.models.user import User


def log_activity(
    db: Session, project_id: int, user: User, action: str, ip_address: str
):
    log_entry = ActivityLog(
        project_id=project_id,
        user_id=user.id,
        action=action,
        ip_address=ip_address,
    )
    db.add(log_entry)
    db.commit()
