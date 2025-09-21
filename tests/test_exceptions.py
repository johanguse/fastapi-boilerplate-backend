import pytest

pytest.skip("deprecated duplicate; moved to tests/common", allow_module_level=True)

from fastapi import status

from src.common.exceptions import (
    APIError,
    NotFoundError,
    PermissionError,
    ValidationError,
)


def test_apierror_init():
    err = APIError(status_code=418, detail="I'm a teapot")
    assert err.status_code == 418
    assert err.detail == "I'm a teapot"


def test_notfounderror_defaults():
    err = NotFoundError()
    assert err.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in err.detail.lower()


def test_permissionerror_defaults():
    err = PermissionError()
    assert err.status_code == status.HTTP_403_FORBIDDEN
    assert "permission" in err.detail.lower()


def test_validationerror_defaults():
    err = ValidationError()
    assert err.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "validation" in err.detail.lower()
