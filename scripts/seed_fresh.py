"""
Fresh seed data script - DELETES all existing data and creates fresh seed data.
WARNING: This will delete ALL data in the database!
"""

import asyncio

from sqlalchemy import delete
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


async def delete_all_data():
    """Delete all existing data from the database."""
    print('⚠️  WARNING: This will delete ALL data from the database!')
    print('Press Ctrl+C within 5 seconds to cancel...')
    await asyncio.sleep(5)

    database_url = str(settings.DATABASE_URL).replace(
        'postgresql://', 'postgresql+asyncpg://'
    )
    engine = create_async_engine(database_url)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        print('🗑️  Deleting existing data...')

        # Delete in reverse order of dependencies with error handling
        tables_to_delete = [
            ('AI Usage Logs', AIUsageLog),
            ('Billing History', BillingHistory),
            ('Customer Subscriptions', CustomerSubscription),
            ('Activity Logs', ActivityLog),
            ('Projects', Project),
            ('Organization Members', OrganizationMember),
            ('Organizations', Organization),
            ('Email Tokens', EmailToken),
            ('Users', User),
            ('Subscription Plans', SubscriptionPlan),
        ]

        for table_name, model in tables_to_delete:
            try:
                await session.execute(delete(model))
                print(f'   ✓ Deleted {table_name}')
            except Exception as e:
                print(f'   ⚠️  Skipped {table_name} (table may not exist): {str(e).split(":")[-1].strip()}')
                continue

        await session.commit()
        print('✅ All existing data deleted')

    await engine.dispose()


if __name__ == '__main__':
    asyncio.run(delete_all_data())
    print('\n📦 Now running the seed script...')
    import os
    import sys

    # Import and run the regular seed script
    sys.path.insert(0, os.path.dirname(__file__))
    # Import from the seed.py file, not the seed/ directory
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        'seed_module', os.path.join(os.path.dirname(__file__), 'seed.py')
    )
    seed_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seed_module)
    asyncio.run(seed_module.create_seed_data())
