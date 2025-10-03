"""Database reset utilities for seed data."""
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy import text
from src.common.database import Base

async def reset_database(engine: AsyncEngine):
    """
    Drop all tables and recreate them.
    WARNING: This deletes ALL data!
    """
    async with engine.begin() as conn:
        print("🗑️  Dropping all tables...")
        
        # Drop all tables
        await conn.run_sync(Base.metadata.drop_all)
        
        # Drop any remaining enum types
        await conn.execute(text("DROP TYPE IF EXISTS organizationmemberrole CASCADE"))
        
        print("📦 Creating all tables...")
        
        # Recreate all tables
        await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Database reset complete")
