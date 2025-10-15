import enum
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.database import Base

if TYPE_CHECKING:
    from src.activity_log.models import ActivityLog
    from src.auth.models import User
    from src.projects.models import Project
    from src.subscriptions.models import CustomerSubscription


class OrganizationMemberRole(str, enum.Enum):
    OWNER = 'owner'
    ADMIN = 'admin'
    MEMBER = 'member'
    VIEWER = 'viewer'


class Organization(Base):
    __tablename__ = 'organizations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[Optional[str]] = mapped_column(String(120), unique=True)
    logo_url: Mapped[Optional[str]] = mapped_column(Text)
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

    members: Mapped[list['OrganizationMember']] = relationship(
        'OrganizationMember', back_populates='organization'
    )
    activity_logs: Mapped[list['ActivityLog']] = relationship(
        'ActivityLog', back_populates='organization'
    )
    invitations: Mapped[list['OrganizationInvitation']] = relationship(
        'OrganizationInvitation', back_populates='organization'
    )
    projects: Mapped[list['Project']] = relationship(
        'Project', back_populates='organization'
    )
    subscription: Mapped[Optional['CustomerSubscription']] = relationship(
        'CustomerSubscription', back_populates='organization', uselist=False
    )

    def __repr__(self) -> str:
        return f'<Organization {self.name}>'


class OrganizationMember(Base):
    __tablename__ = 'organization_members'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role: Mapped[OrganizationMemberRole] = mapped_column(
        Enum(OrganizationMemberRole),
        default=OrganizationMemberRole.MEMBER,
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

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False
    )
    organization_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False,
    )

    user: Mapped['User'] = relationship(
        'User', back_populates='organization_memberships'
    )
    organization: Mapped['Organization'] = relationship(
        'Organization', back_populates='members'
    )

    def __repr__(self) -> str:
        return f'<OrganizationMember {self.user_id} in org {self.organization_id} as {self.role}>'


class OrganizationInvitation(Base):
    __tablename__ = 'organization_invitations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default='pending', nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    organization_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False,
    )
    invited_by_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False
    )
    invitee_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )

    organization: Mapped['Organization'] = relationship(
        'Organization', back_populates='invitations'
    )
    invited_by: Mapped['User'] = relationship(
        'User',
        foreign_keys=[invited_by_id],
        back_populates='sent_org_invitations',
    )
    invitee: Mapped[Optional['User']] = relationship(
        'User',
        foreign_keys=[invitee_id],
        back_populates='received_org_invitations',
    )

    def __repr__(self) -> str:
        return (
            f'<OrgInvitation to {self.email} for org {self.organization_id}>'
        )
