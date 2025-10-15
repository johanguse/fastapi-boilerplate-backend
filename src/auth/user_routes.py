from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.auth.schemas import UserRead, UserUpdate
from src.auth.service import get_user_by_email, get_users, update_user
from src.auth.users import current_active_user
from src.common.exceptions import NotFoundError
from src.common.i18n import i18n
from src.common.pagination import CustomParams, Paginated
from src.common.session import get_async_session
from src.common.utils import get_request_language, translate_message

router = APIRouter(tags=['users'])


@router.get('/me', response_model=UserRead)
async def get_current_user(
    current_user: User = Depends(current_active_user),
):
    """
    Get current user profile
    """
    return current_user


@router.patch('/me', response_model=UserRead)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Update current user profile
    """
    return await update_user(db, current_user.id, user_update)


@router.get('/users', response_model=Paginated[UserRead])
async def list_users(
    params: CustomParams = Depends(),
    search: str = Query(None, description='Search by name or email'),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """
    List users with pagination and search
    """
    return await get_users(db, params, search)


@router.get('/users/{email}', response_model=UserRead)
async def get_user_profile(
    email: str,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """
    Get user profile by email
    """
    user = await get_user_by_email(db, email)
    if not user:
        # Get the user's preferred language from request
        language = get_request_language(request)
        # Raise exception with translated message
        raise NotFoundError(
            translation_key='auth.user_not_found', language=language
        )
    return user


@router.get('/i18n/languages')
async def get_available_languages():
    """
    Get list of supported languages
    """
    languages = []
    for lang_code in i18n.get_supported_languages():
        locale_info = i18n.get_locale_info(lang_code)
        languages.append(locale_info)

    return {
        'supported_languages': languages,
        'default_language': i18n.DEFAULT_LANGUAGE,
    }


@router.get('/i18n/test')
async def test_translation(  # noqa: PT028
    request: Request,
    key: str = Query(
        'auth.user_not_found', description='Translation key to test'
    ),
):
    """
    Test translation endpoint - returns translated message based on Accept-Language header
    """
    language = get_request_language(request)
    translated_message = translate_message(key, request)

    return {
        'language': language,
        'key': key,
        'message': translated_message,
        'available_languages': i18n.get_supported_languages(),
    }


@router.get('/i18n/pluralization')
async def test_pluralization(  # noqa: PT028
    request: Request,
    key: str = Query('messages', description='Base plural key to test'),
    count: int = Query(1, description='Count for pluralization'),
):
    """
    Test pluralization endpoint - demonstrates plural forms in different languages
    """
    language = get_request_language(request)
    plural_form = i18n.get_plural_form(language, count)
    translated_message = i18n.translate_plural(key, count, language)

    return {
        'language': language,
        'count': count,
        'plural_form': plural_form,
        'base_key': key,
        'message': translated_message,
        'examples': {
            lang: i18n.translate_plural(key, count, lang)
            for lang in i18n.get_supported_languages()
        },
    }


@router.get('/i18n/datetime')
async def get_localized_datetime(request: Request):
    """
    Returns current datetime formatted according to the user's locale
    """
    from datetime import datetime

    from babel.dates import format_datetime

    language = get_request_language(request)

    try:
        from babel import Locale

        locale = Locale.parse(language)
        now = datetime.now()
        localized_time = format_datetime(now, locale=locale)
    except Exception:
        localized_time = str(datetime.now())

    return {
        'language': language,
        'datetime': localized_time,
        'iso_datetime': datetime.now().isoformat(),
    }
