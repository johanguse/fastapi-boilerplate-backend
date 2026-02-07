"""Fiscal Nacional External API Client for NFS-e Generation.

Integrates with Fiscal Nacional API for Brazilian electronic service invoices.
See: docs/external-api-integration.md
"""

from typing import Optional

import httpx

from src.utils.currencies import get_bacen_code

# ============================================================================
# Configuration
# ============================================================================

FISCAL_NACIONAL_CONFIG = {
    # Company info - UPDATE WITH YOUR COMPANY DATA
    'company_name': 'YOUR COMPANY NAME',
    'cnpj': '00000000000000',
    'inscricao_municipal': '000000',
    'city_code': 0000000,  # IBGE code
    'iss_rate': 0.02,  # 2% ISS rate
}

# API Base URLs
API_URLS = {
    'production': 'https://api.fiscalnacional.com.br',
    'staging': 'https://api-staging.fiscalnacional.com.br',
    'development': 'https://api-staging.fiscalnacional.com.br',
}


# ============================================================================
# Types
# ============================================================================

class FiscalNacionalConfig:
    """Configuration for Fiscal Nacional API."""

    def __init__(
        self,
        api_key: str,
        environment: str = 'production',
    ):
        self.api_key = api_key
        self.environment = environment


class CreateNFSeRequest:
    """Request to create a new NFS-e."""

    def __init__(
        self,
        customer_name: str,
        service_description: str,
        amount: float,
        customer_email: Optional[str] = None,
        customer_country: Optional[str] = None,
        customer_country_iso2: Optional[str] = None,
        customer_document: Optional[str] = None,
        customer_nif: Optional[str] = None,
        nif_exemption_code: Optional[int] = None,
        currency_code: Optional[str] = None,
        foreign_currency_amount: Optional[float] = None,
        customer_address: Optional[str] = None,
        customer_number: Optional[str] = None,
        customer_complement: Optional[str] = None,
        customer_neighborhood: Optional[str] = None,
        customer_postal_code: Optional[str] = None,
        customer_state: Optional[str] = None,
        customer_city_name: Optional[str] = None,
        customer_city_code: Optional[int] = None,
        customer_inscricao_municipal: Optional[str] = None,
        external_reference: Optional[str] = None,
        product_name: Optional[str] = None,
    ):
        self.customer_name = customer_name
        self.service_description = service_description
        self.amount = amount
        self.customer_email = customer_email
        self.customer_country = customer_country
        self.customer_country_iso2 = customer_country_iso2
        self.customer_document = customer_document
        self.customer_nif = customer_nif
        self.nif_exemption_code = nif_exemption_code
        self.currency_code = currency_code
        self.foreign_currency_amount = foreign_currency_amount
        self.customer_address = customer_address
        self.customer_number = customer_number
        self.customer_complement = customer_complement
        self.customer_neighborhood = customer_neighborhood
        self.customer_postal_code = customer_postal_code
        self.customer_state = customer_state
        self.customer_city_name = customer_city_name
        self.customer_city_code = customer_city_code
        self.customer_inscricao_municipal = customer_inscricao_municipal
        self.external_reference = external_reference
        self.product_name = product_name

    def to_dict(self) -> dict:
        """Convert to API request dict."""
        data = {
            'customer_name': self.customer_name,
            'service_description': self.service_description,
            'amount': self.amount,
        }

        # Add optional fields if present
        optional_fields = [
            'customer_email',
            'customer_country',
            'customer_country_iso2',
            'customer_document',
            'customer_nif',
            'nif_exemption_code',
            'currency_code',
            'foreign_currency_amount',
            'customer_address',
            'customer_number',
            'customer_complement',
            'customer_neighborhood',
            'customer_postal_code',
            'customer_state',
            'customer_city_name',
            'customer_city_code',
            'customer_inscricao_municipal',
            'external_reference',
            'product_name',
        ]

        for field in optional_fields:
            value = getattr(self, field)
            if value is not None:
                data[field] = value

        return data


# ============================================================================
# Fiscal Nacional Client
# ============================================================================

