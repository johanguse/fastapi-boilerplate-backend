"""Business logic for subscription management."""

from datetime import UTC, datetime
from typing import Optional

import stripe
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.common.config import settings
from src.organizations.models import Organization
from src.subscriptions.models import (
    BillingHistory,
    CustomerSubscription,
    SubscriptionPlan,
)
from src.subscriptions.schemas import (
    CheckoutSessionResponse,
    CustomerPortalResponse,
    SubscriptionUsageResponse,
)

stripe.api_key = settings.STRIPE_SECRET_KEY


async def get_subscription_plans(
    db: AsyncSession, active_only: bool = True
) -> list[SubscriptionPlan]:
    """Get all subscription plans."""
    query = select(SubscriptionPlan).order_by(SubscriptionPlan.sort_order)
    
    if active_only:
        query = query.where(SubscriptionPlan.is_active == True)  # noqa: E712
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_subscription_plan(
    db: AsyncSession, plan_id: int
) -> Optional[SubscriptionPlan]:
    """Get a subscription plan by ID."""
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
    )
    return result.scalar_one_or_none()


async def get_subscription_plan_by_name(
    db: AsyncSession, name: str
) -> Optional[SubscriptionPlan]:
    """Get a subscription plan by name."""
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.name == name)
    )
    return result.scalar_one_or_none()


async def get_organization_subscription(
    db: AsyncSession, organization_id: int
) -> Optional[CustomerSubscription]:
    """Get organization's current subscription."""
    result = await db.execute(
        select(CustomerSubscription)
        .options(selectinload(CustomerSubscription.plan))
        .where(CustomerSubscription.organization_id == organization_id)
    )
    return result.scalar_one_or_none()


async def create_checkout_session(
    db: AsyncSession,
    organization: Organization,
    price_id: str,
    success_url: str,
    cancel_url: str,
) -> CheckoutSessionResponse:
    """Create a Stripe checkout session for subscription."""
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(500, 'Stripe not configured')
    
    # Get or create subscription record
    subscription = await get_organization_subscription(db, organization.id)
    
    if not subscription:
        subscription = CustomerSubscription(
            organization_id=organization.id,
            status='incomplete',
        )
        db.add(subscription)
        await db.flush()
    
    # Get plan details from price_id
    plan_name = 'starter'
    for pid, plan_config in settings.STRIPE_PLANS.items():
        if pid == price_id:
            plan_name = plan_config.get('name', 'starter')
            break
    
    try:
        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            customer=subscription.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                }
            ],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            subscription_data={
                'metadata': {
                    'organization_id': str(organization.id),
                    'subscription_id': str(subscription.id),
                    'plan_name': plan_name,
                }
            },
            metadata={
                'organization_id': str(organization.id),
                'subscription_id': str(subscription.id),
            },
        )
        
        # Update subscription with customer ID
        if session.customer:
            subscription.stripe_customer_id = session.customer
            await db.commit()
        
        return CheckoutSessionResponse(
            session_id=session.id, checkout_url=session.url
        )
    
    except stripe.error.StripeError as e:
        raise HTTPException(400, f'Stripe error: {str(e)}')


async def create_customer_portal_session(
    db: AsyncSession, organization: Organization, return_url: str
) -> CustomerPortalResponse:
    """Create a Stripe customer portal session."""
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(500, 'Stripe not configured')
    
    subscription = await get_organization_subscription(db, organization.id)
    
    if not subscription or not subscription.stripe_customer_id:
        raise HTTPException(404, 'No active subscription found')
    
    try:
        session = stripe.billing_portal.Session.create(
            customer=subscription.stripe_customer_id, return_url=return_url
        )
        
        return CustomerPortalResponse(portal_url=session.url)
    
    except stripe.error.StripeError as e:
        raise HTTPException(400, f'Stripe error: {str(e)}')


async def cancel_subscription(
    db: AsyncSession, organization_id: int
) -> CustomerSubscription:
    """Cancel an organization's subscription."""
    subscription = await get_organization_subscription(db, organization_id)
    
    if not subscription or not subscription.stripe_subscription_id:
        raise HTTPException(404, 'No active subscription found')
    
    try:
        # Cancel in Stripe
        stripe.Subscription.modify(
            subscription.stripe_subscription_id, cancel_at_period_end=True
        )
        
        # Update local record
        subscription.cancel_at_period_end = True
        subscription.canceled_at = datetime.now(UTC)
        await db.commit()
        
        return subscription
    
    except stripe.error.StripeError as e:
        raise HTTPException(400, f'Stripe error: {str(e)}')


async def get_subscription_usage(
    db: AsyncSession, organization_id: int
) -> SubscriptionUsageResponse:
    """Get organization's subscription usage metrics."""
    subscription = await get_organization_subscription(db, organization_id)
    
    if not subscription or not subscription.plan:
        raise HTTPException(404, 'No active subscription found')
    
    plan = subscription.plan
    
    # Calculate usage percentages
    projects_usage = (
        (subscription.current_projects_count / plan.max_projects * 100)
        if plan.max_projects > 0
        else 0
    )
    users_usage = (
        (subscription.current_users_count / plan.max_users * 100)
        if plan.max_users > 0
        else 0
    )
    storage_usage = (
        (subscription.current_storage_gb / plan.max_storage_gb * 100)
        if plan.max_storage_gb > 0
        else 0
    )
    
    return SubscriptionUsageResponse(
        organization_id=organization_id,
        plan_name=plan.name,
        max_projects=plan.max_projects,
        max_users=plan.max_users,
        max_storage_gb=plan.max_storage_gb,
        current_projects=subscription.current_projects_count,
        current_users=subscription.current_users_count,
        current_storage_gb=subscription.current_storage_gb,
        projects_usage_percent=projects_usage,
        users_usage_percent=users_usage,
        storage_usage_percent=storage_usage,
    )


