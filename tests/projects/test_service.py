import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi import HTTPException

from src.auth.models import User
from src.projects.models import Project
from src.projects import service as proj_service


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
        self.deleted = []

    async def execute(self, *_args, **_kwargs):
        if self._results:
            return self._results.pop(0)
        return FakeResult()

    async def commit(self):
        self.commits += 1

    async def refresh(self, obj):
        if getattr(obj, 'id', None) in (None, 0):
            obj.id = 777

    def add(self, obj):
        self.added.append(obj)

    async def delete(self, obj):
        self.deleted.append(obj)


def make_user() -> User:
    u = User()
    u.id = 1
    u.email = 'user@example.com'
    u.is_active = True
    return u


@pytest.mark.asyncio
async def test_create_project_membership_required(monkeypatch):
    db = FakeSession()
    user = make_user()

    monkeypatch.setattr(proj_service, 'is_org_member', AsyncMock(return_value=False))

    with pytest.raises(Exception) as e:
        await proj_service.create_project(
            db,
            SimpleNamespace(name='P', description=None, organization_id=1),
            user,
        )
    assert 'member' in str(e.value).lower()


@pytest.mark.asyncio
async def test_create_project_plan_limits(monkeypatch):
    class OrgObj:
        def __init__(self, plan, active):
            self.plan_name = plan
            self.active_projects = active

    db = FakeSession()
    user = make_user()

    monkeypatch.setattr(proj_service, 'is_org_member', AsyncMock(return_value=True))

    # starter limit
    monkeypatch.setattr(proj_service, 'get_organization', AsyncMock(return_value=OrgObj('starter', 1)))
    with pytest.raises(HTTPException) as e1:
        await proj_service.create_project(db, SimpleNamespace(name='P', description=None, organization_id=1), user)
    assert e1.value.status_code == 403

    # pro limit
    monkeypatch.setattr(proj_service, 'get_organization', AsyncMock(return_value=OrgObj('pro', proj_service.MAX_PRO_PROJECTS)))
    with pytest.raises(HTTPException) as e2:
        await proj_service.create_project(db, SimpleNamespace(name='P', description=None, organization_id=1), user)
    assert e2.value.status_code == 403

    # business limit
    monkeypatch.setattr(proj_service, 'get_organization', AsyncMock(return_value=OrgObj('business', proj_service.MAX_BUSINESS_PROJECTS)))
    with pytest.raises(HTTPException) as e3:
        await proj_service.create_project(db, SimpleNamespace(name='P', description=None, organization_id=1), user)
    assert e3.value.status_code == 403


@pytest.mark.asyncio
async def test_get_project_and_update_and_delete(monkeypatch):
    user = make_user()

    proj = Project()
    proj.id = 9
    proj.name = 'X'
    proj.description = None
    proj.organization_id = 5

    # get_project success
    db = FakeSession(results=[FakeResult(scalar_value=proj)])
    monkeypatch.setattr(proj_service, 'is_org_member', AsyncMock(return_value=True))
    got = await proj_service.get_project(db, 9, user)
    assert got.id == 9

    # update_project path
    db2 = FakeSession(results=[FakeResult(scalar_value=proj)])
    upd = await proj_service.update_project(db2, 9, SimpleNamespace(model_dump=lambda **_: {'name': 'Y'}), user)
    assert upd.name == 'Y'
    assert db2.commits >= 1

    # delete_project path
    db3 = FakeSession(results=[FakeResult(scalar_value=proj)])
    await proj_service.delete_project(db3, 9, user)
    assert db3.commits >= 1


@pytest.mark.asyncio
async def test_create_project_success(monkeypatch):
    """Test successful project creation"""
    class OrgObj:
        def __init__(self, plan, active):
            self.plan_name = plan
            self.active_projects = active

    db = FakeSession()
    user = make_user()
    
    # Mock successful org membership and limits check
    monkeypatch.setattr(proj_service, 'is_org_member', AsyncMock(return_value=True))
    org = OrgObj('pro', 2)  # Under limit
    monkeypatch.setattr(proj_service, 'get_organization', AsyncMock(return_value=org))

    project_data = SimpleNamespace(name='Test Project', description='Test description', organization_id=1)
    result = await proj_service.create_project(db, project_data, user)
    
    assert result.name == 'Test Project'
    assert result.description == 'Test description'
    assert result.organization_id == 1
    assert db.commits >= 2  # One for project creation, one for updating org active_projects
    assert org.active_projects == 3  # Should be incremented


@pytest.mark.asyncio
async def test_get_project_not_found(monkeypatch):
    """Test getting a project that doesn't exist"""
    db = FakeSession(results=[FakeResult(scalar_value=None)])
    user = make_user()
    
    with pytest.raises(Exception) as e:
        await proj_service.get_project(db, 999, user)
    assert 'not found' in str(e.value).lower()


@pytest.mark.asyncio
async def test_get_project_permission_denied(monkeypatch):
    """Test getting a project when user is not org member"""
    proj = Project()
    proj.id = 9
    proj.name = 'X'
    proj.description = None
    proj.organization_id = 5
    
    db = FakeSession(results=[FakeResult(scalar_value=proj)])
    user = make_user()
    monkeypatch.setattr(proj_service, 'is_org_member', AsyncMock(return_value=False))
    
    with pytest.raises(Exception) as e:
        await proj_service.get_project(db, 9, user)
    assert 'member' in str(e.value).lower()


@pytest.mark.asyncio 
async def test_get_projects_success(monkeypatch):
    """Test getting all projects for a user"""
    projects = [
        Project(id=1, name='Project 1', organization_id=1),
        Project(id=2, name='Project 2', organization_id=1),
    ]
    
    db = FakeSession(results=[FakeResult(scalars_list=projects)])
    user = make_user()
    
    result = await proj_service.get_projects(db, user)
    assert len(result) == 2
    assert result[0].name == 'Project 1'
    assert result[1].name == 'Project 2'


@pytest.mark.asyncio
async def test_update_project_success(monkeypatch):
    """Test successful project update"""
    proj = Project()
    proj.id = 9
    proj.name = 'Old Name'
    proj.description = 'Old Description'
    proj.organization_id = 5
    
    db = FakeSession(results=[FakeResult(scalar_value=proj)])
    user = make_user()
    monkeypatch.setattr(proj_service, 'is_org_member', AsyncMock(return_value=True))
    
    update_data = SimpleNamespace(model_dump=lambda **_: {'name': 'New Name', 'description': 'New Description'})
    result = await proj_service.update_project(db, 9, update_data, user)
    
    assert result.name == 'New Name'
    assert result.description == 'New Description'
    assert db.commits >= 1
