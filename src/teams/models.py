import enum
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.database import Base

if TYPE_CHECKING:
    # Still needed for relationship annotations
    from src.activity_log.models import ActivityLog
    from src.auth.models import User
    from src.projects.models import Project


class TeamMemberRole(str, enum.Enum):
    """Team member role enum."""

    OWNER = 'owner'
    ADMIN = 'admin'
    MEMBER = 'member'
    VIEWER = 'viewer'


class Team(Base):
    """Team model."""

    __tablename__ = 'teams'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        Text, unique=True
    )
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(
        Text, unique=True
    )
    stripe_product_id: Mapped[Optional[str]] = mapped_column(Text)
    plan_name: Mapped[Optional[str]] = mapped_column(String(50))
    subscription_status: Mapped[Optional[str]] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=lambda: datetime.now(UTC),
    )
    max_projects: Mapped[int] = mapped_column(
        Integer, default=3, nullable=False
    )
    active_projects: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    # Relationships
    team_members: Mapped[list['TeamMember']] = relationship(
        back_populates='team'
    )
    activity_logs: Mapped[list['ActivityLog']] = relationship(
        back_populates='team'
    )
    invitations: Mapped[list['Invitation']] = relationship(
        back_populates='team'
    )
    projects: Mapped[list['Project']] = relationship(back_populates='team')

    def __repr__(self) -> str:
        return f'<Team {self.name}>'


class TeamMember(Base):
    """Team member model for project teams."""

    __tablename__ = 'team_members'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role: Mapped[TeamMemberRole] = mapped_column(
        Enum(TeamMemberRole),
        default=TeamMemberRole.MEMBER,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=lambda: datetime.now(UTC),
    )

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )
    team_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('teams.id', ondelete='CASCADE'),
        nullable=False,
    )

    # Relationships
    user: Mapped['User'] = relationship(
        'User', back_populates='team_memberships'
    )
    team: Mapped['Team'] = relationship('Team', back_populates='team_members')

    def __repr__(self) -> str:
        return f'<TeamMember {self.user_id} in team {self.team_id} as {self.role}>'


class Invitation(Base):
    """Invitation model for team invites."""

    __tablename__ = 'invitations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default='pending',
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    # Foreign Keys
    team_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('teams.id', ondelete='CASCADE'),
        nullable=False,
    )
    invited_by_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )
    invitee_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
    )

    # Relationships
    team: Mapped['Team'] = relationship('Team', back_populates='invitations')
    invited_by: Mapped['User'] = relationship(
        'User', foreign_keys=[invited_by_id], back_populates='sent_invitations'
    )
    invitee: Mapped[Optional['User']] = relationship(
        'User',
        foreign_keys=[invitee_id],
        back_populates='received_invitations',
    )

    def __repr__(self) -> str:
        return f'<Invitation to {self.email} for team {self.team_id}>'
