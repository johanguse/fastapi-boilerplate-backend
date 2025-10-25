"""AI usage tracking and billing integration."""

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Float
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.database import Base


class AIUsageLog(Base):
    """Track AI usage for billing and analytics."""

    __tablename__ = 'ai_usage_logs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('organizations.id', ondelete='CASCADE'), index=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )
    
    # Usage details
    feature: Mapped[str] = mapped_column(String(50), index=True)  # documents, content, analytics
    operation: Mapped[str] = mapped_column(String(50), index=True)  # generate_text, embeddings, etc.
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships
    organization: Mapped['Organization'] = relationship('Organization')
    user: Mapped[Optional['User']] = relationship('User')

    def __repr__(self) -> str:
        return f'<AIUsageLog org={self.organization_id} feature={self.feature} tokens={self.tokens_used}>'


async def track_ai_usage(
    db: AsyncSession,
    organization_id: int,
    user_id: Optional[int],
    feature: str,
    operation: str,
    tokens_used: int,
    cost: float,
) -> None:
    """Track AI usage in the database."""
    usage_log = AIUsageLog(
        organization_id=organization_id,
        user_id=user_id,
        feature=feature,
        operation=operation,
        tokens_used=tokens_used,
        cost=cost,
    )
    
    db.add(usage_log)
    await db.commit()


async def get_usage_stats(
    db: AsyncSession,
    organization_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> dict:
    """Get AI usage statistics for an organization."""
    from sqlalchemy import func, select
    
    query = select(
        AIUsageLog.feature,
        func.sum(AIUsageLog.tokens_used).label('total_tokens'),
        func.sum(AIUsageLog.cost).label('total_cost'),
        func.count(AIUsageLog.id).label('total_operations'),
    ).where(AIUsageLog.organization_id == organization_id)
    
    if start_date:
        query = query.where(AIUsageLog.created_at >= start_date)
    if end_date:
        query = query.where(AIUsageLog.created_at <= end_date)
    
    query = query.group_by(AIUsageLog.feature)
    
    result = await db.execute(query)
    stats = result.fetchall()
    
    return {
        'by_feature': {
            row.feature: {
                'tokens': row.total_tokens,
                'cost': float(row.total_cost),
                'operations': row.total_operations,
            }
            for row in stats
        },
        'total_tokens': sum(row.total_tokens for row in stats),
        'total_cost': sum(float(row.total_cost) for row in stats),
        'total_operations': sum(row.total_operations for row in stats),
    }


async def get_monthly_usage(
    db: AsyncSession,
    organization_id: int,
    year: int,
    month: int,
) -> dict:
    """Get AI usage for a specific month."""
    from datetime import date
    from sqlalchemy import and_, extract
    
    start_date = datetime(year, month, 1, tzinfo=UTC)
    if month == 12:
        end_date = datetime(year + 1, 1, 1, tzinfo=UTC)
    else:
        end_date = datetime(year, month + 1, 1, tzinfo=UTC)
    
    return await get_usage_stats(db, organization_id, start_date, end_date)
