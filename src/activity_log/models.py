from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.common.database import Base

if TYPE_CHECKING:
    from src.auth.models import User
    from src.organizations.models import Organization
    from src.projects.models import Project


class ActivityLog(Base):
    """Activity log model."""

    __tablename__ = 'activity_logs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    action_type: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    action_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON, name='metadata'
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Foreign Keys
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
    )
    organization_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=True,
    )
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey('projects.id', ondelete='CASCADE'),
        nullable=True,
    )

    # Relationships using string literals for forward references
    user: Mapped[Optional['User']] = relationship(
        'User',
        back_populates='activities',
    )
    organization: Mapped['Organization'] = relationship(
        'Organization',
        back_populates='activity_logs',
    )
    # Back-populated on Organization
    # organization relationship defined above
    project: Mapped['Project'] = relationship(
        'Project',
        back_populates='activity_logs',
    )

    # Add indexes
    __table_args__ = (
        Index('ix_activity_logs_created_at', 'created_at'),
        Index('ix_activity_logs_action_type', 'action_type'),
        Index('ix_activity_logs_org_user', 'organization_id', 'user_id'),
    )

    def __repr__(self) -> str:
        return f'<ActivityLog {self.action} by {self.user_id} at {self.created_at}>'
