import pytest

from src.utils import email as email_utils


@pytest.mark.real_email  # Opt-out of auto email mocking - this test controls its own mock
@pytest.mark.asyncio
async def test_send_email_success(monkeypatch):
    class FakeResponse:
        id = 'msg_123'

        def get(self, key):
            if key == 'id':
                return self.id
            return None

    class FakeEmails:
        @staticmethod
        def send(params):
            assert params['to'] == 'user@example.com'
            assert params['subject'] == 'Hello'
            return FakeResponse()

    class FakeResend:
        Emails = FakeEmails()
        api_key = 'dummy'

    # Mock settings.RESEND_API_KEY so the function doesn't return early
    monkeypatch.setattr('src.utils.email.settings.RESEND_API_KEY', 'test-api-key')
    monkeypatch.setattr(email_utils, 'resend', FakeResend())
    ok = await email_utils.send_email('user@example.com', 'Hello', '<p>hi</p>')
    assert ok is True



@pytest.mark.real_email  # Opt-out of auto email mocking - this test controls its own mock
@pytest.mark.asyncio
async def test_send_email_failure(monkeypatch):
    class FakeEmails:
        @staticmethod
        def send(params):
            raise RuntimeError('boom')

    class FakeResend:
        Emails = FakeEmails()
        api_key = 'dummy'

    # Mock settings.RESEND_API_KEY so the function doesn't return early
    monkeypatch.setattr('src.utils.email.settings.RESEND_API_KEY', 'test-api-key')
    monkeypatch.setattr(email_utils, 'resend', FakeResend())
    ok = await email_utils.send_email('user@example.com', 'Hello', '<p>hi</p>')
    assert ok is False


@pytest.mark.real_email  # Opt-out of auto email mocking - this test controls its own mock
@pytest.mark.asyncio
async def test_send_invitation_email_calls_send_email(monkeypatch):
    called = {}

    async def fake_send_email(**kwargs):
        called.update(kwargs)
        return True

    monkeypatch.setattr(email_utils, 'send_email', fake_send_email)

    ok = await email_utils.send_invitation_email(
        to_email='invitee@example.com',
        team_name='Alpha',
        invited_by_email='owner@example.com',
        frontend_url='https://web.app',
    )
    assert ok is True
    assert called['to_email'] == 'invitee@example.com'
    assert 'Alpha' in called['subject']


@pytest.mark.real_email  # Opt-out of auto email mocking - this test controls its own mock
@pytest.mark.asyncio
async def test_send_welcome_email_calls_send_email(monkeypatch):
    called = {}

    async def fake_send_email(**kwargs):
        called.update(kwargs)
        return True

    monkeypatch.setattr(email_utils, 'send_email', fake_send_email)
    ok = await email_utils.send_welcome_email(
        'new@example.com', user_name='Neo'
    )
    assert ok is True
    assert called['to_email'] == 'new@example.com'
    assert 'Welcome' in called['subject']
