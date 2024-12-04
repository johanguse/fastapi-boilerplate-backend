from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class TeamMember(Base):
    __tablename__ = 'team_members'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    role = Column(String(50), nullable=False)
    joined_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship('User', back_populates='team_members')
    team = relationship('Team', back_populates='team_members')
