"""Rename teams to organizations and update FKs

Revision ID: 20250821_orgs
Revises: 646a06554f40
Create Date: 2025-08-21 12:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250821_orgs'
down_revision: Union[str, None] = '646a06554f40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=120), nullable=True, unique=True),
        sa.Column('logo_url', sa.Text(), nullable=True),
        sa.Column('stripe_customer_id', sa.Text(), nullable=True, unique=True),
        sa.Column('stripe_subscription_id', sa.Text(), nullable=True, unique=True),
        sa.Column('stripe_product_id', sa.Text(), nullable=True),
        sa.Column('plan_name', sa.String(length=50), nullable=True),
        sa.Column('subscription_status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('max_projects', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('active_projects', sa.Integer(), nullable=False, server_default='0'),
    )

    # 2) Create organization_members
    op.create_table(
        'organization_members',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='member'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
    )

    # 3) Create organization_invitations
    op.create_table(
        'organization_invitations',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('organization_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('invited_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('invitee_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
    )

    # 4) Projects: add organization_id, backfill from teams if exists, then drop team_id
    with op.batch_alter_table('projects') as batch_op:
        batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_projects_org', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')

    # Backfill organization_id from teams if column exists
    conn = op.get_bind()
    insp = sa.inspect(conn)
    project_cols = [c['name'] for c in insp.get_columns('projects')]
    if 'team_id' in project_cols:
        conn.execute(sa.text('UPDATE projects p SET organization_id = p.team_id'))
        # Now set not null and drop team_id
        with op.batch_alter_table('projects') as batch_op:
            batch_op.alter_column('organization_id', nullable=False)
            try:
                batch_op.drop_constraint('projects_team_id_fkey', type_='foreignkey')
            except Exception:
                pass
            batch_op.drop_column('team_id')

    # 5) Activity logs: add organization_id, backfill, index, drop team_id
    with op.batch_alter_table('activity_logs') as batch_op:
        batch_op.add_column(sa.Column('organization_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_activity_logs_org', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
        try:
            batch_op.drop_index('ix_activity_logs_team_user')
        except Exception:
            pass
        batch_op.create_index('ix_activity_logs_org_user', ['organization_id', 'user_id'])

    act_cols = [c['name'] for c in insp.get_columns('activity_logs')]
    if 'team_id' in act_cols:
        conn.execute(sa.text('UPDATE activity_logs a SET organization_id = a.team_id'))
        with op.batch_alter_table('activity_logs') as batch_op:
            batch_op.drop_constraint(None, type_='foreignkey')  # best-effort
            batch_op.drop_column('team_id')

    # 6) Optionally drop teams tables (if present)
    if insp.has_table('team_members'):
        op.drop_table('team_members')
    if insp.has_table('invitations'):
        op.drop_table('invitations')
    if insp.has_table('teams'):
        op.drop_table('teams')


def downgrade() -> None:
    # Not implementing full downgrade for simplicity of refactor
    raise RuntimeError('Downgrade not supported for orgs refactor')
