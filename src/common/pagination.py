from typing import Any, Generic, TypeVar

from fastapi import Query
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate as _paginate

from src.common.config import settings

T = TypeVar('T')


class CustomParams(Params):
    """
    Custom pagination parameters with default values from settings
    """

    size: int = Query(
        settings.DEFAULT_PAGE_SIZE, alias='page_size', ge=1, le=100
    )
    page: int = Query(1, ge=1)


class Paginated(Page[T], Generic[T]):
    """
    Custom pagination class that uses settings for default page size
    """
    pass


def paginate(query: Any, params: CustomParams):  # type: ignore
    return _paginate(query, params)
