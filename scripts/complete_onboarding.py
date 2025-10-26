#!/usr/bin/env python3
"""
Script to manually mark a user's onboarding as completed.
Usage: poetry run python scripts/complete_onboarding.py <email>
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.auth.models import User


async def complete_onboarding(email: str):
    """Mark user's onboarding as completed."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return
    
    # Convert postgresql:// to postgresql+asyncpg://
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    engine = create_async_engine(database_url)
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.email == email)  # type: ignore[arg-type]
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"User not found: {email}")
            await engine.dispose()
            return
        
        print(f"Found user: {user.email}")
        print(f"Current status:")
        print(f"  - Onboarding completed: {user.onboarding_completed}")
        print(f"  - Onboarding step: {user.onboarding_step}")
        
        # Update onboarding status
        user.onboarding_completed = True
        user.onboarding_step = 999  # Mark as fully completed
        
        await session.commit()
        
        print(f"\nUpdated status:")
        print(f"  - Onboarding completed: {user.onboarding_completed}")
        print(f"  - Onboarding step: {user.onboarding_step}")
        print(f"\n✅ User {email} can now access the dashboard!")
    
    await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: poetry run python scripts/complete_onboarding.py <email>")
        sys.exit(1)
    
    email = sys.argv[1]
    asyncio.run(complete_onboarding(email))
