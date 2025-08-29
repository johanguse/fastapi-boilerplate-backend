#!/usr/bin/env python3
"""
Test script to generate correct password hash for FastAPI Users
"""
import asyncio
from src.auth.users import get_user_manager
from src.common.session import get_async_session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.common.config import settings

async def test_password():
    """Test password hashing and verification"""
    
    # Create async engine and session
    database_url = str(settings.DATABASE_URL).replace('postgresql://', 'postgresql+asyncpg://')
    engine = create_async_engine(database_url)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Get user manager
        from src.auth.users import UserManager
        from src.auth.models import User
        
        user_manager = UserManager(User, session)
        
        # Test password hashing
        password = "admin123"
        hashed = user_manager.password_helper.hash(password)
        print(f"Password: {password}")
        print(f"Hashed: {hashed}")
        
        # Test verification
        verification_result = user_manager.password_helper.verify_and_update(password, hashed)
        print(f"Verification result: {verification_result}")
        
        # Test with the seed file hash
        seed_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8xq/2vV3za"
        verification_seed = user_manager.password_helper.verify_and_update(password, seed_hash)
        print(f"Seed hash verification: {verification_seed}")
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_password())