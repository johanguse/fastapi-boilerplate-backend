from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from src.auth.models import User
from src.organizations import service as org_service
from src.organizations.models import Organization, OrganizationInvitation


class FakeResult:
    def __init__(self, scalar_value=None, scalars_list=None):
        self._scalar = scalar_value
        self._scalars_list = scalars_list or []

    def scalar(self):
        return self._scalar

    def scalar_one_or_none(self):
        return self._scalar

    class _Scalars:
        def __init__(self, items):
            self._items = items

        def all(self):
            return list(self._items)

    def scalars(self):
        return FakeResult._Scalars(self._scalars_list)


class FakeSession:
    def __init__(self, results=None):
        self._results = list(results or [])
        self.added = []
        self.commits = 0

    async def execute(self, *_args, **_kwargs):
        if self._results:
            return self._results.pop(0)
        return FakeResult()

    async def commit(self):
        self.commits += 1

    async def refresh(self, obj):
        # simulate DB generated id
        if getattr(obj, 'id', None) in {None, 0}:
            obj.id = 123

    def add(self, obj):
        self.added.append(obj)


def make_user(is_active=True, max_teams=3) -> User:
    u = User()
    u.id = 1
    u.email = 'user@example.com'
    u.is_active = is_active
    u.max_teams = max_teams
    return u


@pytest.mark.asyncio
async def test_create_organization_inactive_user_raises():
    db = FakeSession()
    user = make_user(is_active=False)
    with pytest.raises(HTTPException) as e:
        await org_service.create_organization(
            db,
            SimpleNamespace(name='Org', slug=None, logo_url=None),
            user,
        )
    assert e.value.status_code == 403


@pytest.mark.asyncio
async def test_create_organization_duplicate_name_conflict():
    # First execute() returns an existing org for name check
    db = FakeSession(results=[FakeResult(scalar_value=Organization())])
    user = make_user()
    with pytest.raises(HTTPException) as e:
        await org_service.create_organization(
            db,
            SimpleNamespace(name='Existing', slug=None, logo_url=None),
            user,
        )
    assert e.value.status_code == 409


@pytest.mark.asyncio
async def test_create_organization_limit_reached():
    # Name check returns None, membership list returns >= max_teams
    db = FakeSession(
        results=[
            FakeResult(scalar_value=None),
            FakeResult(
                scalars_list=[Organization(), Organization(), Organization()]
            ),
        ]
    )
    user = make_user(max_teams=2)
    with pytest.raises(HTTPException) as e:
        await org_service.create_organization(
            db,
            SimpleNamespace(name='LimitOrg', slug=None, logo_url=None),
            user,
        )
    assert e.value.status_code == 403
    assert 'limit' in e.value.detail.lower()


@pytest.mark.asyncio
async def test_is_org_admin_true_false():
    org = Organization()
    org.id = 10
    user = make_user()

    # True branch
    db_true = FakeSession(results=[FakeResult(scalar_value=SimpleNamespace())])
    assert await org_service.is_org_admin(db_true, org, user) is True

    # False branch
    db_false = FakeSession(results=[FakeResult(scalar_value=None)])
    assert await org_service.is_org_admin(db_false, org, user) is False


@pytest.mark.asyncio
async def test_invite_to_organization_success(monkeypatch):
    db = FakeSession()

    org = Organization()
    org.id = 42
    org.name = 'Acme'

    # Patch helpers used by invite flow
    monkeypatch.setattr(
        org_service, 'get_organization', AsyncMock(return_value=org)
    )
    monkeypatch.setattr(
        org_service, 'is_org_admin', AsyncMock(return_value=True)
    )

    send_inv = AsyncMock()
    monkeypatch.setattr(
        'src.organizations.service.send_invitation_email', send_inv
    )

    log_activity = AsyncMock()
    monkeypatch.setattr('src.activity_log.service.log_activity', log_activity)

    user = make_user()
    invite = SimpleNamespace(email='invited@example.com', role='member')

    res = await org_service.invite_to_organization(db, org.id, invite, user)

    assert isinstance(res, OrganizationInvitation)
    assert db.commits >= 1
    send_inv.assert_awaited()
    log_activity.assert_awaited()
