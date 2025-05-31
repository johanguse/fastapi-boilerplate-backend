import logging
from typing import Any, Callable, TypeVar

from src.common.exceptions import APIError

logger = logging.getLogger(__name__)

T = TypeVar('T')


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
