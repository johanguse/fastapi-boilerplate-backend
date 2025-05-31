import logging
import time

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import (
    RequestResponseEndpoint,
)

logger = logging.getLogger(__name__)


async def logging_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    """
    Middleware to log request/response details.
    Args:
        request: The incoming request
        call_next: The next middleware or endpoint
    Returns:
        The response from the next middleware or endpoint
    """
    start_time = time.time()
    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)

    logger.info(
        f'{request.method} {request.url.path} '
        f'completed in {formatted_process_time}ms '
        f'status_code={response.status_code}'
    )

    return response


def add_logging_middleware(app: FastAPI) -> None:
    """
    Add logging middleware to FastAPI application.
    Args:
        app: The FastAPI application
    """
    app.middleware('http')(logging_middleware)
