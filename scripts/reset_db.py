import asyncio
import subprocess
import sys

from sqlalchemy import text

from src.common.session import engine


async def reset_db():
    # 1) Drop and recreate the public schema for a clean state
    async with engine.begin() as conn:
        await conn.execute(text('DROP SCHEMA IF EXISTS public CASCADE'))
        await conn.execute(text('CREATE SCHEMA public'))

    # 2) Run Alembic migrations to head to ensure schema matches code
    # Use the same Python interpreter and environment
    result = subprocess.run(
        [sys.executable, '-m', 'alembic', 'upgrade', 'head'],
        check=False,
        capture_output=True,
        text=True,
        cwd=None,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)
    else:
        # Optionally print condensed success output
        print('Alembic upgrade head completed')


if __name__ == '__main__':
    asyncio.run(reset_db())
