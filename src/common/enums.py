from enum import Enum


class UserRole(str, Enum):
    """User role enumeration."""

    ADMIN = "admin"
    USER = "user"


class TeamMemberRole(str, Enum):
    """Team member role enumeration."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
