#!/usr/bin/env python3
"""
Database initialization script.
Creates the initial database migration and sets up the admin user.
"""

import asyncio
import logging
from pathlib import Path
import sys

from sqlalchemy.ext.asyncio import AsyncSession

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.auth.service import AuthService  # noqa: E402
from src.common.database import engine  # noqa: E402
from src.common.models import Base  # noqa: E402
from src.config.settings import config  # noqa: E402

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


async def create_tables():
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables created successfully")


async def create_admin_user():
    """Create the initial admin user."""
    async with AsyncSession(engine) as session:
        # Check if admin user already exists
        existing_admin = await AuthService.get_user_by_email(
            session, config.ADMIN_EMAIL
        )

        if existing_admin:
            logger.info("i  Admin user already exists: %s", config.ADMIN_EMAIL)
            return

        # Create admin user
        admin_user = await AuthService.create_user(
            db=session,
            email=config.ADMIN_EMAIL,
            password=config.ADMIN_PASSWORD,
            name=config.ADMIN_NAME,
            is_superuser=True,
        )

        # Mark as verified
        admin_user.is_verified = True
        await session.commit()

        logger.info("✅ Admin user created successfully: %s", config.ADMIN_EMAIL)


async def main():
    """Main initialization function."""
    logger.info("🚀 Initializing database...")

    try:
        await create_tables()
        await create_admin_user()
        logger.info("✅ Database initialization completed successfully!")

    except Exception as e:
        logger.error("❌ Database initialization failed: %s", e)
        sys.exit(1)

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
