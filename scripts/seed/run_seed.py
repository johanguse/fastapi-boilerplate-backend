#!/usr/bin/env python3
"""
Main seed script for development database.
Automatically resets the database and creates fresh seed data.
WARNING: This is for DEVELOPMENT ONLY and will DELETE ALL DATA!
"""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from seed.activity_logs import create_activity_logs
from seed.constants import DEFAULT_PASSWORD
from seed.organizations import (
    create_organization_members,
    create_organizations,
)
from seed.projects import create_projects

# Import seed data creators
from seed.reset import reset_database
from seed.subscription_plans import create_subscription_plans
from seed.subscriptions import create_subscriptions_and_billing
from seed.users import create_users
from src.common.config import settings


async def run_seed():
    """Run the complete seed process."""
    print('🌱 Starting seed process...\n')

    # Create async engine and session
    database_url = str(settings.DATABASE_URL).replace(
        'postgresql://', 'postgresql+asyncpg://'
    )
    engine = create_async_engine(database_url, echo=False)

    # Reset database (drop and recreate all tables)
    await reset_database(engine)
    print()

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # 1. Create subscription plans first
        print('💳 Creating subscription plans...')
        plans = create_subscription_plans()
        for plan in plans:
            session.add(plan)
        await session.commit()
        for plan in plans:
            await session.refresh(plan)
        plans_dict = {plan.name: plan for plan in plans}
        print(f'✅ Created {len(plans)} subscription plans')

        # 2. Create users
        print('👥 Creating users...')
        users = create_users()
        for user in users:
            session.add(user)
        await session.commit()
        for user in users:
            await session.refresh(user)
        print(f'✅ Created {len(users)} users')

        # 3. Create organizations
        print('🏢 Creating organizations...')
        organizations = create_organizations()
        for org in organizations:
            session.add(org)
        await session.commit()
        for org in organizations:
            await session.refresh(org)
        print(f'✅ Created {len(organizations)} organizations')

        # 4. Create organization memberships
        print('👤 Creating organization memberships...')
        org_members = create_organization_members(organizations, users)
        for member in org_members:
            session.add(member)
        await session.commit()
        print(f'✅ Created {len(org_members)} organization memberships')

        # 5. Create projects
        print('📁 Creating projects...')
        projects = create_projects(organizations)
        for project in projects:
            session.add(project)
        await session.commit()
        for project in projects:
            await session.refresh(project)
        print(f'✅ Created {len(projects)} projects')

        # 6. Create activity logs
        print('📝 Creating activity logs...')
        activities = create_activity_logs(
            users, organizations, org_members, projects
        )
        for activity in activities:
            session.add(activity)
        await session.commit()
        print(f'✅ Created {len(activities)} activity logs')

        # 7. Create subscriptions and billing
        print('💰 Creating subscriptions and billing history...')
        subscriptions, billing_records, payment_activities = (
            create_subscriptions_and_billing(organizations, plans_dict)
        )

        for sub in subscriptions:
            session.add(sub)
        await session.flush()  # Flush to get subscription IDs

        # Update subscription IDs in billing records
        for i, billing in enumerate(billing_records):
            billing.subscription_id = (
                subscriptions[i // 3].id if i < 6 else subscriptions[0].id
            )
            session.add(billing)

        for activity in payment_activities:
            session.add(activity)

        await session.commit()
        print(f'✅ Created {len(subscriptions)} subscriptions')
        print(f'✅ Created {len(billing_records)} billing records')
        print(f'✅ Created {len(payment_activities)} payment activity logs')

        # Calculate totals
        total_revenue = sum(b.amount for b in billing_records)
        active_subscriptions = sum(
            1 for s in subscriptions if s.status == 'active'
        )
        total_activities = len(activities) + len(payment_activities)

        print('\n' + '=' * 60)
        print('🎉 Seed data creation completed successfully!')
        print('=' * 60)
        print('\n📊 Summary:')
        print(f'   • {len(plans)} subscription plans')
        print(f'   • {len(users)} users')
        print(f'     - {sum(1 for u in users if u.status == "active")} active')
        print(
            f'     - {sum(1 for u in users if u.status == "invited")} invited'
        )
        print(
            f'     - {sum(1 for u in users if u.status == "suspended")} suspended'
        )
        print(f'     - {sum(1 for u in users if u.is_verified)} verified')
        print(f'   • {len(organizations)} organizations')
        print(f'   • {len(org_members)} organization memberships')
        print(f'   • {len(projects)} projects')
        print(f'   • {total_activities} activity logs')
        print(
            f'   • {len(subscriptions)} subscriptions ({active_subscriptions} active)'
        )
        print(f'   • {len(billing_records)} billing records')
        print(f'   • Total revenue: ${total_revenue / 100:.2f}')

        print(f'\n🔐 Default password for all users: {DEFAULT_PASSWORD}')
        print('\n👥 User accounts:')
        print('   • admin@example.com (admin, superuser)')
        print('   • john@example.com (member)')
        print('   • jane@example.com (member)')
        print('   • sarah@example.com (member)')
        print('   • bob@example.com (member, invited)')
        print('   • alice@example.com (member, invited)')
        print('   • suspended@example.com (member, suspended)')
        print('   • mike@example.com (member)')
        print('   • emma@example.com (admin)')

        print('\n💳 Active Subscriptions:')
        print(
            f'   • Development Team: Business (${plans_dict["business"].price_monthly_usd / 100}/mo)'
        )
        print(
            f'   • Marketing Team: Pro (${plans_dict["pro"].price_monthly_usd / 100}/mo)'
        )
        print(
            f'   • Research Team: Starter (${plans_dict["starter"].price_monthly_usd / 100}/mo)'
        )
        print('   • Sales Department: Pro (trialing)')
        print('   • Customer Success: Free')
        print()

    await engine.dispose()


if __name__ == '__main__':
    asyncio.run(run_seed())
