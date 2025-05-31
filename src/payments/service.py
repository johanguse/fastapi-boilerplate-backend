import stripe
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.config import settings
from src.teams.models import Team
from src.teams.service import get_team_by_stripe_id

stripe.api_key = settings.STRIPE_SECRET_KEY


async def create_checkout_session(
    db: AsyncSession,
    team: Team,
    price_id: str,
) -> str:
    """Create Stripe checkout session"""
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[
            {
                'price': price_id,
                'quantity': 1,
            }
        ],
        mode='subscription',
        success_url=settings.PAYMENT_SUCCESS_URL,
        cancel_url=settings.PAYMENT_CANCEL_URL,
        subscription_data={
            'metadata': {
                'team_id': team.id,
                'plan_name': settings.STRIPE_PLANS[price_id]['name'],
            }
        },
    )

    team.stripe_customer_id = session.customer
    await db.commit()

    return session.url


async def handle_subscription_update(db: AsyncSession, event: dict):
    """Handle subscription updates from Stripe"""
    subscription = event['data']['object']
    team = await get_team_by_stripe_id(db, subscription.customer)

    if not team:
        return

    # Get price details
    price_id = subscription['items']['data'][0]['price']['id']
    plan_config = settings.STRIPE_PLANS.get(price_id, {})

    team.stripe_subscription_id = subscription.id
    team.plan_name = plan_config.get('name', 'starter')
    team.subscription_status = subscription.status
    team.max_projects = plan_config.get('max_projects', 1)
    team.billing_cycle = plan_config.get('interval', 'month')

    await db.commit()
