from typing import Any, Optional

from fastapi import HTTPException, status

from .i18n import i18n


class APIError(HTTPException):
    """Base API error class with i18n support"""

    def __init__(
        self,
        status_code: int,
        detail: str,
        translation_key: Optional[str] = None,
        language: Optional[str] = None,
        headers: dict[str, str] | None = None,
        **translation_params: Any,
    ):
        # Use translated message if translation_key is provided
        if translation_key:
            detail = i18n.translate(  # type: ignore
                translation_key, language, **translation_params
            )

        super().__init__(
            status_code=status_code, detail=detail, headers=headers
        )


class NotFoundError(APIError):
    """Resource not found error"""

    def __init__(
        self,
        detail: str = 'Resource not found',
        translation_key: Optional[str] = None,
        language: Optional[str] = None,
        **translation_params: Any,
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            translation_key=translation_key,
            language=language,
            **translation_params,
        )


class PermissionError(APIError):
    """Permission denied error"""

    def __init__(
        self,
        detail: str = 'Permission denied',
        translation_key: Optional[str] = None,
        language: Optional[str] = None,
        **translation_params: Any,
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            translation_key=translation_key,
            language=language,
            **translation_params,
        )


class ValidationError(APIError):
    """Validation error"""

    def __init__(
        self,
        detail: str = 'Validation error',
        translation_key: Optional[str] = None,
        language: Optional[str] = None,
        **translation_params: Any,
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            translation_key=translation_key,
            language=language,
            **translation_params,
        )


class AuthenticationError(APIError):
    """Authentication error"""

    def __init__(
        self,
        detail: str = 'Authentication failed',
        translation_key: Optional[str] = None,
        language: Optional[str] = None,
        **translation_params: Any,
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            translation_key=translation_key,
            language=language,
            **translation_params,
        )


class OrganizationError(APIError):
    """Organization-related error"""

    def __init__(
        self,
        detail: str = 'Organization error',
        translation_key: Optional[str] = None,
        language: Optional[str] = None,
        **translation_params: Any,
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            translation_key=translation_key,
            language=language,
            **translation_params,
        )


class ProjectError(APIError):
    """Project-related error"""

    def __init__(
        self,
        detail: str = 'Project error',
        translation_key: Optional[str] = None,
        language: Optional[str] = None,
        **translation_params: Any,
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            translation_key=translation_key,
            language=language,
            **translation_params,
        )


class PaymentError(APIError):
    """Payment-related error"""

    def __init__(
        self,
        detail: str = 'Payment error',
        translation_key: Optional[str] = None,
        language: Optional[str] = None,
        **translation_params: Any,
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            translation_key=translation_key,
            language=language,
            **translation_params,
        )
