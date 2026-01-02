"""add_social_identity_and_facebook_page_tables

Revision ID: a1b2c3d4e5f6
Revises: 9a1f8f3c1b2a
Create Date: 2025-12-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "9a1f8f3c1b2a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use existing platform enum (created in earlier migration)
    from sqlalchemy.dialects.postgresql import ENUM
    platform_enum = ENUM('facebook', 'tiktok', name='platform', create_type=False)

    # Create social_identity table
    op.create_table(
        'social_identity',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenant.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('platform', platform_enum, nullable=False),
        sa.Column('platform_user_id', sa.String(255), nullable=False),
        sa.Column('facebook_user_id', sa.String(255), nullable=True),  # CRITICAL: Real FB user ID (stable anchor)
        sa.Column('platform_username', sa.String(255), nullable=True),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('profile_data', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )

    # Add unique constraints for social_identity
    op.create_unique_constraint('uq_social_identity_platform_user', 'social_identity', ['platform', 'platform_user_id'])
    op.create_unique_constraint('uq_social_identity_tenant_user_platform', 'social_identity', ['tenant_id', 'user_id', 'platform'])

    # Add indexes for social_identity
    op.create_index('idx_social_identity_tenant_user', 'social_identity', ['tenant_id', 'user_id'])
    op.create_index('idx_social_identity_platform_user', 'social_identity', ['platform', 'platform_user_id'])

    # Create facebook_page table
    op.create_table(
        'facebook_page',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('social_identity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('social_identity.id', ondelete='CASCADE'), nullable=False),
        sa.Column('page_id', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(255), nullable=True),
        sa.Column('tasks', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('page_data', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )

    # Add indexes for facebook_page
    op.create_index('idx_facebook_page_identity', 'facebook_page', ['social_identity_id'])
    op.create_index('idx_facebook_page_page_id', 'facebook_page', ['page_id'])


def downgrade() -> None:
    # Drop facebook_page table
    op.drop_index('idx_facebook_page_page_id', table_name='facebook_page')
    op.drop_index('idx_facebook_page_identity', table_name='facebook_page')
    op.drop_table('facebook_page')

    # Drop social_identity table
    op.drop_index('idx_social_identity_platform_user', table_name='social_identity')
    op.drop_index('idx_social_identity_tenant_user', table_name='social_identity')
    op.drop_constraint('uq_social_identity_tenant_user_platform', 'social_identity', type_='unique')
    op.drop_constraint('uq_social_identity_platform_user', 'social_identity', type_='unique')
    op.drop_table('social_identity')
