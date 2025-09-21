"""Common type definitions for the project."""

from typing import TYPE_CHECKING, Any

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

__all__ = [
    'ActivityLog',
    'User',
    'Project',
    'Organization',
    'OrganizationMember',
    'OrganizationInvitation',
]
