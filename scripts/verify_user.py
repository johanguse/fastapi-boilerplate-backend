"""Mark user as verified."""
import asyncio
import sys
from sqlalchemy import select, update
from src.auth.models import User
from src.common.session import get_async_session

async def verify_user(email: str):
    """Mark user as verified."""
    async for session in get_async_session():
        # Get user
        result = await session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f'✗ User not found: {email}')
            return
        
        if user.is_verified:
            print(f'✓ User {email} is already verified')
            return
        
        # Mark as verified
        user.is_verified = True
        await session.commit()
        
        print(f'✓ User {email} has been marked as verified!')
        print(f'  - Is Verified: {user.is_verified}')
        print(f'  - Is Active: {user.is_active}')

if __name__ == '__main__':
    email = sys.argv[1] if len(sys.argv) > 1 else 'johanguse@gmail.com'
    asyncio.run(verify_user(email))
