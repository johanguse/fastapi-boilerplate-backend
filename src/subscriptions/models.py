"""Database models for subscription management."""

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.database import Base


class SubscriptionPlan(Base):
    """Subscription plan model with multi-currency support."""

    __tablename__ = 'subscription_plans'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stripe_price_id_monthly: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    stripe_price_id_yearly: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    stripe_product_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )

    # Pricing (in cents)
    price_monthly_usd: Mapped[int] = mapped_column(Integer, default=0)
    price_yearly_usd: Mapped[int] = mapped_column(Integer, default=0)
    price_monthly_eur: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    price_yearly_eur: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    price_monthly_gbp: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    price_yearly_gbp: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    price_monthly_brl: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    price_yearly_brl: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    # Plan limits
    max_projects: Mapped[int] = mapped_column(Integer, default=1)
    max_users: Mapped[int] = mapped_column(Integer, default=1)
    max_storage_gb: Mapped[int] = mapped_column(Integer, default=1)

    # AI limits
    max_ai_credits_monthly: Mapped[int] = mapped_column(Integer, default=0)
    ai_features_enabled: Mapped[dict] = mapped_column(JSON, default=dict)

    # Features (JSON array of feature keys)
    features: Mapped[dict] = mapped_column(JSON, default=dict)

    # Metadata
    is_active: Mapped[bool] = mapped_column(default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    subscriptions: Mapped[list['CustomerSubscription']] = relationship(
        back_populates='plan', cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'<SubscriptionPlan {self.name}>'


class CustomerSubscription(Base):
    """Customer subscription tracking with Stripe integration."""

    __tablename__ = 'customer_subscriptions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('organizations.id', ondelete='CASCADE'), index=True
    )
    plan_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey('subscription_plans.id', ondelete='SET NULL'),
        nullable=True,
    )

    # Stripe identifiers
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True
    )
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True
    )

    # Subscription status
    status: Mapped[str] = mapped_column(
        String(20), default='inactive', index=True
    )  # active, canceled, past_due, unpaid, incomplete, trialing

    # Billing cycle
    current_period_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_period_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancel_at_period_end: Mapped[bool] = mapped_column(default=False)
    canceled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    trial_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    trial_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Usage tracking
    current_users_count: Mapped[int] = mapped_column(Integer, default=0)
    current_projects_count: Mapped[int] = mapped_column(Integer, default=0)
    current_storage_gb: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata (using extra_data to avoid SQLAlchemy reserved name)
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    from src.organizations.models import Organization

    organization: Mapped['Organization'] = relationship(
        back_populates='subscription'
    )
    plan: Mapped[Optional['SubscriptionPlan']] = relationship(
        back_populates='subscriptions'
    )
    billing_history: Mapped[list['BillingHistory']] = relationship(
        back_populates='subscription', cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'<CustomerSubscription org={self.organization_id} status={self.status}>'


class BillingHistory(Base):
    """Billing and invoice history."""

    __tablename__ = 'billing_history'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    subscription_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('customer_subscriptions.id', ondelete='CASCADE'),
        index=True,
    )

    # Invoice details
    stripe_invoice_id: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True
    )
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )

    # Payment information
    amount: Mapped[int] = mapped_column(Integer)  # in cents
    currency: Mapped[str] = mapped_column(String(3), default='usd')
    status: Mapped[str] = mapped_column(
        String(20), index=True
    )  # paid, failed, pending, refunded

    # Dates
    invoice_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # URLs
    invoice_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    invoice_pdf: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata (using extra_data to avoid SQLAlchemy reserved name)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Relationships
    subscription: Mapped['CustomerSubscription'] = relationship(
        back_populates='billing_history'
    )

    def __repr__(self) -> str:
        return f'<BillingHistory invoice={self.stripe_invoice_id} status={self.status}>'
