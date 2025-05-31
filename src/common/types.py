"""Common type definitions for the project."""

from typing import TYPE_CHECKING, Any

# Define type aliases to avoid circular imports
if not TYPE_CHECKING:
    ActivityLog = Any
    User = Any
    Project = Any
    Team = Any
    TeamMember = Any
    Invitation = Any

if TYPE_CHECKING:
    from src.activity_log.models import ActivityLog
    from src.auth.models import User
    from src.projects.models import Project
    from src.teams.models import Invitation, Team, TeamMember

__all__ = [
    'ActivityLog',
    'User',
    'Project',
    'Team',
    'TeamMember',
    'Invitation',
]
