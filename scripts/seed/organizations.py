"""Seed data for organizations."""

from datetime import UTC, datetime, timedelta

from src.organizations.models import Organization, OrganizationMember


def create_organizations():
    """Create organization seed data."""
    organizations = [
        Organization(
            name='Development Team',
            created_at=datetime.now(UTC) - timedelta(days=80),
        ),
        Organization(
            name='Marketing Team',
            created_at=datetime.now(UTC) - timedelta(days=60),
        ),
        Organization(
            name='Research Team',
            created_at=datetime.now(UTC) - timedelta(days=50),
        ),
        Organization(
            name='Sales Department',
            created_at=datetime.now(UTC) - timedelta(days=40),
        ),
        Organization(
            name='Customer Success',
            created_at=datetime.now(UTC) - timedelta(days=25),
        ),
    ]
    return organizations


def create_organization_members(organizations, users):
    """Create organization membership seed data."""
    organization_members = [
        # Development Team (5 members)
        OrganizationMember(
            organization_id=organizations[0].id,
            user_id=users[0].id,
            role='owner',
        ),
        OrganizationMember(
            organization_id=organizations[0].id,
            user_id=users[1].id,
            role='admin',
        ),
        OrganizationMember(
            organization_id=organizations[0].id,
            user_id=users[2].id,
            role='member',
        ),
        OrganizationMember(
            organization_id=organizations[0].id,
            user_id=users[3].id,
            role='member',
        ),
        OrganizationMember(
            organization_id=organizations[0].id,
            user_id=users[7].id,
            role='member',
        ),
        # Marketing Team (4 members)
        OrganizationMember(
            organization_id=organizations[1].id,
            user_id=users[1].id,
            role='owner',
        ),
        OrganizationMember(
            organization_id=organizations[1].id,
            user_id=users[2].id,
            role='admin',
        ),
        OrganizationMember(
            organization_id=organizations[1].id,
            user_id=users[4].id,
            role='member',
        ),
        OrganizationMember(
            organization_id=organizations[1].id,
            user_id=users[5].id,
            role='member',
        ),
        # Research Team (3 members)
        OrganizationMember(
            organization_id=organizations[2].id,
            user_id=users[8].id,
            role='owner',
        ),
        OrganizationMember(
            organization_id=organizations[2].id,
            user_id=users[3].id,
            role='admin',
        ),
        OrganizationMember(
            organization_id=organizations[2].id,
            user_id=users[7].id,
            role='member',
        ),
        # Sales Department (3 members)
        OrganizationMember(
            organization_id=organizations[3].id,
            user_id=users[2].id,
            role='owner',
        ),
        OrganizationMember(
            organization_id=organizations[3].id,
            user_id=users[3].id,
            role='member',
        ),
        OrganizationMember(
            organization_id=organizations[3].id,
            user_id=users[7].id,
            role='member',
        ),
        # Customer Success (2 members)
        OrganizationMember(
            organization_id=organizations[4].id,
            user_id=users[0].id,
            role='owner',
        ),
        OrganizationMember(
            organization_id=organizations[4].id,
            user_id=users[1].id,
            role='admin',
        ),
    ]
    return organization_members
