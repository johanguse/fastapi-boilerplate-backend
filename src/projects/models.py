from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.database import Base

if TYPE_CHECKING:
    # Still needed for relationship annotations
    from src.activity_log.models import ActivityLog
    from src.organizations.models import Organization


class Project(Base):
    """Project model."""

    __tablename__ = 'projects'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=lambda: datetime.now(UTC),
    )

    # Foreign Keys
    organization_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False,
    )

    # Relationships
    organization: Mapped['Organization'] = relationship('Organization', back_populates='projects')
    activity_logs: Mapped[list['ActivityLog']] = relationship(
        'ActivityLog',
        back_populates='project',
        cascade='all, delete-orphan',
    )

    def __repr__(self) -> str:
        return f'<Project {self.name}>'