async def handle_subscription_created(db: AsyncSession, event: dict):
    """Handle subscription.created webhook event."""
    subscription_data = event['data']['object']
    
    # Get metadata
    metadata = subscription_data.get('metadata', {})
    subscription_id = metadata.get('subscription_id')
    
    if not subscription_id:
        return
    
    # Update subscription record
    result = await db.execute(
        select(CustomerSubscription).where(CustomerSubscription.id == int(subscription_id))
    )
    subscription = result.scalar_one_or_none()
    
    if subscription:
        subscription.stripe_subscription_id = subscription_data['id']
        subscription.stripe_customer_id = subscription_data['customer']
        subscription.status = subscription_data['status']
        subscription.current_period_start = datetime.fromtimestamp(
            subscription_data['current_period_start'], UTC
        )
        subscription.current_period_end = datetime.fromtimestamp(
            subscription_data['current_period_end'], UTC
        )
        await db.commit()


async def handle_subscription_updated(db: AsyncSession, event: dict):
    """Handle subscription.updated webhook event."""
    subscription_data = event['data']['object']
    stripe_subscription_id = subscription_data['id']
    
    # Find subscription by Stripe ID
    result = await db.execute(
        select(CustomerSubscription).where(
            CustomerSubscription.stripe_subscription_id == stripe_subscription_id
        )
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        return
    
    # Update subscription details
    subscription.status = subscription_data['status']
    subscription.current_period_start = datetime.fromtimestamp(
        subscription_data['current_period_start'], UTC
    )
    subscription.current_period_end = datetime.fromtimestamp(
        subscription_data['current_period_end'], UTC
    )
    subscription.cancel_at_period_end = subscription_data.get(
        'cancel_at_period_end', False
    )
    
    # Update trial info if present
    if subscription_data.get('trial_start'):
        subscription.trial_start = datetime.fromtimestamp(
            subscription_data['trial_start'], UTC
        )
    if subscription_data.get('trial_end'):
        subscription.trial_end = datetime.fromtimestamp(
            subscription_data['trial_end'], UTC
        )
    
    await db.commit()


async def handle_subscription_deleted(db: AsyncSession, event: dict):
    """Handle subscription.deleted webhook event."""
    subscription_data = event['data']['object']
    stripe_subscription_id = subscription_data['id']
    
    # Find and update subscription
    result = await db.execute(
        select(CustomerSubscription).where(
            CustomerSubscription.stripe_subscription_id == stripe_subscription_id
        )
    )
    subscription = result.scalar_one_or_none()
    
    if subscription:
        subscription.status = 'canceled'
        subscription.canceled_at = datetime.now(UTC)
        await db.commit()


async def handle_invoice_paid(db: AsyncSession, event: dict):
    """Handle invoice.payment_succeeded webhook event."""
    invoice_data = event['data']['object']
    stripe_subscription_id = invoice_data.get('subscription')
    
    if not stripe_subscription_id:
        return
    
    # Find subscription
    result = await db.execute(
        select(CustomerSubscription).where(
            CustomerSubscription.stripe_subscription_id == stripe_subscription_id
        )
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        return
    
    # Create billing history record
    billing_record = BillingHistory(
        subscription_id=subscription.id,
        stripe_invoice_id=invoice_data['id'],
        stripe_payment_intent_id=invoice_data.get('payment_intent'),
        amount=invoice_data['amount_paid'],
        currency=invoice_data['currency'],
        status='paid',
        invoice_date=datetime.fromtimestamp(invoice_data['created'], UTC),
        paid_at=datetime.now(UTC),
        invoice_url=invoice_data.get('hosted_invoice_url'),
        invoice_pdf=invoice_data.get('invoice_pdf'),
        description=invoice_data.get('description'),
    )
    
    db.add(billing_record)
    
    # Update subscription status
    if subscription.status != 'active':
        subscription.status = 'active'
    
    await db.commit()


async def handle_invoice_payment_failed(db: AsyncSession, event: dict):
    """Handle invoice.payment_failed webhook event."""
    invoice_data = event['data']['object']
    stripe_subscription_id = invoice_data.get('subscription')
    
    if not stripe_subscription_id:
        return
    
    # Find subscription
    result = await db.execute(
        select(CustomerSubscription).where(
            CustomerSubscription.stripe_subscription_id == stripe_subscription_id
        )
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        return
    
    # Create billing history record
    billing_record = BillingHistory(
        subscription_id=subscription.id,
        stripe_invoice_id=invoice_data['id'],
        stripe_payment_intent_id=invoice_data.get('payment_intent'),
        amount=invoice_data['amount_due'],
        currency=invoice_data['currency'],
        status='failed',
        invoice_date=datetime.fromtimestamp(invoice_data['created'], UTC),
        invoice_url=invoice_data.get('hosted_invoice_url'),
        description=invoice_data.get('description'),
    )
    
    db.add(billing_record)
    
    # Update subscription status
    subscription.status = 'past_due'
    
    await db.commit()


async def get_billing_history(
    db: AsyncSession, subscription_id: int
) -> list[BillingHistory]:
    """Get billing history for a subscription."""
    result = await db.execute(
        select(BillingHistory)
        .where(BillingHistory.subscription_id == subscription_id)
        .order_by(BillingHistory.invoice_date.desc())
    )
    return list(result.scalars().all())
