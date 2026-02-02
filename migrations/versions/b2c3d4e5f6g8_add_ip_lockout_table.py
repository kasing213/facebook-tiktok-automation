# migrations/versions/add_ip_lockout_table.py
"""add ip lockout table

Revision ID: add_ip_lockout_table
Revises:
Create Date: 2026-02-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import datetime as dt

# revision identifiers
revision = 'b2c3d4e5f6g8'
down_revision = 'a1b2c3d4e5f7'
branch_labels = None
depends_on = None


def upgrade():
    # Create ip_lockout table
    op.create_table(
        'ip_lockout',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.func.uuid_generate_v4()),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('lockout_reason', sa.String(255), nullable=False),
        sa.Column('failed_attempts_count', sa.Integer, nullable=False, default=0),
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=False, default=lambda: dt.datetime.now(dt.timezone.utc)),
        sa.Column('unlock_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('unlocked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('unlocked_by', sa.String(255), nullable=True),
    )

    # Create indexes
    op.create_index('idx_ip_lockout_ip', 'ip_lockout', ['ip_address'])
    op.create_index('idx_ip_lockout_unlock_at', 'ip_lockout', ['unlock_at'])
    op.create_index('idx_ip_lockout_active', 'ip_lockout', ['ip_address', 'unlocked_at'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_ip_lockout_active', table_name='ip_lockout')
    op.drop_index('idx_ip_lockout_unlock_at', table_name='ip_lockout')
    op.drop_index('idx_ip_lockout_ip', table_name='ip_lockout')

    # Drop table
    op.drop_table('ip_lockout')