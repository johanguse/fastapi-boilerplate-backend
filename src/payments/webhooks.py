import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from stripe import Webhook

from src.common.config import settings
from src.common.session import get_async_session
from src.organizations.service import get_organization
from src.payments.service import handle_subscription_update

router = APIRouter()


@router.post('/stripe-webhook')
async def stripe_webhook(
    request: Request, db: AsyncSession = Depends(get_async_session)
):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(400, 'Invalid payload')
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, 'Invalid signature')

    # Handle subscription changes
    if event['type'] == 'customer.subscription.updated':
        await handle_subscription_update(db, event)

    if event.type == 'checkout.session.completed':
        session = event.data.object
        org = await get_organization(db, int(session.metadata.organization_id))
        if org:
            org.plan_name = session.metadata.plan_name
            org.subscription_status = 'active'
            await db.commit()

    return {'status': 'success'}
