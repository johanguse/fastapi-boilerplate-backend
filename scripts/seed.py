"""
Seed data script for development database.
Creates sample users, teams, projects, and related data.
"""

import asyncio

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.activity_log.models import ActivityLog
from src.ai_core.usage import AIUsageLog

# Import all models
from src.auth.models import User, EmailToken
from src.common.config import settings
from src.organizations.models import Organization, OrganizationMember
from src.projects.models import Project
from src.subscriptions.models import (
    BillingHistory,
    CustomerSubscription,
    SubscriptionPlan,
)

# Import modular seed functions
from scripts.seed import (
    ai_usage,
    constants,
    organizations,
    projects,
    subscription_plans,
    subscriptions,
    users,
)
from scripts.seed.activity_logs import create_activity_logs

# Password context for hashing (same as FastAPI Users)
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


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
            plans = subscription_plans.create_subscription_plans()
            for plan in plans:
                session.add(plan)
            await session.commit()
            print(f'✅ Created {len(plans)} subscription plans')
        else:
            print('✓ Subscription plans already exist')

        # Hash the password properly using FastAPI Users method
        admin_password = constants.DEFAULT_PASSWORD
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

        # 1. Create Users
        print('👥 Creating users...')
        users_list = users.create_users()
        for user in users_list:
            session.add(user)
        await session.commit()

        # Refresh to get IDs
        for user in users_list:
            await session.refresh(user)

        print(f'✅ Created {len(users_list)} users')

        # 2. Create Organizations
        print('🏢 Creating organizations...')
        organizations_list = organizations.create_organizations()
        for organization in organizations_list:
            session.add(organization)
        await session.commit()

        for organization in organizations_list:
            await session.refresh(organization)

        print(f'✅ Created {len(organizations_list)} organizations')

        # 3. Create Organization Members
        print('👤 Creating organization memberships...')
        organization_members = organizations.create_organization_members(
            organizations_list, users_list
        )
        for member in organization_members:
            session.add(member)
        await session.commit()

        print(
            f'✅ Created {len(organization_members)} organization memberships'
        )

        # 4. Create Projects
        print('📁 Creating projects...')
        projects_list = projects.create_projects(organizations_list)
        for project in projects_list:
            session.add(project)
        await session.commit()

        for project in projects_list:
            await session.refresh(project)

        print(f'✅ Created {len(projects_list)} projects')

        # 5. Create Activity Logs
        print('📝 Creating activity logs...')
        activities = create_activity_logs(
            users_list, organizations_list, organization_members, projects_list
        )
        for activity in activities:
            session.add(activity)
        await session.commit()

        print(f'✅ Created {len(activities)} activity logs')

        # 6. Create Active Subscriptions and Billing History
        print('💳 Creating subscriptions and billing history...')

        # Get subscription plans
        plans_result = await session.execute(select(SubscriptionPlan))
        all_plans = {plan.name: plan for plan in plans_result.scalars().all()}

        # Create subscriptions
        subscriptions_list = subscriptions.create_subscriptions(
            organizations_list, all_plans
        )

        for sub in subscriptions_list:
            session.add(sub)
        await session.flush()

        # Now create billing records with subscription IDs
        billing_records, payment_activities = (
            subscriptions.create_billing_history(
                subscriptions_list, all_plans
            )
        )

        for billing in billing_records:
            session.add(billing)
        await session.commit()

        print(f'✅ Created {len(subscriptions_list)} subscriptions')
        print(f'✅ Created {len(billing_records)} billing records')

        # Add payment activity logs
        for activity in payment_activities:
            session.add(activity)
        await session.commit()

        print(f'✅ Created {len(payment_activities)} payment activity logs')

        # 7. Create AI Usage Logs
        print('🤖 Creating AI usage logs...')
        ai_usage_logs = ai_usage.create_ai_usage_logs(organizations_list)

        for log in ai_usage_logs:
            session.add(log)
        await session.commit()

        print(f'✅ Created {len(ai_usage_logs)} AI usage logs')

        # Get final counts
        final_plans = await session.execute(select(SubscriptionPlan))
        plan_count = len(list(final_plans.scalars().all()))

        # Calculate total revenue
        total_revenue = sum(b.amount for b in billing_records)
        active_subscriptions = sum(
            1 for s in subscriptions_list if s.status == 'active'
        )

        print('\n🎉 Seed data creation completed successfully!')
        print('\n📊 Summary:')
        print(f'   • {plan_count} subscription plans')
        print(f'   • {len(users_list)} users')
        print(
            f'     - {sum(1 for u in users_list if u.status == "active")} active users'
        )
        print(
            f'     - {sum(1 for u in users_list if u.status == "invited")} invited users'
        )
        print(
            f'     - {sum(1 for u in users_list if u.status == "suspended")} suspended users'
        )
        print(
            f'     - {sum(1 for u in users_list if u.is_verified)} verified users'
        )
        print(
            f'   • {len(organizations_list)} organizations with {len(organization_members)} total memberships'
        )
        print(f'   • {len(projects_list)} projects')
        print(
            f'   • {len(activities) + len(payment_activities)} activity logs'
        )
        print(
            f'   • {len(subscriptions_list)} subscriptions ({active_subscriptions} active)'
        )
        print(
            f'   • {len(billing_records)} billing records (Total revenue: ${total_revenue / 100:.2f})'
        )
        print(f'   • {len(ai_usage_logs)} AI usage logs')
        print(f'\n🔐 Default password for all users: {admin_password}')
        print('\n👤 User accounts:')
        print('   • admin@example.com (admin, superuser)')
        print('   • john@example.com (member, active)')
        print('   • jane@example.com (member, active)')
        print('   • sarah@example.com (member, active)')
        print('   • bob@example.com (member, invited)')
        print('   • alice@example.com (member, invited)')
        print('   • suspended@example.com (member, suspended)')
        print('   • mike@example.com (member, active)')
        print('   • emma@example.com (admin, active)')
        print('   • newuser@example.com (member, active, incomplete onboarding)')
        print('\n💳 Active Subscriptions:')
        print(
            f'   • Development Team: Business Plan (${all_plans["business"].price_monthly_usd / 100}/mo)'
        )
        print(
            f'   • Marketing Team: Pro Plan (${all_plans["pro"].price_monthly_usd / 100}/mo)'
        )
        print(
            f'   • Research Team: Starter Plan (${all_plans["starter"].price_monthly_usd / 100}/mo)'
        )
        print('   • Sales Department: Pro Plan (trialing)')
        print('   • Customer Success: Free Plan')

    await engine.dispose()


if __name__ == '__main__':
    asyncio.run(create_seed_data())
