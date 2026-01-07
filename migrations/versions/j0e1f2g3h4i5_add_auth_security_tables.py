"""Add RefreshToken and TokenBlacklist tables for auth security

Revision ID: j0e1f2g3h4i5
Revises: i9d0e1f2g3h4
Create Date: 2026-01-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'j0e1f2g3h4i5'
down_revision: Union[str, None] = 'i9d0e1f2g3h4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create refresh_token table
    op.create_table(
        'refresh_token',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('family_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('replaced_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('device_info', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash', name='uq_refresh_token_hash')
    )

    # Create refresh_token indexes
    op.create_index('idx_refresh_token_hash', 'refresh_token', ['token_hash'], unique=True)
    op.create_index('idx_refresh_token_user', 'refresh_token', ['user_id'])
    op.create_index('idx_refresh_token_family', 'refresh_token', ['family_id'])
    op.create_index('idx_refresh_token_expires', 'refresh_token', ['expires_at'])

    # Create token_blacklist table
    op.create_table(
        'token_blacklist',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('jti', sa.String(length=36), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('reason', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('jti', name='uq_token_blacklist_jti')
    )

    # Create token_blacklist indexes
    op.create_index('idx_token_blacklist_jti', 'token_blacklist', ['jti'], unique=True)
    op.create_index('idx_token_blacklist_expires', 'token_blacklist', ['expires_at'])
    op.create_index('idx_token_blacklist_user', 'token_blacklist', ['user_id'])


def downgrade() -> None:
    # Drop token_blacklist indexes and table
    op.drop_index('idx_token_blacklist_user', table_name='token_blacklist')
    op.drop_index('idx_token_blacklist_expires', table_name='token_blacklist')
    op.drop_index('idx_token_blacklist_jti', table_name='token_blacklist')
    op.drop_table('token_blacklist')

    # Drop refresh_token indexes and table
    op.drop_index('idx_refresh_token_expires', table_name='refresh_token')
    op.drop_index('idx_refresh_token_family', table_name='refresh_token')
    op.drop_index('idx_refresh_token_user', table_name='refresh_token')
    op.drop_index('idx_refresh_token_hash', table_name='refresh_token')
    op.drop_table('refresh_token')
