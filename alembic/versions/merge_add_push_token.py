"""merge alembic heads and add users.push_token for FCM

Revision ID: merge_add_push_token
Revises: 0b79c1911baa, add_fiscal_tables
Create Date: 2026-04-25

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'merge_add_push_token'
down_revision: Union[str, None] = (
    '0b79c1911baa',
    'add_fiscal_tables',
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('push_token', sa.String(length=512), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('users', 'push_token')
