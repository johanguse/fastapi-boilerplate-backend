import pytest

from src.common import security


@pytest.mark.asyncio
async def test_resolve_email_prefers_email_claim_over_sub(monkeypatch):
    payload = {'email': 'e@example.com', 'sub': 'subvalue'}
    email = security._resolve_email_from_payload(payload)
    assert email == 'e@example.com'


@pytest.mark.asyncio
async def test_better_auth_sub_is_email(monkeypatch):
    payload = {'sub': 'sub-is-email'}
    monkeypatch.setattr(security.settings, 'BETTER_AUTH_ENABLED', True)
    monkeypatch.setattr(security.settings, 'BETTER_AUTH_SUB_IS_EMAIL', True)
    email = security._resolve_email_from_payload(payload)
    assert email == 'sub-is-email'
