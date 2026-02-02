# migrations/versions/add_mfa_secret_table.py
"""add mfa secret table

Revision ID: add_mfa_secret_table
Revises: add_ip_lockout_table
Create Date: 2026-02-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import datetime as dt

# revision identifiers
revision = 'add_mfa_secret_table'
down_revision = 'add_ip_lockout_table'
branch_labels = None
depends_on = None


def upgrade():
    # Create mfa_secret table
    op.create_table(
        'mfa_secret',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.func.uuid_generate_v4()),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenant.id', ondelete='CASCADE'), nullable=False),
        sa.Column('secret', sa.String(32), nullable=False),
        sa.Column('backup_codes', sa.JSON, nullable=True),
        sa.Column('is_verified', sa.Boolean, default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=lambda: dt.datetime.now(dt.timezone.utc)),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('backup_codes_used', sa.Integer, default=0, nullable=False),
    )

    # Create indexes
    op.create_index('idx_mfa_secret_user', 'mfa_secret', ['user_id'])
    op.create_index('idx_mfa_secret_tenant', 'mfa_secret', ['tenant_id'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_mfa_secret_tenant', table_name='mfa_secret')
    op.drop_index('idx_mfa_secret_user', table_name='mfa_secret')

    # Drop table
    op.drop_table('mfa_secret')