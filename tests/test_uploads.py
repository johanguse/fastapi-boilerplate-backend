import pytest

from src.common.config import settings


@pytest.mark.asyncio
async def test_upload_file_unsupported_type(authenticated_client, monkeypatch):
    # Make allowed types only images to force rejection
    monkeypatch.setattr(
        settings, 'ALLOWED_FILE_TYPES', ['image/png'], raising=False
    )
    files = {'file': ('test.txt', b'hello', 'text/plain')}
    resp = await authenticated_client.post('/api/v1/uploads/', files=files)
    assert resp.status_code == 400
    assert resp.json()['detail'].lower().startswith('unsupported')


@pytest.mark.asyncio
async def test_upload_file_storage_failure(authenticated_client, monkeypatch):
    # Allow text/plain, but force storage to fail
    monkeypatch.setattr(
        settings, 'ALLOWED_FILE_TYPES', ['text/plain'], raising=False
    )
    from src.uploads import routes as upload_routes

    async def fake_upload_file_to_r2(*args, **kwargs):
        return None

    # Patch the symbol used by the route module, not the storage module
    monkeypatch.setattr(
        upload_routes, 'upload_file_to_r2', fake_upload_file_to_r2
    )
    files = {'file': ('note.txt', b'data', 'text/plain')}
    resp = await authenticated_client.post('/api/v1/uploads/', files=files)
    assert resp.status_code == 500
    assert resp.json()['detail'].lower().startswith('upload failed')


@pytest.mark.asyncio
async def test_delete_file_failure(authenticated_client, monkeypatch):
    from src.uploads import routes as upload_routes

    async def fake_delete_file_from_r2(*args, **kwargs):
        return False

    monkeypatch.setattr(
        upload_routes, 'delete_file_from_r2', fake_delete_file_from_r2
    )
    resp = await authenticated_client.delete('/api/v1/uploads/missing.txt')
    assert resp.status_code == 404
    assert 'not found' in resp.json()['detail'].lower()


@pytest.mark.asyncio
async def test_get_presigned_url_failure(authenticated_client, monkeypatch):
    from src.uploads import routes as upload_routes

    async def fake_get_file_url(*args, **kwargs):
        return None

    monkeypatch.setattr(upload_routes, 'get_file_url', fake_get_file_url)
    resp = await authenticated_client.get('/api/v1/uploads/missing.txt/url')
    assert resp.status_code == 404
    assert 'not found' in resp.json()['detail'].lower()
