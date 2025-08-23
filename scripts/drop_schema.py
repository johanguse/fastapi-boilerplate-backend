import asyncio
from sqlalchemy import text
from src.common.session import engine

async def main():
    async with engine.begin() as conn:
        await conn.execute(text('DROP SCHEMA IF EXISTS public CASCADE'))
        await conn.execute(text('CREATE SCHEMA public'))

if __name__ == '__main__':
    asyncio.run(main())
