"""Seed data for subscriptions and billing."""
from datetime import UTC, datetime, timedelta
from src.subscriptions.models import CustomerSubscription, BillingHistory
from .constants import random_ip, random_user_agent

def create_subscriptions_and_billing(organizations, plans):
    """Create subscription and billing history seed data."""
    subscriptions = []
    billing_records = []
    payment_activities = []
    
    # Development Team - Business plan (active subscription)
    sub1 = CustomerSubscription(
        organization_id=organizations[0].id,
        plan_id=plans['business'].id,
        stripe_customer_id='cus_dev_team_001',
        stripe_subscription_id='sub_dev_team_001',
        status='active',
        current_period_start=datetime.now(UTC) - timedelta(days=15),
        current_period_end=datetime.now(UTC) + timedelta(days=15),
        cancel_at_period_end=False,
        current_users_count=5,
        current_projects_count=3,
        current_storage_gb=45,
        created_at=datetime.now(UTC) - timedelta(days=75)
    )
    subscriptions.append(sub1)
    
    # Billing history for Development Team (last 3 months)
    for months_ago in range(3):
        billing_records.append(BillingHistory(
            subscription_id=sub1.id,
            stripe_invoice_id=f'inv_dev_{months_ago}_001',
            stripe_payment_intent_id=f'pi_dev_{months_ago}_001',
            amount=plans['business'].price_monthly_usd,
            currency='usd',
            status='paid',
            invoice_date=datetime.now(UTC) - timedelta(days=30 * months_ago),
            paid_at=datetime.now(UTC) - timedelta(days=30 * months_ago, hours=1),
            description=f"Business Plan - Monthly subscription (Month {3-months_ago})"
        ))
    
    # Marketing Team - Pro plan (active)
    sub2 = CustomerSubscription(
        organization_id=organizations[1].id,
        plan_id=plans['pro'].id,
        stripe_customer_id='cus_marketing_001',
        stripe_subscription_id='sub_marketing_001',
        status='active',
        current_period_start=datetime.now(UTC) - timedelta(days=10),
        current_period_end=datetime.now(UTC) + timedelta(days=20),
        cancel_at_period_end=False,
        current_users_count=4,
        current_projects_count=2,
        current_storage_gb=12,
        created_at=datetime.now(UTC) - timedelta(days=55)
    )
    subscriptions.append(sub2)
    
    # Billing history for Marketing Team (last 2 months)
    for months_ago in range(2):
        billing_records.append(BillingHistory(
            subscription_id=sub2.id,
            stripe_invoice_id=f'inv_marketing_{months_ago}_001',
            stripe_payment_intent_id=f'pi_marketing_{months_ago}_001',
            amount=plans['pro'].price_monthly_usd,
            currency='usd',
            status='paid',
            invoice_date=datetime.now(UTC) - timedelta(days=30 * months_ago),
            paid_at=datetime.now(UTC) - timedelta(days=30 * months_ago, hours=2),
            description=f"Pro Plan - Monthly subscription (Month {2-months_ago})"
        ))
    
    # Research Team - Starter plan (active)
    sub3 = CustomerSubscription(
        organization_id=organizations[2].id,
        plan_id=plans['starter'].id,
        stripe_customer_id='cus_research_001',
        stripe_subscription_id='sub_research_001',
        status='active',
        current_period_start=datetime.now(UTC) - timedelta(days=5),
        current_period_end=datetime.now(UTC) + timedelta(days=25),
        cancel_at_period_end=False,
        current_users_count=3,
        current_projects_count=1,
        current_storage_gb=3,
        created_at=datetime.now(UTC) - timedelta(days=45)
    )
    subscriptions.append(sub3)
    
    # Billing history for Research Team (last month)
    billing_records.append(BillingHistory(
        subscription_id=sub3.id,
        stripe_invoice_id='inv_research_0_001',
        stripe_payment_intent_id='pi_research_0_001',
        amount=plans['starter'].price_monthly_usd,
        currency='usd',
        status='paid',
        invoice_date=datetime.now(UTC) - timedelta(days=30),
        paid_at=datetime.now(UTC) - timedelta(days=30, hours=1),
        description="Starter Plan - Monthly subscription"
    ))
    
    # Sales Department - Pro plan (trialing)
    sub4 = CustomerSubscription(
        organization_id=organizations[3].id,
        plan_id=plans['pro'].id,
        stripe_customer_id='cus_sales_001',
        stripe_subscription_id='sub_sales_001',
        status='trialing',
        trial_start=datetime.now(UTC) - timedelta(days=5),
        trial_end=datetime.now(UTC) + timedelta(days=9),
        current_period_start=datetime.now(UTC) - timedelta(days=5),
        current_period_end=datetime.now(UTC) + timedelta(days=25),
        cancel_at_period_end=False,
        current_users_count=3,
        current_projects_count=1,
        current_storage_gb=2,
        created_at=datetime.now(UTC) - timedelta(days=5)
    )
    subscriptions.append(sub4)
    
    # Customer Success - Free plan
    sub5 = CustomerSubscription(
        organization_id=organizations[4].id,
        plan_id=plans['free'].id,
        status='active',
        current_period_start=datetime.now(UTC) - timedelta(days=20),
        current_period_end=datetime.now(UTC) + timedelta(days=340),
        cancel_at_period_end=False,
        current_users_count=2,
        current_projects_count=1,
        current_storage_gb=0,
        created_at=datetime.now(UTC) - timedelta(days=20)
    )
    subscriptions.append(sub5)
    
    # Create payment activity logs for each billing record
    from src.activity_log.models import ActivityLog
    
    for billing in billing_records:
        # Determine which organization based on subscription
        org_id = None
        if billing.subscription_id == sub1.id:
            org_id = organizations[0].id
        elif billing.subscription_id == sub2.id:
            org_id = organizations[1].id
        elif billing.subscription_id == sub3.id:
            org_id = organizations[2].id
            
        payment_activities.append(ActivityLog(
            action="payment.succeeded",
            action_type="payment",
            description=f"Payment successful: ${billing.amount / 100:.2f} {billing.currency.upper()}",
            organization_id=org_id,
            ip_address=random_ip(),
            user_agent=random_user_agent(),
            created_at=billing.paid_at
        ))
    
    return subscriptions, billing_records, payment_activities
