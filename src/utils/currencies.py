"""Currency utilities for NFS-e international invoices.

Uses BACEN (Banco Central do Brasil) codes as required by Brazilian tax invoices.
See: https://www.bcb.gov.br/estabilidadefinanceira/listatabela
"""

CURRENCIES = [
    {'code': 'USD', 'bacen_code': '220', 'name': 'US Dollar', 'symbol': '$'},
    {'code': 'EUR', 'bacen_code': '978', 'name': 'Euro', 'symbol': '€'},
    {'code': 'GBP', 'bacen_code': '540', 'name': 'British Pound', 'symbol': '£'},
    {'code': 'JPY', 'bacen_code': '470', 'name': 'Japanese Yen', 'symbol': '¥'},
    {'code': 'CHF', 'bacen_code': '510', 'name': 'Swiss Franc', 'symbol': 'CHF'},
    {'code': 'CAD', 'bacen_code': '165', 'name': 'Canadian Dollar', 'symbol': 'C$'},
    {'code': 'AUD', 'bacen_code': '150', 'name': 'Australian Dollar', 'symbol': 'A$'},
    {'code': 'CNY', 'bacen_code': '160', 'name': 'Chinese Yuan', 'symbol': '¥'},
    {'code': 'ARS', 'bacen_code': '175', 'name': 'Argentine Peso', 'symbol': '$'},
    {'code': 'MXN', 'bacen_code': '615', 'name': 'Mexican Peso', 'symbol': '$'},
    {'code': 'BRL', 'bacen_code': '986', 'name': 'Brazilian Real', 'symbol': 'R$'},
]


def get_currency(code: str) -> dict | None:
    """Get currency by ISO code."""
    return next(
        (c for c in CURRENCIES if c['code'] == code.upper()), None
    )


def get_currency_by_bacen_code(bacen_code: str) -> dict | None:
    """Get currency by BACEN code."""
    return next(
        (c for c in CURRENCIES if c['bacen_code'] == bacen_code), None
    )


def get_bacen_code(currency_code: str) -> str:
    """Get BACEN code from ISO currency code."""
    currency = get_currency(currency_code)
    return currency['bacen_code'] if currency else '220'  # Default to USD


def get_default_currency_for_country(country_code: str) -> str:
    """Get default currency for a country."""
    country_to_currency = {
        'US': 'USD',
        'GB': 'GBP',
        'BR': 'BRL',
        'DE': 'EUR',
        'FR': 'EUR',
        'IT': 'EUR',
        'ES': 'EUR',
        'JP': 'JPY',
        'CN': 'CNY',
        'CA': 'CAD',
        'AU': 'AUD',
        'CH': 'CHF',
        'AR': 'ARS',
        'MX': 'MXN',
    }
    return country_to_currency.get(country_code.upper(), 'USD')
