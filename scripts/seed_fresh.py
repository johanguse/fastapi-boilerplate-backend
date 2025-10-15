"""
Fresh seed data script - DELETES all existing data and creates fresh seed data.
WARNING: This will delete ALL data in the database!
"""

import asyncio

from sqlalchemy import delete
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


async def delete_all_data():
    """Delete all existing data from the database."""
    print('⚠️  WARNING: This will delete ALL data from the database!')
    print('Press Ctrl+C within 3 seconds to cancel...')
    await asyncio.sleep(3)

    database_url = str(settings.DATABASE_URL).replace(
        'postgresql://', 'postgresql+asyncpg://'
    )
    engine = create_async_engine(database_url)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        print('🗑️  Deleting existing data...')

        # Delete in reverse order of dependencies
        await session.execute(delete(BillingHistory))
        await session.execute(delete(CustomerSubscription))
        await session.execute(delete(ActivityLog))
        await session.execute(delete(Project))
        await session.execute(delete(OrganizationMember))
        await session.execute(delete(Organization))
        await session.execute(delete(User))
        await session.execute(delete(SubscriptionPlan))

        await session.commit()
        print('✅ All data deleted')

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
