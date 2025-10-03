"""Drop alembic_version table to reset migration history."""
from sqlalchemy import create_engine, text
from src.common.config import settings

engine = create_engine(str(settings.DATABASE_URL))
with engine.begin() as conn:
    conn.execute(text('DROP TABLE IF EXISTS alembic_version'))
    print('✅ Dropped alembic_version table')
