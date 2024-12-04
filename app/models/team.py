from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Team(Base):
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    stripe_customer_id = Column(Text, unique=True)
    stripe_subscription_id = Column(Text, unique=True)
    stripe_product_id = Column(Text)
    plan_name = Column(String(50))
    subscription_status = Column(String(20))

    team_members = relationship('TeamMember', back_populates='team')
    activity_logs = relationship('ActivityLog', back_populates='team')
    invitations = relationship('Invitation', back_populates='team')
    projects = relationship('Project', back_populates='team')
