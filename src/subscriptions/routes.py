"""API routes for subscription management."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.common.security import get_current_active_user
from src.common.session import get_async_session
from src.organizations.service import get_organization, is_org_admin
from src.subscriptions.models import BillingHistory, SubscriptionPlan
from src.subscriptions.schemas import (
    BillingHistoryResponse,
    CheckoutSessionCreate,
    CheckoutSessionResponse,
    CustomerPortalResponse,
    CustomerSubscriptionResponse,
    SubscriptionPlanResponse,
    SubscriptionUsageResponse,
)
from src.subscriptions.service import (
    cancel_subscription,
    create_checkout_session,
    create_customer_portal_session,
    get_billing_history,
    get_organization_subscription,
    get_subscription_plans,
    get_subscription_usage,
)

router = APIRouter()


@router.get('/plans', response_model=list[SubscriptionPlanResponse])
async def list_subscription_plans(
    db: AsyncSession = Depends(get_async_session),
    active_only: bool = True,
):
    """Get all available subscription plans."""
    plans = await get_subscription_plans(db, active_only=active_only)
    return plans


@router.post(
    '/organizations/{organization_id}/checkout',
    response_model=CheckoutSessionResponse,
)
async def create_subscription_checkout(
    organization_id: int,
    checkout_data: CheckoutSessionCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Create a Stripe checkout session for subscribing to a plan."""
    # Verify user is admin of organization
    organization = await get_organization(db, organization_id)
    if not organization:
        raise HTTPException(404, 'Organization not found')
    
    if not await is_org_admin(db, organization, current_user):
        raise HTTPException(403, 'Only organization admins can manage subscriptions')
    
    # Create checkout session
    return await create_checkout_session(
        db,
        organization,
        checkout_data.price_id,
        checkout_data.success_url,
        checkout_data.cancel_url,
    )


@router.get(
    '/organizations/{organization_id}/subscription',
    response_model=CustomerSubscriptionResponse,
)
async def get_organization_subscription_details(
    organization_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get organization's current subscription details."""
    # Verify user is member of organization
    organization = await get_organization(db, organization_id)
    if not organization:
        raise HTTPException(404, 'Organization not found')
    
    subscription = await get_organization_subscription(db, organization_id)
    if not subscription:
        raise HTTPException(404, 'No subscription found')
    
    return subscription


@router.post(
    '/organizations/{organization_id}/portal', response_model=CustomerPortalResponse
)
async def get_customer_portal(
    organization_id: int,
    return_url: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get Stripe customer portal URL for managing billing."""
    # Verify user is admin of organization
    organization = await get_organization(db, organization_id)
    if not organization:
        raise HTTPException(404, 'Organization not found')
    
    if not await is_org_admin(db, organization, current_user):
        raise HTTPException(403, 'Only organization admins can access billing portal')
    
    return await create_customer_portal_session(db, organization, return_url)


@router.post(
    '/organizations/{organization_id}/cancel',
    response_model=CustomerSubscriptionResponse,
)
async def cancel_organization_subscription(
    organization_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Cancel organization's subscription (at end of billing period)."""
    # Verify user is admin of organization
    organization = await get_organization(db, organization_id)
    if not organization:
        raise HTTPException(404, 'Organization not found')
    
    if not await is_org_admin(db, organization, current_user):
        raise HTTPException(403, 'Only organization admins can cancel subscriptions')
    
    return await cancel_subscription(db, organization_id)


@router.get(
    '/organizations/{organization_id}/usage',
    response_model=SubscriptionUsageResponse,
)
async def get_organization_usage(
    organization_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get organization's subscription usage metrics."""
    # Verify user is member of organization
    organization = await get_organization(db, organization_id)
    if not organization:
        raise HTTPException(404, 'Organization not found')
    
    return await get_subscription_usage(db, organization_id)


@router.get(
    '/organizations/{organization_id}/billing-history',
    response_model=Page[BillingHistoryResponse],
)
async def get_organization_billing_history(
    organization_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    """Get organization's billing history."""
    # Verify user is admin of organization
    organization = await get_organization(db, organization_id)
    if not organization:
        raise HTTPException(404, 'Organization not found')
    
    if not await is_org_admin(db, organization, current_user):
        raise HTTPException(403, 'Only organization admins can view billing history')
    
    # Get subscription
    subscription = await get_organization_subscription(db, organization_id)
    if not subscription:
        raise HTTPException(404, 'No subscription found')
    
    # Return paginated billing history
    return await paginate(
        db,
        select(BillingHistory)
        .where(BillingHistory.subscription_id == subscription.id)
        .order_by(BillingHistory.invoice_date.desc()),
    )
