import pytest

pytest.skip("deprecated duplicate; moved to tests/common", allow_module_level=True)

from types import SimpleNamespace

from fastapi import FastAPI

from src.common.openapi import custom_openapi


def test_custom_openapi_builds_and_caches():
    app = FastAPI()

    @app.get("/ping")
    def ping():
        return {"ok": True}

    # First call builds and caches
    schema1 = custom_openapi(app)
    assert "components" in schema1
    assert "security" in schema1
    assert "paths" in schema1
    # Paths should be prefixed by API_V1_STR
    assert any(path.startswith("/api/v1/") for path in schema1["paths"].keys())

    # Second call returns cached object
    schema2 = custom_openapi(app)
    assert schema1 is schema2
