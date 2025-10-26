"""Common type definitions for the project."""

from typing import TYPE_CHECKING, Any, AsyncGenerator, TypeVar

# Define type aliases to avoid circular imports
if not TYPE_CHECKING:
    ActivityLog = Any
    User = Any
    Project = Any
    Organization = Any
    OrganizationMember = Any
    OrganizationInvitation = Any

if TYPE_CHECKING:
    from src.activity_log.models import ActivityLog
    from src.auth.models import User
    from src.organizations.models import (
        Organization,
        OrganizationInvitation,
        OrganizationMember,
    )
    from src.projects.models import Project

# Generic TypeVar for use across the project
T = TypeVar('T')
"""Generic type variable for generic classes and functions."""

# HTTP types
JSONDict = dict[str, Any]
"""Type alias for JSON-compatible dictionaries."""

# Database types
DatabaseSession = AsyncGenerator[Any, None]
"""Type alias for database session generators."""

__all__ = [
    'ActivityLog',
    'User',
    'Project',
    'Organization',
    'OrganizationMember',
    'OrganizationInvitation',
    'T',
    'JSONDict',
    'DatabaseSession',
    'TYPE_CHECKING',
]
