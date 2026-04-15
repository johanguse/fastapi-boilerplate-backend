"""
Currency Conversion Service for NFS-e generation.

Implements a robust currency conversion strategy:
1. Primary: Stripe Balance Transaction (exact exchange rate)
2. Fallback: PTAX (Banco Central do Brasil official rate)
3. Emergency: Conservative fallback rate

This ensures accurate tax reporting for both domestic and international customers.
"""

import logging
from datetime import date, datetime
from typing import Optional

import httpx
import stripe

from src.common.config import settings
from src.utils.currencies import CURRENCIES, get_currency

logger = logging.getLogger(__name__)


# ============================================================================
# Types
# ============================================================================


class CurrencyConversionResult:
    """Result of currency conversion with audit trail."""

    def __init__(
        self,
        amount_brl: float,
        original_amount: float,
        original_currency: str,
        exchange_rate: float,
        source: str,
        rate_date: str,
        audit_description: str,
        stripe_fees_brl: Optional[float] = None,
        net_amount_brl: Optional[float] = None,
    ):
        self.amount_brl = amount_brl
        self.original_amount = original_amount
        self.original_currency = original_currency
        self.exchange_rate = exchange_rate
        self.source = source
        self.rate_date = rate_date
        self.audit_description = audit_description
        self.stripe_fees_brl = stripe_fees_brl
        self.net_amount_brl = net_amount_brl


class StripeBalanceInfo:
    """Stripe balance transaction information."""

    def __init__(
        self,
        gross_amount_brl: float,
        fees_brl: float,
        net_amount_brl: float,
        exchange_rate: float,
        original_amount: float,
        original_currency: str,
    ):
        self.gross_amount_brl = gross_amount_brl
        self.fees_brl = fees_brl
        self.net_amount_brl = net_amount_brl
        self.exchange_rate = exchange_rate
        self.original_amount = original_amount
        self.original_currency = original_currency


class PTAXRate:
    """PTAX exchange rate from Banco Central do Brasil."""

    def __init__(self, buy_rate: float, sell_rate: float, rate_date: str):
        self.buy_rate = buy_rate
        self.sell_rate = sell_rate
        self.date = rate_date


# Currency code mappings
ISO_TO_BACEN = {c['code']: c['bacen_code'] for c in CURRENCIES}
BACEN_TO_ISO = {c['bacen_code']: c['code'] for c in CURRENCIES}

# Conservative fallback rates (update periodically)
FALLBACK_RATES = {
    'USD': 5.5,
    'EUR': 6.0,
    'GBP': 7.0,
    'CAD': 4.0,
    'AUD': 3.5,
    'JPY': 0.037,
    'CHF': 6.2,
}


# ============================================================================
# Currency Conversion Service
# ============================================================================


