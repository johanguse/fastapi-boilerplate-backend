import stripe
from fastapi_pagination import Page, Params, create_page
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.config import settings
from src.organizations.models import Organization
from src.payments.schemas import PlanResponse

stripe.api_key = settings.STRIPE_SECRET_KEY


async def create_checkout_session(
    db: AsyncSession,
    organization: Organization,
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
                'organization_id': organization.id,
                'plan_name': settings.STRIPE_PLANS[price_id]['name'],
            }
        },
    )

    organization.stripe_customer_id = session.customer
    await db.commit()

    return session.url


async def handle_subscription_update(db: AsyncSession, event: dict):
    """Handle subscription updates from Stripe"""
    subscription = event['data']['object']

    # Helper to support both dict- and attribute-style access
    def _get(obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)
    # Lookup organization by stripe_customer_id
    result = await db.execute(
        __import__('sqlalchemy').sql.select(Organization).where(
            Organization.stripe_customer_id == _get(subscription, 'customer')
        )
    )
    organization = result.scalar_one_or_none()
    if not organization:
        return

    # Get price details (supports dict or attribute style)
    items = _get(subscription, 'items', {})
    data_list = _get(items, 'data', []) if items is not None else []
    first_item = data_list[0] if data_list else {}
    price = _get(first_item, 'price', {})
    price_id = _get(price, 'id')
    plan_config = settings.STRIPE_PLANS.get(price_id, {})

    organization.stripe_subscription_id = _get(subscription, 'id')
    organization.plan_name = plan_config.get('name', 'starter')
    organization.subscription_status = _get(subscription, 'status')
    organization.max_projects = plan_config.get('max_projects', 1)
    # If you track billing cycle, you may want to store it separately

    await db.commit()


async def get_available_plans() -> Page[PlanResponse]:
    """Return available plans defined in settings.STRIPE_PLANS as a page."""
    plans: list[PlanResponse] = []
    for price_id, cfg in settings.STRIPE_PLANS.items():
        plans.append(
            PlanResponse(
                id=price_id,
                name=cfg.get('name', 'starter'),
                price=cfg.get('price', 0),
                interval=cfg.get('interval', 'month'),
                max_projects=cfg.get('max_projects', 1),
                features=cfg.get('features', []),
            )
        )

    # simple one-shot page since source is small in-memory list
    # Provide Params explicitly to work both inside and outside request context
    # create_page signature is (items, total, params) as positional-only
    return create_page(plans, len(plans), Params(page=1, size=len(plans)))
