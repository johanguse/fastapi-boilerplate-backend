import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from stripe import Webhook

from src.common.config import settings
from src.common.session import get_async_session
from src.payments.service import handle_subscription_update
from src.teams.service import get_team

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
        team = await get_team(db, session.metadata.team_id)
        team.plan_name = session.metadata.plan_name
        team.subscription_status = 'active'
        await db.commit()

    return {'status': 'success'}
