"""Initial database schema with multi-tenant architecture

Revision ID: 001
Revises:
Create Date: 2025-09-25 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Let SQLAlchemy handle enum creation automatically with checkfirst=True

    # Create tenant table
    op.create_table('tenant',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )

    # Create user table
    op.create_table('user',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('telegram_user_id', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('role', sa.Enum('admin', 'user', 'viewer', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'telegram_user_id', name='uq_user_tenant_telegram'),
        sa.UniqueConstraint('tenant_id', 'email', name='uq_user_tenant_email')
    )
    op.create_index('idx_user_telegram_id', 'user', ['telegram_user_id'], unique=False)

    # Create destination table
    op.create_table('destination',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.Enum('telegram_chat', 'webhook', 'email', name='destinationtype'), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_destination_tenant_type', 'destination', ['tenant_id', 'type'], unique=False)

    # Create ad_token table
    op.create_table('ad_token',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.Enum('facebook', 'tiktok', name='platform'), nullable=False),
        sa.Column('account_ref', sa.String(length=255), nullable=True),
        sa.Column('account_name', sa.String(length=255), nullable=True),
        sa.Column('access_token_enc', sa.String(), nullable=False),
        sa.Column('refresh_token_enc', sa.String(), nullable=True),
        sa.Column('scope', sa.String(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_valid', sa.Boolean(), nullable=False),
        sa.Column('last_validated', sa.DateTime(), nullable=True),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'platform', 'account_ref', name='uq_token_tenant_platform_account')
    )
    op.create_index('idx_ad_token_platform', 'ad_token', ['platform'], unique=False)
    op.create_index('idx_ad_token_expires', 'ad_token', ['expires_at'], unique=False)

    # Create automation table
    op.create_table('automation',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('destination_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.Enum('scheduled_report', 'alert', 'data_sync', name='automationtype'), nullable=False),
        sa.Column('status', sa.Enum('active', 'paused', 'stopped', 'error', name='automationstatus'), nullable=False),
        sa.Column('schedule_config', sa.JSON(), nullable=True),
        sa.Column('automation_config', sa.JSON(), nullable=False),
        sa.Column('platforms', sa.JSON(), nullable=True),
        sa.Column('last_run', sa.DateTime(), nullable=True),
        sa.Column('next_run', sa.DateTime(), nullable=True),
        sa.Column('run_count', sa.Integer(), nullable=False),
        sa.Column('error_count', sa.Integer(), nullable=False),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['destination_id'], ['destination.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_automation_next_run', 'automation', ['next_run'], unique=False)
    op.create_index('idx_automation_tenant_status', 'automation', ['tenant_id', 'status'], unique=False)

    # Create automation_run table
    op.create_table('automation_run',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('automation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('logs', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['automation_id'], ['automation.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_automation_run_started', 'automation_run', ['started_at'], unique=False)
    op.create_index('idx_automation_run_automation_status', 'automation_run', ['automation_id', 'status'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_table('automation_run')
    op.drop_table('automation')
    op.drop_table('ad_token')
    op.drop_table('destination')
    op.drop_table('user')
    op.drop_table('tenant')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS automationtype")
    op.execute("DROP TYPE IF EXISTS automationstatus")
    op.execute("DROP TYPE IF EXISTS destinationtype")
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS platform")