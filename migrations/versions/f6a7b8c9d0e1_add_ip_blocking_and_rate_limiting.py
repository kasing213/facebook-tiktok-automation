"""Add IP blocking and rate limiting tables

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-01-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create IP rule type enum
    ip_rule_type_enum = postgresql.ENUM(
        'whitelist',
        'blacklist',
        'auto_banned',
        name='ipruletype',
        create_type=False
    )
    ip_rule_type_enum.create(op.get_bind(), checkfirst=True)

    # Create ip_access_rule table
    op.create_table('ip_access_rule',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=False),  # IPv6 max length
        sa.Column('rule_type', ip_rule_type_enum, nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for ip_access_rule
    op.create_index('idx_ip_access_rule_ip', 'ip_access_rule', ['ip_address'], unique=False)
    op.create_index('idx_ip_access_rule_type', 'ip_access_rule', ['rule_type'], unique=False)
    op.create_index('idx_ip_access_rule_active', 'ip_access_rule', ['is_active'], unique=False)
    op.create_index('idx_ip_access_rule_expires', 'ip_access_rule', ['expires_at'], unique=False)

    # Create rate_limit_violation table
    op.create_table('rate_limit_violation',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('endpoint', sa.String(length=500), nullable=False),
        sa.Column('violation_count', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('last_violation_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('auto_banned', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for rate_limit_violation
    op.create_index('idx_rate_limit_violation_ip', 'rate_limit_violation', ['ip_address'], unique=False)
    op.create_index('idx_rate_limit_violation_last', 'rate_limit_violation', ['last_violation_at'], unique=False)
    op.create_index('idx_rate_limit_violation_ip_endpoint', 'rate_limit_violation', ['ip_address', 'endpoint'], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_index('idx_rate_limit_violation_ip_endpoint', table_name='rate_limit_violation')
    op.drop_index('idx_rate_limit_violation_last', table_name='rate_limit_violation')
    op.drop_index('idx_rate_limit_violation_ip', table_name='rate_limit_violation')
    op.drop_table('rate_limit_violation')

    op.drop_index('idx_ip_access_rule_expires', table_name='ip_access_rule')
    op.drop_index('idx_ip_access_rule_active', table_name='ip_access_rule')
    op.drop_index('idx_ip_access_rule_type', table_name='ip_access_rule')
    op.drop_index('idx_ip_access_rule_ip', table_name='ip_access_rule')
    op.drop_table('ip_access_rule')

    # Drop enum
    ip_rule_type_enum = postgresql.ENUM(
        'whitelist',
        'blacklist',
        'auto_banned',
        name='ipruletype',
        create_type=False
    )
    ip_rule_type_enum.drop(op.get_bind(), checkfirst=True)
