def upgrade():
    op.alter_column('activity_logs', 'metadata', new_column_name='action_metadata')
    op.add_column('activity_logs', sa.Column('action_type', sa.String(length=20), nullable=False, server_default='user'))
    op.add_column('activity_logs', sa.Column('ip_address', sa.String(length=45)))
    op.add_column('activity_logs', sa.Column('user_agent', sa.Text()))
    op.create_index('ix_activity_logs_created_at', 'activity_logs', ['created_at'])
    op.create_index('ix_activity_logs_action_type', 'activity_logs', ['action_type'])
    op.create_index('ix_activity_logs_team_user', 'activity_logs', ['team_id', 'user_id'])

def downgrade():
    op.alter_column('activity_logs', 'action_metadata', new_column_name='metadata')
    op.drop_index('ix_activity_logs_team_user')
    op.drop_index('ix_activity_logs_action_type')
    op.drop_index('ix_activity_logs_created_at')
    op.drop_column('activity_logs', 'user_agent')
    op.drop_column('activity_logs', 'ip_address')
    op.drop_column('activity_logs', 'action_type') 