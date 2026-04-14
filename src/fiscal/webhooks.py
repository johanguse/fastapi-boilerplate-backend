"""Webhook handlers for Fiscal Nacional status updates."""

import hashlib
import hmac
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.config import settings
from src.common.session import get_db
from src.fiscal.models import NFSe

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================


class FiscalNacionalWebhookEvent(BaseModel):
    """Fiscal Nacional webhook event payload."""

    event: str = Field(..., description='Event type')
    reference: str = Field(..., description='External reference')
    nfse_number: Optional[str] = Field(None, description='NFS-e number')
    status: str = Field(..., description='Current status')
    issued_at: Optional[str] = Field(None, description='Issue timestamp')
    error_message: Optional[str] = Field(None, description='Error message')
    pdf_url: Optional[str] = Field(None, description='PDF download URL')
    xml_url: Optional[str] = Field(None, description='XML download URL')
    timestamp: str = Field(..., description='Event timestamp')


# ============================================================================
# Webhook Signature Verification
# ============================================================================


def verify_fiscal_webhook_signature(
    payload: bytes, signature: str, secret: str
) -> bool:
    """
    Verify Fiscal Nacional webhook signature.

    NOTE: Update this implementation based on Fiscal Nacional's actual
    signature verification mechanism. This is a placeholder implementation.
    """
    if not secret:
        logger.warning('No webhook secret configured - skipping verification')
        return True

    try:
        # Generate expected signature
        expected_signature = hmac.new(
            secret.encode('utf-8'), payload, hashlib.sha256
        ).hexdigest()

        # Constant-time comparison
        return hmac.compare_digest(signature, expected_signature)

    except Exception as e:
        logger.error(f'Error verifying webhook signature: {e}')
        return False


# ============================================================================
# Webhook Endpoints
# ============================================================================


@router.post('/fiscal-webhook')
async def handle_fiscal_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_fiscal_signature: Optional[str] = Header(None),
) -> dict:
    """
    Handle webhook events from Fiscal Nacional.

    Events:
    - nfse.authorized: NFS-e was successfully authorized
    - nfse.processing: NFS-e is being processed
    - nfse.error: Error during NFS-e generation
    - nfse.cancelled: NFS-e was cancelled
    """
    # Get raw payload for signature verification
    raw_payload = await request.body()

    # Verify signature (if configured)
    webhook_secret = getattr(settings, 'FISCAL_WEBHOOK_SECRET', '')
    if webhook_secret and x_fiscal_signature:
        if not verify_fiscal_webhook_signature(
            raw_payload, x_fiscal_signature, webhook_secret
        ):
            logger.warning('Invalid webhook signature')
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid signature',
            )

    # Parse event
    try:
        event_data = await request.json()
        event = FiscalNacionalWebhookEvent(**event_data)
    except Exception as e:
        logger.error(f'Failed to parse webhook payload: {e}')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid payload',
        )

    logger.info(
        f'Received Fiscal Nacional webhook: {event.event} '
        f'for reference {event.reference}'
    )

    # Find NFS-e by reference
    nfse = await _find_nfse_by_reference(db, event.reference)
    if not nfse:
        logger.warning(f'NFS-e not found for reference: {event.reference}')
        # Return 200 to prevent retries for unknown references
        return {'status': 'ignored', 'reason': 'nfse_not_found'}

    # Update NFS-e based on event type
    try:
        await _handle_webhook_event(nfse, event, db)
        return {'status': 'processed', 'nfse_id': nfse.id}

    except Exception as e:
        logger.error(f'Error processing webhook for NFS-e {nfse.id}: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to process webhook',
        )


# ============================================================================
# Helper Functions
# ============================================================================


async def _find_nfse_by_reference(
    db: AsyncSession, reference: str
) -> Optional[NFSe]:
    """Find NFS-e by fiscal reference."""
    from sqlalchemy import select

    result = await db.execute(
        select(NFSe).where(NFSe.fiscal_nacional_reference == reference)
    )
    return result.scalar_one_or_none()


async def _handle_webhook_event(
    nfse: NFSe, event: FiscalNacionalWebhookEvent, db: AsyncSession
) -> None:
    """Handle different webhook event types."""

    if event.event == 'nfse.authorized':
        # NFS-e successfully authorized
        nfse.status = 'authorized'
        nfse.nfse_number = event.nfse_number

        if event.issued_at:
            try:
                nfse.issued_at = datetime.fromisoformat(event.issued_at)
            except ValueError:
                logger.warning(f'Invalid issued_at format: {event.issued_at}')

        if event.pdf_url:
            nfse.pdf_url = event.pdf_url
        if event.xml_url:
            nfse.xml_url = event.xml_url

        logger.info(
            f'NFS-e {nfse.id} authorized with number {event.nfse_number}'
        )

    elif event.event == 'nfse.processing':
        # NFS-e is being processed
        nfse.status = 'processing'
        logger.info(f'NFS-e {nfse.id} is processing')

    elif event.event == 'nfse.error':
        # Error during generation
        nfse.status = 'error'
        nfse.error_message = event.error_message or 'Unknown error'

        logger.error(f'NFS-e {nfse.id} failed: {nfse.error_message}')

        # Send error notification to admin
        await _send_error_notification(nfse)

    elif event.event == 'nfse.cancelled':
        # NFS-e was cancelled
        nfse.status = 'cancelled'
        nfse.cancelled_at = datetime.fromisoformat(event.timestamp)

        logger.info(f'NFS-e {nfse.id} cancelled')

    else:
        logger.warning(f'Unknown webhook event type: {event.event}')
        return

    # Save updates
    await db.commit()
    await db.refresh(nfse)


async def _send_error_notification(nfse: NFSe) -> None:
    """Send error notification to admin."""
    admin_email = settings.NFSE_ADMIN_EMAIL
    if not admin_email:
        return

    try:
        from src.services.email_service import EmailService

        email_service = EmailService()
        await email_service.send_email(
            to_email=admin_email,
            subject=f'NFS-e Error: {nfse.fiscal_nacional_reference}',
            html_content=f"""
            <h2>NFS-e Webhook Error</h2>
            <p><strong>Reference:</strong> {nfse.fiscal_nacional_reference}</p>
            <p><strong>User:</strong> {nfse.user_id}</p>
            <p><strong>Customer:</strong> {nfse.customer_name}</p>
            <p><strong>Amount:</strong> R$ {nfse.value_brl:.2f}</p>
            <p><strong>Error:</strong></p>
            <pre>{nfse.error_message}</pre>
            """,
        )
    except Exception as e:
        logger.error(f'Failed to send error notification: {e}')
