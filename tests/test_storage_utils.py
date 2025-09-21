import pytest

pytest.skip("deprecated duplicate; moved to tests/common", allow_module_level=True)

from botocore.exceptions import ClientError
from src.utils import storage as storage_utils


class DummyClient:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail

    def put_object(self, **kwargs):
        if self.should_fail:
            raise ClientError({"Error": {"Code": "500", "Message": "fail"}}, "PutObject")
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}

    def delete_object(self, **kwargs):
        if self.should_fail:
            raise ClientError({"Error": {"Code": "500", "Message": "fail"}}, "DeleteObject")
        return {"ResponseMetadata": {"HTTPStatusCode": 204}}

    def generate_presigned_url(self, *args, **kwargs):
        if self.should_fail:
            raise ClientError({"Error": {"Code": "500", "Message": "fail"}}, "GeneratePresignedUrl")
        return "https://r2.example.com/bucket/key"


@pytest.mark.asyncio
async def test_upload_file_to_r2_success(monkeypatch):
    monkeypatch.setattr(storage_utils, "get_r2_client", lambda: DummyClient(should_fail=False))
    url = await storage_utils.upload_file_to_r2(b"data", "key.txt", "text/plain")
    assert url and url.endswith("/key.txt")


@pytest.mark.asyncio
async def test_upload_file_to_r2_failure(monkeypatch):
    monkeypatch.setattr(storage_utils, "get_r2_client", lambda: DummyClient(should_fail=True))
    url = await storage_utils.upload_file_to_r2(b"data", "key.txt", "text/plain")
    assert url is None


@pytest.mark.asyncio
async def test_delete_file_from_r2_success(monkeypatch):
    monkeypatch.setattr(storage_utils, "get_r2_client", lambda: DummyClient(should_fail=False))
    ok = await storage_utils.delete_file_from_r2("key.txt")
    assert ok is True


@pytest.mark.asyncio
async def test_delete_file_from_r2_failure(monkeypatch):
    monkeypatch.setattr(storage_utils, "get_r2_client", lambda: DummyClient(should_fail=True))
    ok = await storage_utils.delete_file_from_r2("key.txt")
    assert ok is False


@pytest.mark.asyncio
async def test_get_file_url_success(monkeypatch):
    monkeypatch.setattr(storage_utils, "get_r2_client", lambda: DummyClient(should_fail=False))
    url = await storage_utils.get_file_url("key.txt")
    assert url.startswith("http")


@pytest.mark.asyncio
async def test_get_file_url_failure(monkeypatch):
    monkeypatch.setattr(storage_utils, "get_r2_client", lambda: DummyClient(should_fail=True))
    url = await storage_utils.get_file_url("key.txt")
    assert url is None
