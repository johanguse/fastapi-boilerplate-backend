"""AI Analytics models."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.database import Base

if TYPE_CHECKING:
    from src.organizations.models import Organization
    from src.auth.models import User


class AIAnalyticsQuery(Base):
    """AI Analytics queries and results."""

    __tablename__ = 'ai_analytics_queries'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('organizations.id', ondelete='CASCADE'), index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), index=True
    )
    
    # Query details
    natural_query: Mapped[str] = mapped_column(Text, nullable=False)
    sql_query: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Results and visualization
    results: Mapped[dict] = mapped_column(JSON, default=dict)
    chart_config: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Status and metadata
    status: Mapped[str] = mapped_column(String(20), default='pending')  # pending, completed, failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Usage tracking
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(default=0.0)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships
    organization: Mapped['Organization'] = relationship('Organization')
    user: Mapped['User'] = relationship('User')

    def __repr__(self) -> str:
        return f'<AIAnalyticsQuery org={self.organization_id} status={self.status}>'
