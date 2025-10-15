"""
Seed data script for development database.
Creates sample users, teams, projects, and related data.
"""

import asyncio
import random
from datetime import UTC, datetime, timedelta

# Import FastAPI Users password helper for proper hashing
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.activity_log.models import ActivityLog

# Import all models
from src.auth.models import User
from src.common.config import settings
from src.organizations.models import Organization, OrganizationMember
from src.projects.models import Project
from src.subscriptions.models import (
    BillingHistory,
    CustomerSubscription,
    SubscriptionPlan,
)

# Password context for hashing (same as FastAPI Users)
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

# Diverse user agents for realistic activity logs
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14.2; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
]

# Diverse IP addresses (for demo purposes)
IP_ADDRESSES = [
    '192.168.1.100',
    '10.0.0.50',
    '172.16.0.25',
    '203.0.113.45',  # Documentation IP
    '198.51.100.78',  # Documentation IP
    '192.0.2.123',  # Documentation IP
    '2001:db8::1',  # IPv6 documentation
    '127.0.0.1',
]


async def create_seed_data():
    """Create comprehensive seed data for development."""

    # Create async engine and session
    database_url = str(settings.DATABASE_URL).replace(
        'postgresql://', 'postgresql+asyncpg://'
    )
    engine = create_async_engine(database_url)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        print('🌱 Creating seed data...')

        # === 0. Create Subscription Plans (if they don't exist) ===
        print('💳 Checking subscription plans...')
        existing_plans = await session.execute(select(SubscriptionPlan))
        if not existing_plans.scalars().first():
            print('📦 Creating subscription plans...')
            plans = [
                SubscriptionPlan(
                    name='free',
                    display_name='Free',
                    description='Perfect for trying out the platform',
                    stripe_price_id_monthly=None,
                    stripe_price_id_yearly=None,
                    stripe_product_id=None,
                    price_monthly_usd=0,
                    price_yearly_usd=0,
                    price_monthly_eur=0,
                    price_yearly_eur=0,
                    price_monthly_gbp=0,
                    price_yearly_gbp=0,
                    price_monthly_brl=0,
                    price_yearly_brl=0,
                    max_projects=1,
                    max_users=1,
                    max_storage_gb=1,
                    features={
                        'features': [
                            '1 project',
                            '1 user',
                            '1GB storage',
                            'Basic support',
                        ]
                    },
                    is_active=True,
                    sort_order=1,
                ),
                SubscriptionPlan(
                    name='basic',
                    display_name='Basic Plan',
                    description='Entry-level plan for small businesses',
                    stripe_price_id_monthly='price_1Rsk6eD9jtDTgtt7wOVii0Uv',
                    stripe_price_id_yearly='price_1Rsk6fD9jtDTgtt7atHuhVi0',
                    stripe_product_id='prod_SmwOSjZOdHh8R2',
                    price_monthly_usd=2800,
                    price_yearly_usd=19900,
                    price_monthly_eur=2520,
                    price_yearly_eur=17910,
                    price_monthly_gbp=2240,
                    price_yearly_gbp=15920,
                    price_monthly_brl=14000,
                    price_yearly_brl=99500,
                    max_projects=3,
                    max_users=5,
                    max_storage_gb=5,
                    features={
                        'features': [
                            '3 projects',
                            '5 team members',
                            '5GB storage',
                            'Basic support',
                        ]
                    },
                    is_active=True,
                    sort_order=2,
                ),
                SubscriptionPlan(
                    name='premium',
                    display_name='Premium Subscription',
                    description='Monthly premium subscription with advanced features',
                    stripe_price_id_monthly='price_1Rsk6gD9jtDTgtt7D6J4QE4k',
                    stripe_price_id_yearly='price_1Rsk6gD9jtDTgtt7KbZqwLhV',
                    stripe_product_id='prod_SmwOCZUzUTQ5Zi',
                    price_monthly_usd=6800,
                    price_yearly_usd=45000,
                    price_monthly_eur=6120,
                    price_yearly_eur=40500,
                    price_monthly_gbp=5440,
                    price_yearly_gbp=36000,
                    price_monthly_brl=34000,
                    price_yearly_brl=225000,
                    max_projects=10,
                    max_users=20,
                    max_storage_gb=50,
                    features={
                        'features': [
                            '10 projects',
                            '20 team members',
                            '50GB storage',
                            'Priority support',
                            'Advanced analytics',
                        ]
                    },
                    is_active=True,
                    sort_order=3,
                ),
                SubscriptionPlan(
                    name='enterprise',
                    display_name='Enterprise Solution',
                    description='Full-featured enterprise package with custom support',
                    stripe_price_id_monthly='price_1Rsk6bD9jtDTgtt7YVFraetI',
                    stripe_price_id_yearly='price_1Rsk6dD9jtDTgtt7qEkMYgBF',
                    stripe_product_id='prod_SmwOdGQRNlyp3D',
                    price_monthly_usd=25500,
                    price_yearly_usd=199900,
                    price_monthly_eur=22950,
                    price_yearly_eur=179910,
                    price_monthly_gbp=20400,
                    price_yearly_gbp=159920,
                    price_monthly_brl=127500,
                    price_yearly_brl=999500,
                    max_projects=50,
                    max_users=100,
                    max_storage_gb=500,
                    features={
                        'features': [
                            'Unlimited projects',
                            '100 team members',
                            '500GB storage',
                            '24/7 priority support',
                            'Advanced analytics',
                            'Custom integrations',
                            'Dedicated account manager',
                        ]
                    },
                    is_active=True,
                    sort_order=4,
                ),
            ]
            for plan in plans:
                session.add(plan)
            await session.commit()
            print(f'✅ Created {len(plans)} subscription plans')
        else:
            print('✓ Subscription plans already exist')

        # Hash the password properly using FastAPI Users method
        admin_password = 'admin123'
        hashed_password = pwd_context.hash(admin_password)
        print(f"🔐 Generated password hash for '{admin_password}'")

        # Check if users already exist
        existing_admin = await session.execute(
            select(User).where(User.email == 'admin@example.com')
        )
        admin_user = existing_admin.scalar_one_or_none()

        if admin_user:
            print('⚠️ Admin user already exists, updating password hash...')
            # Update the password hash to ensure it works with the current password
            admin_user.hashed_password = hashed_password
            await session.commit()
            print(
                f'🔐 Updated admin password hash for: admin@example.com / {admin_password}'
            )

            # Update other existing users' passwords too
            for email in [
                'john@example.com',
                'jane@example.com',
                'bob@example.com',
            ]:
                result = await session.execute(
                    select(User).where(User.email == email)
                )
                user = result.scalar_one_or_none()
                if user:
                    user.hashed_password = hashed_password
                    print(f'🔐 Updated password hash for: {email}')

            await session.commit()
            print(
                f'✅ All user passwords updated to work with: {admin_password}'
            )
            await engine.dispose()
            return

        # 1. Create Users (more diverse with different statuses and verification states)
        print('👥 Creating users...')
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
            ),
            # Invited user (not verified yet)
            User(
                email='bob@example.com',
                name='Bob Wilson',
                role='member',
                status='invited',
                is_active=True,
                is_verified=False,
                hashed_password=hashed_password,
                created_at=datetime.now(UTC) - timedelta(days=2),
            ),
            # Another invited user
            User(
                email='alice@example.com',
                name='Alice Cooper',
                role='member',
                status='invited',
                is_active=True,
                is_verified=False,
                hashed_password=hashed_password,
                created_at=datetime.now(UTC) - timedelta(days=1),
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
            ),
        ]

        for user in users:
            session.add(user)
        await session.commit()

        # Refresh to get IDs
        for user in users:
            await session.refresh(user)

        print(f'✅ Created {len(users)} users')

        # 2. Create Organizations (more diverse)
        print('🏢 Creating organizations...')
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

        for organization in organizations:
            session.add(organization)
        await session.commit()

        for organization in organizations:
            await session.refresh(organization)

        print(f'✅ Created {len(organizations)} organizations')

        # 3. Create Organization Members (more diverse memberships)
        print('👤 Creating organization memberships...')
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

        for member in organization_members:
            session.add(member)
        await session.commit()

        print(
            f'✅ Created {len(organization_members)} organization memberships'
        )

        # 4. Create Projects (more varied)
        print('📁 Creating projects...')
        projects = [
            Project(
                name='AI Chatbot Platform',
                description='Customer service AI chatbot with RAG capabilities',
                organization_id=organizations[0].id,
                created_at=datetime.now(UTC) - timedelta(days=70),
            ),
            Project(
                name='Content Generation Tool',
                description='AI-powered content creation for marketing',
                organization_id=organizations[1].id,
                created_at=datetime.now(UTC) - timedelta(days=55),
            ),
            Project(
                name='Document Analyzer',
                description='Intelligent document processing and analysis',
                organization_id=organizations[0].id,
                created_at=datetime.now(UTC) - timedelta(days=45),
            ),
            Project(
                name='Research Assistant',
                description='AI research assistant for academic papers',
                organization_id=organizations[2].id,
                created_at=datetime.now(UTC) - timedelta(days=40),
            ),
            Project(
                name='Sales Analytics Dashboard',
                description='Real-time sales data visualization and insights',
                organization_id=organizations[3].id,
                created_at=datetime.now(UTC) - timedelta(days=30),
            ),
            Project(
                name='Customer Feedback System',
                description='Automated customer feedback collection and analysis',
                organization_id=organizations[4].id,
                created_at=datetime.now(UTC) - timedelta(days=20),
            ),
            Project(
                name='Email Campaign Manager',
                description='Automated email marketing campaigns',
                organization_id=organizations[1].id,
                created_at=datetime.now(UTC) - timedelta(days=15),
            ),
        ]

        for project in projects:
            session.add(project)
        await session.commit()

        for project in projects:
            await session.refresh(project)

        print(f'✅ Created {len(projects)} projects')

        # 5. Create Activity Logs (diverse with different IPs, user agents, types, and times)
        print('📝 Creating activity logs...')
        activities = []

        # User registration activities
        for idx, user in enumerate(users[:5]):
            activities.append(
                ActivityLog(
                    action='user.register',
                    action_type='auth',
                    description=f'User {user.email} registered',
                    user_id=user.id,
                    ip_address=random.choice(IP_ADDRESSES),
                    user_agent=random.choice(USER_AGENTS),
                    created_at=user.created_at,
                )
            )

        # Login activities (spread over time)
        login_times = [
            90,
            89,
            87,
            85,
            80,
            75,
            70,
            65,
            60,
            55,
            50,
            45,
            40,
            35,
            30,
            25,
            20,
            15,
            10,
            5,
            3,
            2,
            1,
            0,
        ]
        for days_ago in login_times:
            user = random.choice(users[:5])  # Only active users
            activities.append(
                ActivityLog(
                    action='user.login',
                    action_type='auth',
                    description=f'User {user.email} logged in',
                    user_id=user.id,
                    ip_address=random.choice(IP_ADDRESSES),
                    user_agent=random.choice(USER_AGENTS),
                    created_at=datetime.now(UTC)
                    - timedelta(days=days_ago, hours=random.randint(0, 23)),
                )
            )

        # Organization activities
        for idx, org in enumerate(organizations):
            owner_member = next(
                m
                for m in organization_members
                if m.organization_id == org.id and m.role == 'owner'
            )
            activities.append(
                ActivityLog(
                    action='organization.created',
                    action_type='organization',
                    description=f"Organization '{org.name}' created",
                    user_id=owner_member.user_id,
                    organization_id=org.id,
                    ip_address=random.choice(IP_ADDRESSES),
                    user_agent=random.choice(USER_AGENTS),
                    created_at=org.created_at,
                )
            )

        # Organization member invitations
        for member in organization_members[5:10]:  # Some members invited later
            activities.append(
                ActivityLog(
                    action='organization.member.invited',
                    action_type='organization',
                    description='User invited to organization',
                    user_id=users[0].id,  # Admin sent invites
                    organization_id=member.organization_id,
                    ip_address=random.choice(IP_ADDRESSES),
                    user_agent=random.choice(USER_AGENTS),
                    created_at=datetime.now(UTC)
                    - timedelta(days=random.randint(10, 30)),
                )
            )

        # Project activities
        for project in projects:
            activities.append(
                ActivityLog(
                    action='project.created',
                    action_type='project',
                    description=f"Project '{project.name}' created",
                    user_id=users[0].id,
                    organization_id=project.organization_id,
                    project_id=project.id,
                    ip_address=random.choice(IP_ADDRESSES),
                    user_agent=random.choice(USER_AGENTS),
                    created_at=project.created_at,
                )
            )

            # Project updates
            activities.append(
                ActivityLog(
                    action='project.updated',
                    action_type='project',
                    description=f"Project '{project.name}' settings updated",
                    user_id=random.choice(users[:4]).id,
                    organization_id=project.organization_id,
                    project_id=project.id,
                    ip_address=random.choice(IP_ADDRESSES),
                    user_agent=random.choice(USER_AGENTS),
                    created_at=project.created_at
                    + timedelta(days=random.randint(1, 10)),
                )
            )

        # Security events
        activities.extend([
            ActivityLog(
                action='user.password.changed',
                action_type='security',
                description='User changed password',
                user_id=users[1].id,
                ip_address=random.choice(IP_ADDRESSES),
                user_agent=random.choice(USER_AGENTS),
                created_at=datetime.now(UTC) - timedelta(days=20),
            ),
            ActivityLog(
                action='user.email.verified',
                action_type='security',
                description='Email address verified',
                user_id=users[2].id,
                ip_address=random.choice(IP_ADDRESSES),
                user_agent=random.choice(USER_AGENTS),
                created_at=datetime.now(UTC) - timedelta(days=44),
            ),
            ActivityLog(
                action='user.suspended',
                action_type='security',
                description='User account suspended by admin',
                user_id=users[6].id,
                ip_address=random.choice(IP_ADDRESSES),
                user_agent=random.choice(USER_AGENTS),
                created_at=datetime.now(UTC) - timedelta(days=10),
            ),
            ActivityLog(
                action='security.2fa.enabled',
                action_type='security',
                description='Two-factor authentication enabled',
                user_id=users[0].id,
                ip_address=random.choice(IP_ADDRESSES),
                user_agent=random.choice(USER_AGENTS),
                created_at=datetime.now(UTC) - timedelta(days=60),
            ),
        ])

        # System activities
        activities.extend([
            ActivityLog(
                action='system.backup.completed',
                action_type='system',
                description='Database backup completed successfully',
                ip_address='127.0.0.1',
                user_agent='System Cron Job',
                created_at=datetime.now(UTC) - timedelta(days=1),
            ),
            ActivityLog(
                action='system.maintenance.completed',
                action_type='system',
                description='Scheduled system maintenance completed',
                ip_address='127.0.0.1',
                user_agent='System Cron Job',
                created_at=datetime.now(UTC) - timedelta(days=7),
            ),
        ])

        # Payment activities (we'll create these after subscriptions)

        for activity in activities:
            session.add(activity)
        await session.commit()

        print(f'✅ Created {len(activities)} activity logs')

        # 6. Create Active Subscriptions and Billing History
        print('💳 Creating subscriptions and billing history...')

        # Get subscription plans
        plans_result = await session.execute(select(SubscriptionPlan))
        all_plans = {plan.name: plan for plan in plans_result.scalars().all()}

        # Create subscriptions for organizations
        subscriptions = []
        billing_records = []

        # Development Team - Enterprise plan (active subscription)
        sub1 = CustomerSubscription(
            organization_id=organizations[0].id,
            plan_id=all_plans['enterprise'].id,
            stripe_customer_id='cus_dev_team_001',
            stripe_subscription_id='sub_dev_team_001',
            status='active',
            current_period_start=datetime.now(UTC) - timedelta(days=15),
            current_period_end=datetime.now(UTC) + timedelta(days=15),
            cancel_at_period_end=False,
            current_users_count=5,
            current_projects_count=3,
            current_storage_gb=45,
            created_at=datetime.now(UTC) - timedelta(days=75),
        )
        subscriptions.append(sub1)
        session.add(sub1)
        await session.flush()

        # Billing history for Development Team (last 3 months)
        for months_ago in range(3):
            billing_records.append(
                BillingHistory(
                    subscription_id=sub1.id,
                    stripe_invoice_id=f'inv_dev_{months_ago}_001',
                    stripe_payment_intent_id=f'pi_dev_{months_ago}_001',
                    amount=all_plans['enterprise'].price_monthly_usd,
                    currency='usd',
                    status='paid',
                    invoice_date=datetime.now(UTC)
                    - timedelta(days=30 * months_ago),
                    paid_at=datetime.now(UTC)
                    - timedelta(days=30 * months_ago, hours=1),
                    description=f'Enterprise Solution - Monthly subscription (Month {3 - months_ago})',
                )
            )

        # Marketing Team - Premium plan (active)
        sub2 = CustomerSubscription(
            organization_id=organizations[1].id,
            plan_id=all_plans['premium'].id,
            stripe_customer_id='cus_marketing_001',
            stripe_subscription_id='sub_marketing_001',
            status='active',
            current_period_start=datetime.now(UTC) - timedelta(days=10),
            current_period_end=datetime.now(UTC) + timedelta(days=20),
            cancel_at_period_end=False,
            current_users_count=4,
            current_projects_count=2,
            current_storage_gb=12,
            created_at=datetime.now(UTC) - timedelta(days=55),
        )
        subscriptions.append(sub2)
        session.add(sub2)
        await session.flush()

        # Billing history for Marketing Team (last 2 months)
        for months_ago in range(2):
            billing_records.append(
                BillingHistory(
                    subscription_id=sub2.id,
                    stripe_invoice_id=f'inv_marketing_{months_ago}_001',
                    stripe_payment_intent_id=f'pi_marketing_{months_ago}_001',
                    amount=all_plans['premium'].price_monthly_usd,
                    currency='usd',
                    status='paid',
                    invoice_date=datetime.now(UTC)
                    - timedelta(days=30 * months_ago),
                    paid_at=datetime.now(UTC)
                    - timedelta(days=30 * months_ago, hours=2),
                    description=f'Premium Subscription - Monthly subscription (Month {2 - months_ago})',
                )
            )

        # Research Team - Basic plan (active)
        sub3 = CustomerSubscription(
            organization_id=organizations[2].id,
            plan_id=all_plans['basic'].id,
            stripe_customer_id='cus_research_001',
            stripe_subscription_id='sub_research_001',
            status='active',
            current_period_start=datetime.now(UTC) - timedelta(days=5),
            current_period_end=datetime.now(UTC) + timedelta(days=25),
            cancel_at_period_end=False,
            current_users_count=3,
            current_projects_count=1,
            current_storage_gb=3,
            created_at=datetime.now(UTC) - timedelta(days=45),
        )
        subscriptions.append(sub3)
        session.add(sub3)
        await session.flush()

        # Billing history for Research Team (last month)
        billing_records.append(
            BillingHistory(
                subscription_id=sub3.id,
                stripe_invoice_id='inv_research_0_001',
                stripe_payment_intent_id='pi_research_0_001',
                amount=all_plans['basic'].price_monthly_usd,
                currency='usd',
                status='paid',
                invoice_date=datetime.now(UTC) - timedelta(days=30),
                paid_at=datetime.now(UTC) - timedelta(days=30, hours=1),
                description='Basic Plan - Monthly subscription',
            )
        )

        # Sales Department - Premium plan (trialing)
        sub4 = CustomerSubscription(
            organization_id=organizations[3].id,
            plan_id=all_plans['premium'].id,
            stripe_customer_id='cus_sales_001',
            stripe_subscription_id='sub_sales_001',
            status='trialing',
            trial_start=datetime.now(UTC) - timedelta(days=5),
            trial_end=datetime.now(UTC) + timedelta(days=9),
            current_period_start=datetime.now(UTC) - timedelta(days=5),
            current_period_end=datetime.now(UTC) + timedelta(days=25),
            cancel_at_period_end=False,
            current_users_count=3,
            current_projects_count=1,
            current_storage_gb=2,
            created_at=datetime.now(UTC) - timedelta(days=5),
        )
        subscriptions.append(sub4)
        session.add(sub4)
        await session.flush()

        # Customer Success - Free plan
        sub5 = CustomerSubscription(
            organization_id=organizations[4].id,
            plan_id=all_plans['free'].id,
            status='active',
            current_period_start=datetime.now(UTC) - timedelta(days=20),
            current_period_end=datetime.now(UTC) + timedelta(days=340),
            cancel_at_period_end=False,
            current_users_count=2,
            current_projects_count=1,
            current_storage_gb=0,
            created_at=datetime.now(UTC) - timedelta(days=20),
        )
        subscriptions.append(sub5)
        session.add(sub5)

        # Add all billing records
        for billing in billing_records:
            session.add(billing)

        await session.commit()

        print(f'✅ Created {len(subscriptions)} subscriptions')
        print(f'✅ Created {len(billing_records)} billing records')

        # Add payment activity logs
        payment_activities = []
        for billing in billing_records:
            payment_activities.append(
                ActivityLog(
                    action='payment.succeeded',
                    action_type='payment',
                    description=f'Payment successful: ${billing.amount / 100:.2f} {billing.currency.upper()}',
                    organization_id=subscriptions[0].organization_id
                    if billing.subscription_id == sub1.id
                    else subscriptions[1].organization_id
                    if billing.subscription_id == sub2.id
                    else subscriptions[2].organization_id,
                    ip_address=random.choice(IP_ADDRESSES),
                    user_agent=random.choice(USER_AGENTS),
                    created_at=billing.paid_at,
                )
            )

        for activity in payment_activities:
            session.add(activity)
        await session.commit()

        print(f'✅ Created {len(payment_activities)} payment activity logs')

        # Get final counts
        final_plans = await session.execute(select(SubscriptionPlan))
        plan_count = len(list(final_plans.scalars().all()))

        # Calculate total revenue
        total_revenue = sum(b.amount for b in billing_records)
        active_subscriptions = sum(
            1 for s in subscriptions if s.status == 'active'
        )

        print('\n🎉 Seed data creation completed successfully!')
        print('\n📊 Summary:')
        print(f'   • {plan_count} subscription plans')
        print(f'   • {len(users)} users')
        print(
            f'     - {sum(1 for u in users if u.status == "active")} active users'
        )
        print(
            f'     - {sum(1 for u in users if u.status == "invited")} invited users'
        )
        print(
            f'     - {sum(1 for u in users if u.status == "suspended")} suspended users'
        )
        print(
            f'     - {sum(1 for u in users if u.is_verified)} verified users'
        )
        print(
            f'   • {len(organizations)} organizations with {len(organization_members)} total memberships'
        )
        print(f'   • {len(projects)} projects')
        print(
            f'   • {len(activities) + len(payment_activities)} activity logs'
        )
        print(
            f'   • {len(subscriptions)} subscriptions ({active_subscriptions} active)'
        )
        print(
            f'   • {len(billing_records)} billing records (Total revenue: ${total_revenue / 100:.2f})'
        )
        print(f'\n🔐 Default password for all users: {admin_password}')
        print('\n� User accounts:')
        print('   • admin@example.com (admin, superuser)')
        print('   • john@example.com (member, active)')
        print('   • jane@example.com (member, active)')
        print('   • sarah@example.com (member, active)')
        print('   • bob@example.com (member, invited)')
        print('   • alice@example.com (member, invited)')
        print('   • suspended@example.com (member, suspended)')
        print('   • mike@example.com (member, active)')
        print('   • emma@example.com (admin, active)')
        print('\n💳 Active Subscriptions:')
        print(
            f'   • Development Team: Enterprise Solution (${all_plans["enterprise"].price_monthly_usd / 100}/mo)'
        )
        print(
            f'   • Marketing Team: Premium Subscription (${all_plans["premium"].price_monthly_usd / 100}/mo)'
        )
        print(
            f'   • Research Team: Basic Plan (${all_plans["basic"].price_monthly_usd / 100}/mo)'
        )
        print('   • Sales Department: Premium Subscription (trialing)')
        print('   • Customer Success: Free Plan')

    await engine.dispose()


if __name__ == '__main__':
    asyncio.run(create_seed_data())
