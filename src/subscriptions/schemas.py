"""Pydantic schemas for subscription API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SubscriptionPlanBase(BaseModel):
    """Base subscription plan schema."""

    name: str = Field(..., max_length=50)
    display_name: str = Field(..., max_length=100)
    description: Optional[str] = None
    price_monthly_usd: int = Field(..., ge=0, description='Price in cents')
    price_yearly_usd: int = Field(..., ge=0, description='Price in cents')
    max_projects: int = Field(default=1, ge=1)
    max_users: int = Field(default=1, ge=1)
    max_storage_gb: int = Field(default=1, ge=1)
    features: dict = Field(default_factory=dict)


class SubscriptionPlanCreate(SubscriptionPlanBase):
    """Schema for creating a subscription plan."""

    stripe_price_id_monthly: Optional[str] = None
    stripe_price_id_yearly: Optional[str] = None
    stripe_product_id: Optional[str] = None


class SubscriptionPlanResponse(SubscriptionPlanBase):
    """Response schema for subscription plan."""

    id: int
    stripe_price_id_monthly: Optional[str] = None
    stripe_price_id_yearly: Optional[str] = None
    stripe_product_id: Optional[str] = None
    is_active: bool
    sort_order: int
    created_at: datetime
    
    # Multi-currency pricing
    price_monthly_eur: Optional[int] = None
    price_yearly_eur: Optional[int] = None
    price_monthly_gbp: Optional[int] = None
    price_yearly_gbp: Optional[int] = None
    price_monthly_brl: Optional[int] = None
    price_yearly_brl: Optional[int] = None

    class Config:
        from_attributes = True


class CustomerSubscriptionBase(BaseModel):
    """Base customer subscription schema."""

    status: str = Field(default='inactive')
    cancel_at_period_end: bool = False


class CustomerSubscriptionCreate(BaseModel):
    """Schema for creating a subscription."""

    organization_id: int
    plan_id: int
    price_id: str = Field(..., description='Stripe price ID')


class CustomerSubscriptionResponse(CustomerSubscriptionBase):
    """Response schema for customer subscription."""

    id: int
    organization_id: int
    plan_id: Optional[int] = None
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    current_users_count: int
    current_projects_count: int
    current_storage_gb: int
    created_at: datetime
    updated_at: datetime
    
    # Include plan details
    plan: Optional[SubscriptionPlanResponse] = None

    class Config:
        from_attributes = True


class BillingHistoryResponse(BaseModel):
    """Response schema for billing history."""

    id: int
    subscription_id: int
    stripe_invoice_id: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    amount: int
    currency: str
    status: str
    invoice_date: datetime
    paid_at: Optional[datetime] = None
    invoice_url: Optional[str] = None
    invoice_pdf: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CheckoutSessionCreate(BaseModel):
    """Schema for creating a Stripe checkout session."""

    price_id: str = Field(..., description='Stripe price ID')
    success_url: str = Field(..., description='Redirect URL on success')
    cancel_url: str = Field(..., description='Redirect URL on cancel')


class CheckoutSessionResponse(BaseModel):
    """Response schema for checkout session."""

    session_id: str
    checkout_url: str


class CustomerPortalResponse(BaseModel):
    """Response schema for customer portal."""

    portal_url: str


class SubscriptionUsageResponse(BaseModel):
    """Response schema for subscription usage metrics."""

    organization_id: int
    plan_name: str
    max_projects: int
    max_users: int
    max_storage_gb: int
    current_projects: int
    current_users: int
    current_storage_gb: int
    projects_usage_percent: float
    users_usage_percent: float
    storage_usage_percent: float
