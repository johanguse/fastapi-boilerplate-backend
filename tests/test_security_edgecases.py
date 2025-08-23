import pytest

from src.common import security


@pytest.mark.asyncio
async def test_resolve_email_prefers_email_claim_over_sub(monkeypatch):
    # Ensure default behavior prefers email over sub
    payload = {'email': 'e@example.com', 'sub': 'subvalue'}
    # BETTER_AUTH_* flags shouldn't affect when token is decoded already; just check resolver
    email = security._resolve_email_from_payload(payload)
    assert email == 'e@example.com'


@pytest.mark.asyncio
async def test_better_auth_sub_is_email(monkeypatch):
    # When enabled, resolver returns sub if email missing
    payload = {'sub': 'sub-is-email'}
    monkeypatch.setattr(security.settings, 'BETTER_AUTH_ENABLED', True)
    monkeypatch.setattr(security.settings, 'BETTER_AUTH_SUB_IS_EMAIL', True)
    email = security._resolve_email_from_payload(payload)
    assert email == 'sub-is-email'
