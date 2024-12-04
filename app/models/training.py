import enum

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ModelStatus(enum.Enum):
    TRAINING = 'training'
    COMPLETED = 'completed'
    FAILED = 'failed'


class TrainingData(Base):
    __tablename__ = 'training_data'

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    data = Column(JSON, nullable=False)
    status = Column(Enum(ModelStatus), default=ModelStatus.TRAINING)
    file_url = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    project = relationship('Project', back_populates='training_data')
    user = relationship('User', back_populates='training_data')
