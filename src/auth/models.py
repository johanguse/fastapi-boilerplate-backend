from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.database import Base

if TYPE_CHECKING:
    # These are still needed because they're used in relationship annotations
    from src.activity_log.models import ActivityLog
    from src.organizations.models import (
        OrganizationInvitation,
        OrganizationMember,
    )


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
    organization_memberships: Mapped[list['OrganizationMember']] = relationship(
        'OrganizationMember',
        back_populates='user',
        cascade='all, delete-orphan',
    )
    sent_org_invitations: Mapped[list['OrganizationInvitation']] = relationship(
        'OrganizationInvitation',
        back_populates='invited_by',
        foreign_keys='[OrganizationInvitation.invited_by_id]',
        cascade='all, delete-orphan',
    )
    received_org_invitations: Mapped[list['OrganizationInvitation']] = relationship(
        'OrganizationInvitation',
        back_populates='invitee',
        foreign_keys='[OrganizationInvitation.invitee_id]',
        cascade='all, delete-orphan',
    )

    def __repr__(self) -> str:
        return f'<User {self.email}>'
