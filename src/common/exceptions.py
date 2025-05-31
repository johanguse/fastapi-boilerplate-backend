from fastapi import HTTPException, status


class APIError(HTTPException):
    """Base API error class"""

    def __init__(
        self, status_code: int, detail: str, headers: dict | None = None
    ):
        super().__init__(
            status_code=status_code, detail=detail, headers=headers
        )


class NotFoundError(APIError):
    """Resource not found error"""

    def __init__(self, detail: str = 'Resource not found'):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class PermissionError(APIError):
    """Permission denied error"""

    def __init__(self, detail: str = 'Permission denied'):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ValidationError(APIError):
    """Validation error"""

    def __init__(self, detail: str = 'Validation error'):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail
        )
