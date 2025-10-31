"""Seed data for users."""

from datetime import UTC, datetime, timedelta

from passlib.context import CryptContext

from src.auth.models import User

from .constants import DEFAULT_PASSWORD

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def create_users():
    """Create diverse user seed data."""
    hashed_password = pwd_context.hash(DEFAULT_PASSWORD)

    users = [
        # Admin user - verified and active
        User(
            email='admin@example.com',
            name='Admin User',
            role='admin',
            status='active',
            is_active=True,
            is_superuser=True,
            is_verified=True,
            hashed_password=hashed_password,
            created_at=datetime.now(UTC) - timedelta(days=90),
            # Onboarding fields
            phone='+1-555-0100',
            company='TechCorp Inc.',
            job_title='System Administrator',
            country='United States',
            timezone='America/New_York',
            bio='Experienced system administrator with expertise in cloud infrastructure and security.',
            website='https://techcorp.com',
            onboarding_completed=True,
            onboarding_step=3,
        ),
        # Regular verified members
        User(
            email='john@example.com',
            name='John Doe',
            role='member',
            status='active',
            is_active=True,
            is_verified=True,
            hashed_password=hashed_password,
            created_at=datetime.now(UTC) - timedelta(days=60),
            # Onboarding fields
            phone='+1-555-0101',
            company='DevCorp Solutions',
            job_title='Senior Developer',
            country='United States',
            timezone='America/Los_Angeles',
            bio='Full-stack developer passionate about creating innovative web applications.',
            website='https://johndoe.dev',
            onboarding_completed=True,
            onboarding_step=3,
        ),
        User(
            email='jane@example.com',
            name='Jane Smith',
            role='member',
            status='active',
            is_active=True,
            is_verified=True,
            hashed_password=hashed_password,
            created_at=datetime.now(UTC) - timedelta(days=45),
            # Onboarding fields
            phone='+1-555-0102',
            company='Marketing Pro',
            job_title='Marketing Manager',
            country='Canada',
            timezone='America/Toronto',
            bio='Marketing professional with expertise in digital campaigns and brand strategy.',
            website='https://janesmith.marketing',
            onboarding_completed=True,
            onboarding_step=3,
        ),
        User(
            email='sarah@example.com',
            name='Sarah Johnson',
            role='member',
            status='active',
            is_active=True,
            is_verified=True,
            hashed_password=hashed_password,
            created_at=datetime.now(UTC) - timedelta(days=30),
            # Onboarding fields
            phone='+44-20-7946-0958',
            company='Research Labs',
            job_title='Research Scientist',
            country='United Kingdom',
            timezone='Europe/London',
            bio='AI researcher focused on machine learning and natural language processing.',
            website='https://sarahjohnson.research',
            onboarding_completed=True,
            onboarding_step=3,
        ),
        # Invited users (not verified yet)
        User(
            email='bob@example.com',
            name='Bob Wilson',
            role='member',
            status='invited',
            is_active=True,
            is_verified=False,
            hashed_password=hashed_password,
            created_at=datetime.now(UTC) - timedelta(days=2),
            # Onboarding fields - incomplete for invited users
            phone='+1-555-0103',
            company='StartupCo',
            job_title='Product Manager',
            country='United States',
            timezone='America/Chicago',
            bio='Product manager with experience in agile development and user experience design.',
            website='https://bobwilson.pm',
            onboarding_completed=False,
            onboarding_step=1,
        ),
        User(
            email='alice@example.com',
            name='Alice Cooper',
            role='member',
            status='invited',
            is_active=True,
            is_verified=False,
            hashed_password=hashed_password,
            created_at=datetime.now(UTC) - timedelta(days=1),
            # Onboarding fields - incomplete for invited users
            phone='+49-30-12345678',
            company='Design Studio',
            job_title='UX Designer',
            country='Germany',
            timezone='Europe/Berlin',
            bio='Creative UX designer passionate about user-centered design and accessibility.',
            website='https://alicecooper.design',
            onboarding_completed=False,
            onboarding_step=0,
        ),
        # Suspended user
        User(
            email='suspended@example.com',
            name='Suspended User',
            role='member',
            status='suspended',
            is_active=False,
            is_verified=True,
            hashed_password=hashed_password,
            created_at=datetime.now(UTC) - timedelta(days=120),
            # Onboarding fields - completed but suspended
            phone='+1-555-0104',
            company='OldCorp',
            job_title='Data Analyst',
            country='United States',
            timezone='America/Denver',
            bio='Data analyst with expertise in statistical analysis and business intelligence.',
            website='https://suspendeduser.analytics',
            onboarding_completed=True,
            onboarding_step=3,
        ),
        # Recently joined active member
        User(
            email='mike@example.com',
            name='Mike Chen',
            role='member',
            status='active',
            is_active=True,
            is_verified=True,
            hashed_password=hashed_password,
            created_at=datetime.now(UTC) - timedelta(days=7),
            # Onboarding fields
            phone='+86-138-0013-8000',
            company='Tech Innovations',
            job_title='Software Engineer',
            country='China',
            timezone='Asia/Shanghai',
            bio='Software engineer specializing in mobile app development and cloud computing.',
            website='https://mikechen.tech',
            onboarding_completed=True,
            onboarding_step=3,
        ),
        # Another admin
        User(
            email='emma@example.com',
            name='Emma Davis',
            role='admin',
            status='active',
            is_active=True,
            is_superuser=False,
            is_verified=True,
            hashed_password=hashed_password,
            created_at=datetime.now(UTC) - timedelta(days=75),
            # Onboarding fields
            phone='+61-2-9876-5432',
            company='Aussie Tech',
            job_title='Technical Lead',
            country='Australia',
            timezone='Australia/Sydney',
            bio='Technical lead with expertise in DevOps, microservices, and team management.',
            website='https://emmadavis.lead',
            onboarding_completed=True,
            onboarding_step=3,
        ),
        # New user for onboarding demo
        User(
            email='newuser@example.com',
            name='New User',
            role='member',
            status='active',
            is_active=True,
            is_verified=True,
            hashed_password=hashed_password,
            created_at=datetime.now(UTC) - timedelta(hours=2),
            # Onboarding fields - incomplete for demo
            onboarding_completed=False,
            onboarding_step=0,
        ),
    ]

    return users
