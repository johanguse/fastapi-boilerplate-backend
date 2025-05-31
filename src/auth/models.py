from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.database import Base

if TYPE_CHECKING:
    # These are still needed because they're used in relationship annotations
    from src.activity_log.models import ActivityLog
    from src.teams.models import Invitation, TeamMember


class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default='member')
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
    max_teams: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

    # Relationships
    activities: Mapped[list['ActivityLog']] = relationship(
        'ActivityLog',
        back_populates='user',
        cascade='all, delete-orphan',
    )
    team_memberships: Mapped[list['TeamMember']] = relationship(
        'TeamMember',
        back_populates='user',
        cascade='all, delete-orphan',
    )
    sent_invitations: Mapped[list['Invitation']] = relationship(
        'Invitation',
        back_populates='invited_by',
        foreign_keys='[Invitation.invited_by_id]',
        cascade='all, delete-orphan',
    )
    received_invitations: Mapped[list['Invitation']] = relationship(
        'Invitation',
        back_populates='invitee',
        foreign_keys='[Invitation.invitee_id]',
        cascade='all, delete-orphan',
    )

    def __repr__(self) -> str:
        return f'<User {self.email}>'
