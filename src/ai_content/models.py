"""AI Content Generation models."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.database import Base

if TYPE_CHECKING:
    from src.organizations.models import Organization
    from src.auth.models import User


class AIContentTemplate(Base):
    """AI Content Generation templates."""

    __tablename__ = 'ai_content_templates'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('organizations.id', ondelete='CASCADE'), index=True
    )
    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )
    
    # Template details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    template_type: Mapped[str] = mapped_column(String(50), nullable=False)  # blog_post, email, social_media, etc.
    prompt_template: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Template settings
    settings: Mapped[dict] = mapped_column(JSON, default=dict)  # tone, length, style preferences
    
    # Metadata
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    organization: Mapped['Organization'] = relationship('Organization')
    created_by_user: Mapped[Optional['User']] = relationship('User')
    generations: Mapped[list['AIContentGeneration']] = relationship(
        'AIContentGeneration', back_populates='template', cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'<AIContentTemplate {self.name} type={self.template_type}>'


class AIContentGeneration(Base):
    """AI Content Generation history."""

    __tablename__ = 'ai_content_generations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), index=True
    )
    template_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('ai_content_templates.id', ondelete='SET NULL'), nullable=True
    )
    
    # Generation details
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    input_data: Mapped[dict] = mapped_column(JSON, default=dict)  # topic, tone, length, etc.
    output_content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Usage tracking
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(default=0.0)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships
    user: Mapped['User'] = relationship('User')
    template: Mapped[Optional['AIContentTemplate']] = relationship(
        'AIContentTemplate', back_populates='generations'
    )

    def __repr__(self) -> str:
        return f'<AIContentGeneration user={self.user_id} type={self.content_type}>'
