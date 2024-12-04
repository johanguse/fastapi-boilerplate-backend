from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Invitation(Base):
    __tablename__ = 'invitations'

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    invited_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    invited_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    status = Column(String(20), nullable=False, default='pending')

    team = relationship('Team', back_populates='invitations')
    invited_by = relationship('User', back_populates='invitations_sent')