class FiscalNacionalClient:
    """Client for Fiscal Nacional External API."""

    def __init__(self, config: FiscalNacionalConfig):
        self.config = config
        self.base_url = API_URLS[config.environment]

    async def create_nfse(
        self, request: CreateNFSeRequest
    ) -> dict:
        """Create a new NFS-e."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{self.base_url}/api/v1/external/nfse',
                json=request.to_dict(),
                headers={
                    'X-API-Key': self.config.api_key,
                    'Content-Type': 'application/json',
                },
                timeout=30.0,
            )

            if response.status_code != 201:
                error_data = response.json()
                raise FiscalNacionalApiError(
                    f'Failed to create NFS-e: {self._format_error_message(error_data)}',
                    response.status_code,
                    error_data,
                )

            return response.json()

    async def get_nfse_status(self, reference: str) -> dict:
        """Check NFS-e status."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'{self.base_url}/api/v1/external/nfse/{reference}',
                headers={'X-API-Key': self.config.api_key},
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = response.json()
                raise FiscalNacionalApiError(
                    f'Failed to get NFS-e status: {self._format_error_message(error_data)}',
                    response.status_code,
                    error_data,
                )

            return response.json()

    async def get_download_urls(self, reference: str) -> dict:
        """Get download URLs for NFS-e documents."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'{self.base_url}/api/v1/external/nfse/{reference}/download-urls',
                headers={'X-API-Key': self.config.api_key},
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = response.json()
                raise FiscalNacionalApiError(
                    f'Failed to get download URLs: {self._format_error_message(error_data)}',
                    response.status_code,
                    error_data,
                )

            return response.json()

    async def cancel_nfse(self, reference: str, reason: str) -> dict:
        """Cancel NFS-e."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{self.base_url}/api/v1/external/nfse/{reference}/cancel',
                json={'reason': reason},
                headers={
                    'X-API-Key': self.config.api_key,
                    'Content-Type': 'application/json',
                },
                timeout=30.0,
            )

            if response.status_code != 200:
                error_data = response.json()
                raise FiscalNacionalApiError(
                    f'Failed to cancel NFS-e: {self._format_error_message(error_data)}',
                    response.status_code,
                    error_data,
                )

            return response.json()

    def _format_error_message(self, error: dict) -> str:
        """Format error message from API response."""
        detail = error.get('detail', 'Unknown error')
        if isinstance(detail, list):
            messages = [
                f"{err.get('loc', ['unknown'])}: {err.get('msg', 'error')}"
                for err in detail
            ]
            return '; '.join(messages)
        return str(detail)


# ============================================================================
# Error Class
# ============================================================================

class FiscalNacionalApiError(Exception):
    """Exception raised for Fiscal Nacional API errors."""

    def __init__(
        self, message: str, status_code: int, response_data: dict
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


# ============================================================================
# Helper Functions
# ============================================================================

def build_brazilian_nfse_request(
    customer_name: str,
    customer_email: str,
    customer_document: str,
    service_description: str,
    amount_brl: float,
    address: Optional[str] = None,
    number: Optional[str] = None,
    complement: Optional[str] = None,
    neighborhood: Optional[str] = None,
    city: Optional[str] = None,
    city_code: Optional[int] = None,
    state: Optional[str] = None,
    postal_code: Optional[str] = None,
    inscricao_municipal: Optional[str] = None,
    external_reference: Optional[str] = None,
    product_name: Optional[str] = None,
) -> CreateNFSeRequest:
    """Build NFS-e request for Brazilian customer."""
    return CreateNFSeRequest(
        customer_name=customer_name,
        customer_email=customer_email,
        customer_country='BR',
        customer_document=customer_document,
        service_description=service_description,
        amount=amount_brl,
        customer_address=address,
        customer_number=number,
        customer_complement=complement,
        customer_neighborhood=neighborhood,
        customer_city_name=city,
        customer_city_code=city_code,
        customer_state=state,
        customer_postal_code=postal_code,
        customer_inscricao_municipal=inscricao_municipal,
        external_reference=external_reference,
        product_name=product_name,
    )


def build_international_nfse_request(
    customer_name: str,
    customer_email: str,
    customer_country_iso2: str,
    service_description: str,
    amount_brl: float,
    customer_nif: Optional[str] = None,
    nif_exemption_code: Optional[int] = None,
    original_currency_code: Optional[str] = None,
    original_amount: Optional[float] = None,
    external_reference: Optional[str] = None,
    product_name: Optional[str] = None,
) -> CreateNFSeRequest:
    """Build NFS-e request for international customer."""
    # Get BACEN currency code if original currency provided
    bacen_code = None
    if original_currency_code:
        bacen_code = get_bacen_code(original_currency_code)

    return CreateNFSeRequest(
        customer_name=customer_name,
        customer_email=customer_email,
        customer_country='EXTERIOR',
        customer_country_iso2=customer_country_iso2,
        customer_nif=customer_nif,
        nif_exemption_code=nif_exemption_code or 2,
        service_description=service_description,
        amount=amount_brl,
        currency_code=bacen_code,
        foreign_currency_amount=original_amount,
        external_reference=external_reference,
        product_name=product_name,
    )


def generate_external_reference(
    transaction_type: str, stripe_id: str
) -> str:
    """Generate unique external reference for NFS-e."""
    prefix = 'sub' if transaction_type == 'subscription' else 'pkg'
    return f'{prefix}_{stripe_id}'
