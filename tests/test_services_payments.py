from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi_pagination.bases import AbstractPage

from src.payments import service as pay_service


class DummySession:
    def __init__(self):
        self.commits = 0

    async def commit(self):
        self.commits += 1


class DummyOrg:
    def __init__(self, id_: int):
        self.id = id_
        self.stripe_customer_id = None
        self.stripe_subscription_id = None
        self.plan_name = None
        self.subscription_status = None
        self.max_projects = None


@pytest.mark.asyncio
async def test_create_checkout_session_updates_customer_id():
    db = DummySession()
    org = DummyOrg(7)

    class FakeStripeSession:
        def __init__(self):
            self.customer = 'cus_123'
            self.url = 'https://checkout.stripe.com/test'

    with patch(
        'src.payments.service.stripe.checkout.Session.create',
        return_value=FakeStripeSession(),
    ):
        url = await pay_service.create_checkout_session(db, org, 'price_1M')

    assert url.startswith('https://')
    assert org.stripe_customer_id == 'cus_123'
    assert db.commits >= 1


@pytest.mark.asyncio
async def test_handle_subscription_update_happy_path(monkeypatch):
    db = DummySession()
    org = DummyOrg(3)

    # Fake execute returning organization by stripe_customer_id
    class FakeResult:
        def scalar_one_or_none(self):
            return org

    async def fake_execute(*_args, **_kwargs):
        return FakeResult()

    db.execute = fake_execute  # type: ignore[attr-defined]

    event = {
        'data': {
            'object': SimpleNamespace(
                customer='cus_999',
                id='sub_001',
                status='active',
                items={'data': [{'price': {'id': 'price_1M'}}]},
            )
        }
    }

    await pay_service.handle_subscription_update(db, event)

    assert org.stripe_subscription_id == 'sub_001'
    assert org.plan_name == 'starter'
    assert org.subscription_status == 'active'
    assert (
        org.max_projects
        == pay_service.settings.STRIPE_PLANS['price_1M']['max_projects']
    )


@pytest.mark.asyncio
async def test_get_available_plans_returns_page():
    page = await pay_service.get_available_plans()
    assert isinstance(page, AbstractPage)
    assert len(page.items) >= 1
