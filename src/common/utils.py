import logging
from typing import Any, Callable, Optional, TypeVar

from fastapi import Request

from src.common.exceptions import APIError

from .i18n import i18n

logger = logging.getLogger(__name__)

T = TypeVar('T')


def get_request_language(request: Request) -> str:
    """
    Get the user's preferred language from the request.

    Args:
        request: The FastAPI request object

    Returns:
        The language code (e.g., 'en', 'es', 'fr')
    """
    # Try to get language from request state (set by i18n middleware)
    if hasattr(request.state, 'language'):
        return request.state.language

    # Fallback: extract from Accept-Language header
    accept_language = request.headers.get('accept-language')
    return i18n.get_language_from_accept_header(accept_language)


def translate_message(
    key: str,
    request: Optional[Request] = None,
    language: Optional[str] = None,
    **kwargs: Any,  # type: ignore
) -> str:
    """
    Translate a message using the request's language or provided language.

    Args:
        key: Translation key
        request: FastAPI request object (optional)
        language: Language code (optional, overrides request language)
        **kwargs: Variables for string formatting

    Returns:
        Translated message
    """
    if language is None and request is not None:
        language = get_request_language(request)

    return i18n.translate(key, language, **kwargs)


async def handle_errors(
    func: Callable[..., T], *args: Any, **kwargs: Any
) -> T:
    """
    Generic error handler for async functions
    """
    try:
        return await func(*args, **kwargs)
    except APIError:
        # Re-raise our custom API errors
        raise
    except Exception as e:
        # Log unexpected errors and return a generic error
        logger.exception(f'Unexpected error in {func.__name__}: {str(e)}')
        raise APIError(status_code=500, detail='An unexpected error occurred')
