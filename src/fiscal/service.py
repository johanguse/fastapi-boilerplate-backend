"""Service layer for NFS-e (Brazilian electronic service invoices) management."""

import logging
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.fiscal.models import NFSe, UserTaxInfo
from src.services.currency_conversion import (
    create_currency_conversion_service,
)
from src.services.email_service import EmailService
from src.services.fiscal_nacional import (
    FiscalNacionalApiError,
    FiscalNacionalClient,
    FiscalNacionalConfig,
    build_brazilian_nfse_request,
    build_international_nfse_request,
    generate_external_reference,
)
from src.utils.currencies import get_default_currency_for_country

logger = logging.getLogger(__name__)


class NFSeService:
    """High-level service for managing NFS-e operations."""

    def __init__(
        self,
        db: AsyncSession,
        api_key: str,
        base_url: str = '',
        admin_email: Optional[str] = None,
        stripe_api_key: Optional[str] = None,
    ):
        self.db = db
        self.fiscal_client = FiscalNacionalClient(
            FiscalNacionalConfig(api_key=api_key, base_url=base_url)
        )
        self.currency_service = create_currency_conversion_service(
            stripe_api_key
        )
        self.admin_email = admin_email
        self.email_service = EmailService()

    async def create_nfse_for_subscription(
        self,
        user_id: int,
        stripe_invoice_id: str,
        stripe_payment_intent_id: str,
        stripe_charge_id: str,
        service_description: str,
        amount: float,
        currency: str,
        customer_email: str,
        product_name: Optional[str] = None,
    ) -> NFSe:
        """Create NFS-e for subscription payment with automatic currency conversion."""
        # Convert currency to BRL using Stripe balance or PTAX
        conversion = await self.currency_service.convert_to_brl(
            amount=amount,
            currency=currency,
            charge_id=stripe_charge_id,
            payment_intent_id=stripe_payment_intent_id,
        )
        return await self._create_nfse(
            user_id=user_id,
            transaction_type='subscription',
            stripe_invoice_id=stripe_invoice_id,
            stripe_payment_intent_id=stripe_payment_intent_id,
            stripe_charge_id=stripe_charge_id,
            service_description=service_description,
            amount_brl=conversion.amount_brl,
            original_amount=conversion.original_amount,
            original_currency=conversion.original_currency,
            exchange_rate=conversion.exchange_rate,
            conversion_source=conversion.source,
            customer_email=customer_email,
            product_name=product_name,
        )

    async def create_nfse_for_credit_purchase(
        self,
        user_id: int,
        stripe_payment_intent_id: str,
        stripe_charge_id: str,
        service_description: str,
        amount: float,
        currency: str,
        customer_email: str,
        product_name: Optional[str] = None,
    ) -> NFSe:
        """Create NFS-e for credit package purchase with automatic currency conversion."""
        # Convert currency to BRL
        conversion = await self.currency_service.convert_to_brl(
            amount=amount,
            currency=currency,
            charge_id=stripe_charge_id,
            payment_intent_id=stripe_payment_intent_id,
        )
        return await self._create_nfse(
            user_id=user_id,
            transaction_type='credit_purchase',
            stripe_payment_intent_id=stripe_payment_intent_id,
            stripe_charge_id=stripe_charge_id,
            service_description=service_description,
            amount_brl=conversion.amount_brl,
            original_amount=conversion.original_amount,
            original_currency=conversion.original_currency,
            exchange_rate=conversion.exchange_rate,
            conversion_source=conversion.source,
            customer_email=customer_email,
            product_name=product_name,
        )

    async def _create_nfse(
        self,
        user_id: int,
        transaction_type: str,
        stripe_payment_intent_id: str,
        stripe_charge_id: str,
        service_description: str,
        amount_brl: float,
        original_amount: float,
        original_currency: str,
        exchange_rate: float,
        conversion_source: str,
        customer_email: str,
        stripe_invoice_id: Optional[str] = None,
        product_name: Optional[str] = None,
    ) -> NFSe:
        """Internal method to create NFS-e record and emit via API."""
        # Get user's tax info
        tax_info = await self._get_user_tax_info(user_id)
        if not tax_info:
            raise ValueError(
                'User must provide tax information before generating NFS-e'
            )

        # Generate external reference
        stripe_id = stripe_invoice_id or stripe_payment_intent_id
        external_reference = generate_external_reference(
            transaction_type, stripe_id
        )

        # Build API request based on customer location
        if tax_info.is_brazilian:
            api_request = build_brazilian_nfse_request(
                customer_name=tax_info.full_name,
                customer_email=customer_email,
                customer_document=tax_info.cpf_cnpj,
                service_description=service_description,
                amount_brl=amount_brl,
                address=tax_info.address,
                number=tax_info.number,
                complement=tax_info.complement,
                neighborhood=tax_info.neighborhood,
                city=tax_info.city,
                city_code=tax_info.city_code,
                state=tax_info.state,
                postal_code=tax_info.postal_code,
                inscricao_municipal=tax_info.inscricao_municipal,
                external_reference=external_reference,
                product_name=product_name,
            )
        else:
            # International customer
            original_currency = get_default_currency_for_country(
                tax_info.country
            )
            api_request = build_international_nfse_request(
                customer_name=tax_info.full_name,
                customer_email=customer_email,
                customer_country_iso2=tax_info.country,
                service_description=service_description,
                amount_brl=amount_brl,
                customer_nif=tax_info.nif,
                nif_exemption_code=tax_info.nif_exemption_code,
                original_currency_code=original_currency,
                original_amount=original_amount,
                external_reference=external_reference,
                product_name=product_name,
            )

        # Create NFS-e via API
        try:
            api_response = await self.fiscal_client.create_nfse(api_request)

            # Create database record
            nfse = NFSe(
                user_id=user_id,
                tax_info_id=tax_info.id,
                fiscal_nacional_id=api_response.get('id'),
                fiscal_nacional_reference=api_response['reference'],
                stripe_invoice_id=stripe_invoice_id,
                stripe_payment_intent_id=stripe_payment_intent_id,
                stripe_charge_id=stripe_charge_id,
                transaction_type=transaction_type,
                nfse_number=api_response.get('nfse_number'),
                status=api_response['status'],
                service_description=service_description,
                product_name=product_name,
                value_brl=amount_brl,
                value_usd=original_amount
                if original_currency == 'USD'
                else None,
                original_amount=original_amount,
                original_currency=original_currency,
                iss_rate=api_response.get('iss_rate', 0.02),
                iss_value=api_response.get('iss_value', 0.0),
                customer_name=tax_info.full_name,
                customer_email=customer_email,
                customer_country=tax_info.country,
                customer_document=(
                    tax_info.cpf_cnpj
                    if tax_info.is_brazilian
                    else tax_info.nif
                ),
                issued_at=(
                    datetime.fromisoformat(api_response['issued_at'])
                    if api_response.get('issued_at')
                    else None
                ),
            )

            self.db.add(nfse)
            await self.db.commit()
            await self.db.refresh(nfse)

            logger.info(
                f'NFS-e created: {nfse.fiscal_nacional_reference} '
                f'for user {user_id}'
            )

            return nfse

        except FiscalNacionalApiError as e:
            # Create error record
            nfse = NFSe(
                user_id=user_id,
                tax_info_id=tax_info.id,
                fiscal_nacional_reference=external_reference,
                stripe_invoice_id=stripe_invoice_id,
                stripe_payment_intent_id=stripe_payment_intent_id,
                stripe_charge_id=stripe_charge_id,
                transaction_type=transaction_type,
                status='error',
                service_description=service_description,
                product_name=product_name,
                value_brl=amount_brl,
                value_usd=original_amount
                if original_currency == 'USD'
                else None,
                original_amount=original_amount,
                original_currency=original_currency,
                customer_name=tax_info.full_name,
                customer_email=customer_email,
                customer_country=tax_info.country,
                error_message=str(e),
                error_details=str(e.response_data),
            )

            self.db.add(nfse)
            await self.db.commit()
            await self.db.refresh(nfse)

            logger.error(f'Failed to create NFS-e for user {user_id}: {e}')

            # Notify admin
            if self.admin_email:
                await self._send_error_notification(nfse, str(e))

            return nfse

    async def sync_nfse(self, nfse_id: int) -> NFSe:
        """Sync NFS-e status with Fiscal Nacional API."""
        nfse = await self._get_nfse_by_id(nfse_id)
        if not nfse:
            raise ValueError(f'NFS-e {nfse_id} not found')

        try:
            status_response = await self.fiscal_client.get_nfse_status(
                nfse.fiscal_nacional_reference
            )

            # Update record
            nfse.status = status_response['status']
            nfse.nfse_number = status_response.get('nfse_number')
            nfse.error_message = status_response.get('error_message')

            if status_response.get('issued_at'):
                nfse.issued_at = datetime.fromisoformat(
                    status_response['issued_at']
                )

            await self.db.commit()
            await self.db.refresh(nfse)

            logger.info(f'NFS-e {nfse.id} synced: status={nfse.status}')

            return nfse

        except FiscalNacionalApiError as e:
            logger.error(f'Failed to sync NFS-e {nfse_id}: {e}')
            raise

    async def cancel_nfse(self, nfse_id: int, reason: str) -> NFSe:
        """Cancel NFS-e (for refunds)."""
        nfse = await self._get_nfse_by_id(nfse_id)
        if not nfse:
            raise ValueError(f'NFS-e {nfse_id} not found')

        if nfse.status != 'authorized':
            raise ValueError(f'Cannot cancel NFS-e with status {nfse.status}')

        try:
            await self.fiscal_client.cancel_nfse(
                nfse.fiscal_nacional_reference, reason
            )

            nfse.status = 'cancelled'
            nfse.cancelled_at = datetime.now(UTC)
            nfse.cancellation_reason = reason

            await self.db.commit()
            await self.db.refresh(nfse)

            logger.info(f'NFS-e {nfse.id} cancelled: {reason}')

            return nfse

        except FiscalNacionalApiError as e:
            logger.error(f'Failed to cancel NFS-e {nfse_id}: {e}')
            raise

    async def find_by_stripe_charge_id(self, charge_id: str) -> Optional[NFSe]:
        """Find NFS-e by Stripe charge ID."""
        result = await self.db.execute(
            select(NFSe).where(NFSe.stripe_charge_id == charge_id)
        )
        return result.scalar_one_or_none()

    async def find_by_stripe_invoice_id(
        self, invoice_id: str
    ) -> Optional[NFSe]:
        """Find NFS-e by Stripe invoice ID."""
        result = await self.db.execute(
            select(NFSe).where(NFSe.stripe_invoice_id == invoice_id)
        )
        return result.scalar_one_or_none()

    async def list_user_nfse(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> list[NFSe]:
        """List NFS-e records for a user."""
        result = await self.db.execute(
            select(NFSe)
            .where(NFSe.user_id == user_id)
            .order_by(desc(NFSe.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def _get_user_tax_info(self, user_id: int) -> Optional[UserTaxInfo]:
        """Get user's tax information."""
        result = await self.db.execute(
            select(UserTaxInfo).where(UserTaxInfo.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def _get_nfse_by_id(self, nfse_id: int) -> Optional[NFSe]:
        """Get NFS-e by ID."""
        result = await self.db.execute(select(NFSe).where(NFSe.id == nfse_id))
        return result.scalar_one_or_none()

    async def _send_error_notification(self, nfse: NFSe, error: str) -> None:
        """Send error notification to admin."""
        if not self.admin_email:
            return

        try:
            await self.email_service.send_email(
                to_email=self.admin_email,
                subject=f'NFS-e Error: {nfse.fiscal_nacional_reference}',
                html_content=f"""
                <h2>NFS-e Generation Error</h2>
                <p><strong>Reference:</strong> {nfse.fiscal_nacional_reference}</p>
                <p><strong>User:</strong> {nfse.user_id}</p>
                <p><strong>Customer:</strong> {nfse.customer_name}</p>
                <p><strong>Amount:</strong> R$ {nfse.value_brl:.2f}</p>
                <p><strong>Error:</strong></p>
                <pre>{error}</pre>
                """,
            )
        except Exception as e:
            logger.error(f'Failed to send error notification: {e}')
