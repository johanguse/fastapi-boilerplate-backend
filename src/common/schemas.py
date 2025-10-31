from datetime import datetime
from typing import Generic, TypeVar

from fastapi_pagination import Page
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration"""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            'example': {}  # Add examples in child classes
        },
    )


T = TypeVar('T')


class PaginatedResponse(Page[T], Generic[T]):
    """Generic paginated response"""
    pass


class TimestampMixin(BaseModel):
    """Mixin for timestamps"""

    created_at: datetime
    updated_at: datetime
