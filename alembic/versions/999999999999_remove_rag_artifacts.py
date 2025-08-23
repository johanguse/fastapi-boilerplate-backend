"""Remove RAG-related artifacts

Revision ID: 999999999999
Revises: 20250821_orgs
Create Date: 2025-08-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '999999999999'
down_revision: Union[str, None] = '20250821_orgs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop tables if they exist (idempotent where possible)
    conn = op.get_bind()

    # Drop training_data table if present
    if conn.dialect.has_table(conn, 'training_data'):
        op.drop_table('training_data')

    # Drop chats table if present
    if conn.dialect.has_table(conn, 'chats'):
        op.drop_table('chats')

    # Drop ENUM type modelstatus if present (PostgreSQL)
    try:
        op.execute("DROP TYPE IF EXISTS modelstatus")
    except Exception:
        pass


def downgrade() -> None:
    # No-op: we won't recreate RAG artifacts
    pass
