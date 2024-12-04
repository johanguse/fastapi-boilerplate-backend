from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(length=320), unique=True, index=True, nullable=False)
    hashed_password = Column(String(length=1024), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    name = Column(String(100))
    role = Column(String(20), nullable=False, default='member')
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at = Column(DateTime(timezone=True))

    team_members = relationship('TeamMember', back_populates='user')
    invitations_sent = relationship('Invitation', back_populates='invited_by')
    activity_logs = relationship('ActivityLog', back_populates='user')
    training_data = relationship('TrainingData', back_populates='user')
    blog_posts = relationship('BlogPost', back_populates='user')
