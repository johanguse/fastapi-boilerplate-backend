"""Stripe webhook handlers for subscription events."""

import logging

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.config import settings
from src.common.session import get_async_session
from src.subscriptions.service import (
    handle_invoice_paid,
    handle_invoice_payment_failed,
    handle_subscription_created,
    handle_subscription_deleted,
    handle_subscription_updated,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post('/stripe')
async def stripe_webhook(
    request: Request, db: AsyncSession = Depends(get_async_session)
):
    """Handle Stripe webhook events for subscriptions."""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(500, 'Webhook secret not configured')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error('Invalid webhook payload')
        raise HTTPException(400, 'Invalid payload')
    except stripe.error.SignatureVerificationError:
        logger.error('Invalid webhook signature')
        raise HTTPException(400, 'Invalid signature')
    
    event_type = event['type']
    logger.info(f'Processing Stripe webhook: {event_type}')
    
    try:
        # Handle different event types
        if event_type == 'customer.subscription.created':
            await handle_subscription_created(db, event)
        
        elif event_type == 'customer.subscription.updated':
            await handle_subscription_updated(db, event)
        
        elif event_type == 'customer.subscription.deleted':
            await handle_subscription_deleted(db, event)
        
        elif event_type == 'invoice.payment_succeeded':
            await handle_invoice_paid(db, event)
        
        elif event_type == 'invoice.payment_failed':
            await handle_invoice_payment_failed(db, event)
        
        elif event_type == 'checkout.session.completed':
            # Handle successful checkout
            session = event['data']['object']
            logger.info(f"Checkout session completed: {session.get('id')}")
            # The subscription.created event will handle the actual subscription setup
        
        else:
            logger.info(f'Unhandled event type: {event_type}')
    
    except Exception as e:
        logger.error(f'Error processing webhook {event_type}: {str(e)}')
        # Return 200 to prevent Stripe from retrying
        return {'status': 'error', 'message': str(e)}
    
    return {'status': 'success'}
