from fastapi import status

from src.common.exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    OrganizationError,
    PaymentError,
    PermissionError,
    ProjectError,
    ValidationError,
)


def test_apierror_init():
    err = APIError(status_code=418, detail="I'm a teapot")
    assert err.status_code == 418
    assert err.detail == "I'm a teapot"


def test_apierror_with_translation_key():
    err = APIError(
        status_code=400,
        detail='Default message',
        translation_key='error.not_found',
    )
    assert err.status_code == 400
    # Should use translated message if translation system is working
    assert err.detail in {'Default message', 'Resource not found'}


def test_notfounderror_defaults():
    err = NotFoundError()
    assert err.status_code == status.HTTP_404_NOT_FOUND
    assert 'not found' in err.detail.lower()


def test_notfounderror_custom_detail():
    err = NotFoundError(detail='Custom not found message')
    assert err.status_code == status.HTTP_404_NOT_FOUND
    assert err.detail == 'Custom not found message'


def test_permissionerror_defaults():
    err = PermissionError()
    assert err.status_code == status.HTTP_403_FORBIDDEN
    assert 'permission' in err.detail.lower()


def test_permissionerror_custom_detail():
    err = PermissionError(detail='User is not a member of this organization')
    assert err.status_code == status.HTTP_403_FORBIDDEN
    assert 'member' in err.detail.lower()
    assert 'organization' in err.detail.lower()


def test_validationerror_defaults():
    err = ValidationError()
    assert err.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert 'validation' in err.detail.lower()


def test_validationerror_custom_detail():
    err = ValidationError(detail='Invalid email format')
    assert err.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert err.detail == 'Invalid email format'


def test_authenticationerror_defaults():
    err = AuthenticationError()
    assert err.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'authentication' in err.detail.lower()


def test_organizationerror_defaults():
    err = OrganizationError()
    assert err.status_code == status.HTTP_400_BAD_REQUEST
    assert 'organization' in err.detail.lower()


def test_projecterror_defaults():
    err = ProjectError()
    assert err.status_code == status.HTTP_400_BAD_REQUEST
    assert 'project' in err.detail.lower()


def test_paymenterror_defaults():
    err = PaymentError()
    assert err.status_code == status.HTTP_400_BAD_REQUEST
    assert 'payment' in err.detail.lower()


def test_exception_inheritance():
    """Test that all custom exceptions inherit from APIError and HTTPException"""
    from fastapi import HTTPException

    err = PermissionError()
    assert isinstance(err, APIError)
    assert isinstance(err, HTTPException)

    err2 = ValidationError()
    assert isinstance(err2, APIError)
    assert isinstance(err2, HTTPException)
