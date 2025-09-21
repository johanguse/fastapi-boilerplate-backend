import logging
import time

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import (
    RequestResponseEndpoint,
)

from .i18n import i18n

logger = logging.getLogger(__name__)


async def i18n_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    """
    Middleware to detect user's preferred language from multiple sources:
    1. Query parameter (?lang=xx)
    2. Stored cookie (preferred_locale)
    3. Accept-Language header
    4. Default language (fallback)

    Args:
        request: The incoming request
        call_next: The next middleware or endpoint
    Returns:
        The response from the next middleware or endpoint
    """
    # 1. Check query parameter first
    lang_param = request.query_params.get('lang')
    if lang_param and i18n.is_supported_language(lang_param):
        preferred_language = lang_param
    else:
        # 2. Check cookie
        cookie_lang = request.cookies.get('preferred_locale')
        if cookie_lang and i18n.is_supported_language(cookie_lang):
            preferred_language = cookie_lang
        else:
            # 3. Check Accept-Language header
            accept_language = request.headers.get('accept-language')
            preferred_language = i18n.get_language_from_accept_header(
                accept_language
            )

    # Store the language in request state for use in route handlers
    request.state.language = preferred_language

    response = await call_next(request)

    # Add Content-Language header to response
    response.headers['Content-Language'] = preferred_language

    # Set cookie if language was explicitly chosen via query param
    if lang_param and i18n.is_supported_language(lang_param):
        response.set_cookie(
            key='preferred_locale',
            value=lang_param,
            max_age=60 * 60 * 24 * 30,  # 30 days
            httponly=True,
            samesite='lax',
        )

    return response


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


def add_i18n_middleware(app: FastAPI) -> None:
    """
    Add internationalization middleware to FastAPI application.
    Args:
        app: The FastAPI application
    """
    app.middleware('http')(i18n_middleware)


def add_logging_middleware(app: FastAPI) -> None:
    """
    Add logging middleware to FastAPI application.
    Args:
        app: The FastAPI application
    """
    app.middleware('http')(logging_middleware)
