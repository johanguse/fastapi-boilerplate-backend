"""Check user verification status."""
import asyncio
from sqlalchemy import select
from src.auth.models import User
from src.common.session import get_async_session

async def check_user(email: str):
    """Check if user is verified."""
    async for session in get_async_session():
        result = await session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if user:
            print(f'✓ User found: {user.email}')
            print(f'  - Is Verified: {user.is_verified}')
            print(f'  - Is Active: {user.is_active}')
            print(f'  - Onboarding Completed: {user.onboarding_completed}')
            print(f'  - Onboarding Step: {user.onboarding_step}')
        else:
            print(f'✗ User not found: {email}')

if __name__ == '__main__':
    import sys
    email = sys.argv[1] if len(sys.argv) > 1 else 'johanguse@gmail.com'
    asyncio.run(check_user(email))