class CurrencyConversionService:
    """Service for converting foreign currencies to BRL."""

    def __init__(self, stripe_api_key: Optional[str] = None):
        """Initialize service with Stripe API key."""
        api_key = stripe_api_key or settings.STRIPE_SECRET_KEY
        self._client = stripe.StripeClient(api_key)

    async def get_stripe_balance_info(
        self, charge_id: str
    ) -> Optional[StripeBalanceInfo]:
        """
        Get BRL amount from Stripe balance transaction.
        This is the most accurate source as it reflects actual bank settlement.
        """
        try:
            # Retrieve charge with balance transaction expanded
            charge = self._client.v1.charges.retrieve(
                charge_id, params={'expand': ['balance_transaction']}
            )

            balance_transaction = charge.balance_transaction

            if not balance_transaction or isinstance(balance_transaction, str):
                logger.info(
                    f'Balance transaction not available for charge {charge_id}'
                )
                return None

            # Check if settled in BRL
            if balance_transaction.currency != 'brl':
                logger.info(
                    f'Balance transaction for {charge_id} is in '
                    f'{balance_transaction.currency}, not BRL'
                )

            # Extract amounts (in smallest unit - centavos)
            gross_amount = balance_transaction.amount
            fee_amount = balance_transaction.fee
            net_amount = balance_transaction.net

            # Calculate exchange rate if original currency is different
            exchange_rate = 1.0
            original_currency = charge.currency.upper()

            if original_currency != 'BRL':
                original_amount = charge.amount
                # exchange_rate = BRL amount / foreign amount
                exchange_rate = gross_amount / original_amount

            return StripeBalanceInfo(
                gross_amount_brl=gross_amount / 100,  # Convert to BRL
                fees_brl=fee_amount / 100,
                net_amount_brl=net_amount / 100,
                exchange_rate=exchange_rate,
                original_amount=charge.amount,
                original_currency=original_currency,
            )

        except Exception as e:
            logger.error(
                f'Failed to get balance transaction for charge {charge_id}: {e}'
            )
            return None

    async def get_stripe_balance_info_from_payment_intent(
        self, payment_intent_id: str
    ) -> Optional[StripeBalanceInfo]:
        """Get balance info from payment intent."""
        try:
            # Retrieve payment intent with latest charge
            payment_intent = self._client.v1.payment_intents.retrieve(
                payment_intent_id,
                params={'expand': ['latest_charge.balance_transaction']},
            )

            charge = payment_intent.latest_charge

            if not charge or isinstance(charge, str):
                logger.info(
                    f'No charge found for payment intent {payment_intent_id}'
                )
                return None

            return await self.get_stripe_balance_info(charge.id)

        except Exception as e:
            logger.error(
                f'Failed to get balance info from payment intent '
                f'{payment_intent_id}: {e}'
            )
            return None

    async def get_ptax_rate(
        self, currency: str, target_date: Optional[date] = None
    ) -> Optional[PTAXRate]:
        """
        Get PTAX exchange rate from Banco Central do Brasil.
        PTAX is the official rate for tax purposes.
        """
        try:
            target = target_date or date.today()
            formatted_date = self._format_date_for_bacen(target)

            # Get BACEN code
            bacen_code = ISO_TO_BACEN.get(currency.upper())
            if not bacen_code:
                logger.warning(
                    f'No BACEN code mapping for currency: {currency}'
                )
                return None

            # BACEN PTAX API
            url = (
                f'https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/'
                f'CotacaoMoedaDia(moeda=@moeda,dataCotacao=@data)?'
                f"@moeda='{currency}'&@data='{formatted_date}'&$format=json"
            )

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url, headers={'Accept': 'application/json'}
                )

                if response.status_code != 200:
                    logger.error(f'PTAX API returned {response.status_code}')
                    return None

                data = response.json()

                if not data.get('value'):
                    # Try previous business day
                    logger.info(
                        f'No PTAX rate for {formatted_date}, trying previous day'
                    )
                    from datetime import timedelta

                    previous_day = target - timedelta(days=1)

                    # Only try 7 days back
                    if (target - previous_day).days <= 7:
                        return await self.get_ptax_rate(currency, previous_day)

                    return None

                # Get latest rate of the day
                latest_rate = data['value'][-1]

                return PTAXRate(
                    buy_rate=latest_rate['cotacaoCompra'],
                    sell_rate=latest_rate['cotacaoVenda'],
                    rate_date=latest_rate['dataHoraCotacao'],
                )

        except Exception as e:
            logger.error(f'Failed to get PTAX rate for {currency}: {e}')
            return None

    def get_fallback_rate(self, currency: str) -> float:
        """Get fallback exchange rate."""
        rate = FALLBACK_RATES.get(currency.upper())
        if not rate:
            logger.warning(
                f'No fallback rate for {currency}, using 5.5 (USD default)'
            )
            return 5.5
        return rate

    async def convert_to_brl(
        self,
        amount: float,
        currency: str,
        charge_id: Optional[str] = None,
        payment_intent_id: Optional[str] = None,
    ) -> CurrencyConversionResult:
        """
        Convert foreign currency to BRL with full audit trail.
        Implements: Stripe > PTAX > Fallback hierarchy.
        """
        currency_upper = currency.upper()

        # No conversion needed for BRL
        if currency_upper == 'BRL':
            return CurrencyConversionResult(
                amount_brl=amount,
                original_amount=amount,
                original_currency='BRL',
                exchange_rate=1.0,
                source='stripe_balance',
                rate_date=datetime.now().isoformat(),
                audit_description='Pagamento em BRL - sem conversão necessária',
            )

        today = datetime.now().date().isoformat()

        # 1. Try Stripe Balance Transaction (most accurate)
        if charge_id:
            stripe_info = await self.get_stripe_balance_info(charge_id)
            if stripe_info:
                return CurrencyConversionResult(
                    amount_brl=stripe_info.gross_amount_brl,
                    original_amount=amount,
                    original_currency=currency_upper,
                    exchange_rate=stripe_info.exchange_rate,
                    source='stripe_balance',
                    stripe_fees_brl=stripe_info.fees_brl,
                    net_amount_brl=stripe_info.net_amount_brl,
                    rate_date=today,
                    audit_description=self._build_audit_description(
                        amount,
                        currency_upper,
                        stripe_info.exchange_rate,
                        'stripe_balance',
                        stripe_info.fees_brl,
                    ),
                )

        if payment_intent_id:
            stripe_info = (
                await self.get_stripe_balance_info_from_payment_intent(
                    payment_intent_id
                )
            )
            if stripe_info:
                return CurrencyConversionResult(
                    amount_brl=stripe_info.gross_amount_brl,
                    original_amount=amount,
                    original_currency=currency_upper,
                    exchange_rate=stripe_info.exchange_rate,
                    source='stripe_balance',
                    stripe_fees_brl=stripe_info.fees_brl,
                    net_amount_brl=stripe_info.net_amount_brl,
                    rate_date=today,
                    audit_description=self._build_audit_description(
                        amount,
                        currency_upper,
                        stripe_info.exchange_rate,
                        'stripe_balance',
                        stripe_info.fees_brl,
                    ),
                )

        # 2. Try PTAX (official rate for tax compliance)
        ptax_rate = await self.get_ptax_rate(currency_upper)
        if ptax_rate:
            # Use sell rate for conversion to BRL
            amount_brl = amount * ptax_rate.sell_rate
            return CurrencyConversionResult(
                amount_brl=amount_brl,
                original_amount=amount,
                original_currency=currency_upper,
                exchange_rate=ptax_rate.sell_rate,
                source='ptax',
                rate_date=ptax_rate.date,
                audit_description=self._build_audit_description(
                    amount,
                    currency_upper,
                    ptax_rate.sell_rate,
                    'ptax',
                ),
            )

        # 3. Fallback to conservative rate
        fallback_rate = self.get_fallback_rate(currency_upper)
        amount_brl = amount * fallback_rate

        logger.warning(
            f'Using fallback rate for {currency_upper}: {fallback_rate}'
        )

        return CurrencyConversionResult(
            amount_brl=amount_brl,
            original_amount=amount,
            original_currency=currency_upper,
            exchange_rate=fallback_rate,
            source='fallback',
            rate_date=today,
            audit_description=self._build_audit_description(
                amount, currency_upper, fallback_rate, 'fallback'
            ),
        )

    def _build_audit_description(
        self,
        original_amount: float,
        currency: str,
        rate: float,
        source: str,
        fees: Optional[float] = None,
    ) -> str:
        """Build audit description for NFS-e."""
        source_labels = {
            'stripe_balance': 'Taxa de Conversão Stripe',
            'ptax': 'Taxa PTAX (Banco Central)',
            'fallback': 'Taxa de Conversão Estimada',
        }

        currency_obj = get_currency(currency)
        symbol = currency_obj['symbol'] if currency_obj else currency

        description = (
            f'Valor original: {symbol}{original_amount:.2f} - '
            f'{source_labels[source]}: R$ {rate:.4f}'
        )

        if fees and fees > 0:
            description += f' - Taxas operacionais: R$ {fees:.2f}'

        return description

    @staticmethod
    def _format_date_for_bacen(target_date: date) -> str:
        """Format date for BACEN API (MM-DD-YYYY)."""
        return target_date.strftime('%m-%d-%Y')

    @staticmethod
    def get_bacen_code(iso_currency: str) -> Optional[str]:
        """Get BACEN currency code from ISO code."""
        return ISO_TO_BACEN.get(iso_currency.upper())

    @staticmethod
    def get_iso_code(bacen_code: str) -> Optional[str]:
        """Get ISO currency code from BACEN code."""
        return BACEN_TO_ISO.get(bacen_code)


# ============================================================================
# Factory function
# ============================================================================


def create_currency_conversion_service(
    stripe_api_key: Optional[str] = None,
) -> CurrencyConversionService:
    """Create currency conversion service instance."""
    return CurrencyConversionService(stripe_api_key)
