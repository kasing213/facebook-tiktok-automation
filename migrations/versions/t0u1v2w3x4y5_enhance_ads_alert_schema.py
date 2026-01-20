"""Enhance ads_alert schema with media support and scheduling

Revision ID: t0u1v2w3x4y5
Revises: s9n0o1p2q3r4
Create Date: 2026-01-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 't0u1v2w3x4y5'
down_revision: Union[str, None] = 's9n0o1p2q3r4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add media and scheduling columns to promotion table
    op.add_column('promotion', sa.Column('media_urls', postgresql.JSONB(), nullable=True, server_default=sa.text("'[]'::jsonb")), schema='ads_alert')
    op.add_column('promotion', sa.Column('media_type', sa.String(length=20), nullable=True, server_default='text'), schema='ads_alert')
    op.add_column('promotion', sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True), schema='ads_alert')
    op.add_column('promotion', sa.Column('target_type', sa.String(length=20), nullable=True, server_default='all'), schema='ads_alert')
    op.add_column('promotion', sa.Column('target_chat_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True, server_default=sa.text("'{}'::uuid[]")), schema='ads_alert')
    op.add_column('promotion', sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True), schema='ads_alert')

    # Add foreign key for created_by
    op.create_foreign_key(
        'fk_promotion_created_by_user',
        'promotion', 'user',
        ['created_by'], ['id'],
        source_schema='ads_alert',
        referent_schema='public',
        ondelete='SET NULL'
    )

    # Add customer and subscription columns to chat table
    op.add_column('chat', sa.Column('customer_name', sa.String(length=255), nullable=True), schema='ads_alert')
    op.add_column('chat', sa.Column('tags', postgresql.ARRAY(sa.String(length=100)), nullable=True, server_default=sa.text("'{}'::varchar[]")), schema='ads_alert')
    op.add_column('chat', sa.Column('subscribed', sa.Boolean(), nullable=True, server_default='true'), schema='ads_alert')

    # Create media_folder table for folder organization
    op.create_table(
        'media_folder',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['public.tenant.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['ads_alert.media_folder.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['public.user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'parent_id', 'name', name='uq_media_folder_tenant_parent_name'),
        schema='ads_alert'
    )

    # Create media table for file tracking
    op.create_table(
        'media',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('folder_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=True),
        sa.Column('storage_path', sa.String(length=500), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('thumbnail_path', sa.String(length=500), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),  # For videos, in seconds
        sa.Column('meta', postgresql.JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['public.tenant.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['folder_id'], ['ads_alert.media_folder.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['public.user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        schema='ads_alert'
    )

    # Create broadcast_log table to track sent promotions
    op.create_table(
        'broadcast_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('promotion_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chat_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),  # pending, sent, failed
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['public.tenant.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['promotion_id'], ['ads_alert.promotion.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chat_id'], ['ads_alert.chat.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='ads_alert'
    )

    # Create indexes
    op.create_index('idx_ads_alert_media_folder_tenant', 'media_folder', ['tenant_id'], schema='ads_alert')
    op.create_index('idx_ads_alert_media_folder_parent', 'media_folder', ['parent_id'], schema='ads_alert')
    op.create_index('idx_ads_alert_media_tenant', 'media', ['tenant_id'], schema='ads_alert')
    op.create_index('idx_ads_alert_media_folder', 'media', ['folder_id'], schema='ads_alert')
    op.create_index('idx_ads_alert_media_file_type', 'media', ['file_type'], schema='ads_alert')
    op.create_index('idx_ads_alert_promotion_scheduled', 'promotion', ['scheduled_at'], schema='ads_alert', postgresql_where=sa.text("status = 'scheduled'"))
    op.create_index('idx_ads_alert_promotion_status', 'promotion', ['status'], schema='ads_alert')
    op.create_index('idx_ads_alert_chat_subscribed', 'chat', ['subscribed'], schema='ads_alert')
    op.create_index('idx_ads_alert_broadcast_log_promotion', 'broadcast_log', ['promotion_id'], schema='ads_alert')
    op.create_index('idx_ads_alert_broadcast_log_chat', 'broadcast_log', ['chat_id'], schema='ads_alert')


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_ads_alert_broadcast_log_chat', table_name='broadcast_log', schema='ads_alert')
    op.drop_index('idx_ads_alert_broadcast_log_promotion', table_name='broadcast_log', schema='ads_alert')
    op.drop_index('idx_ads_alert_chat_subscribed', table_name='chat', schema='ads_alert')
    op.drop_index('idx_ads_alert_promotion_status', table_name='promotion', schema='ads_alert')
    op.drop_index('idx_ads_alert_promotion_scheduled', table_name='promotion', schema='ads_alert')
    op.drop_index('idx_ads_alert_media_file_type', table_name='media', schema='ads_alert')
    op.drop_index('idx_ads_alert_media_folder', table_name='media', schema='ads_alert')
    op.drop_index('idx_ads_alert_media_tenant', table_name='media', schema='ads_alert')
    op.drop_index('idx_ads_alert_media_folder_parent', table_name='media_folder', schema='ads_alert')
    op.drop_index('idx_ads_alert_media_folder_tenant', table_name='media_folder', schema='ads_alert')

    # Drop tables
    op.drop_table('broadcast_log', schema='ads_alert')
    op.drop_table('media', schema='ads_alert')
    op.drop_table('media_folder', schema='ads_alert')

    # Drop foreign key constraint
    op.drop_constraint('fk_promotion_created_by_user', 'promotion', schema='ads_alert', type_='foreignkey')

    # Drop columns from chat table
    op.drop_column('chat', 'subscribed', schema='ads_alert')
    op.drop_column('chat', 'tags', schema='ads_alert')
    op.drop_column('chat', 'customer_name', schema='ads_alert')

    # Drop columns from promotion table
    op.drop_column('promotion', 'created_by', schema='ads_alert')
    op.drop_column('promotion', 'target_chat_ids', schema='ads_alert')
    op.drop_column('promotion', 'target_type', schema='ads_alert')
    op.drop_column('promotion', 'scheduled_at', schema='ads_alert')
    op.drop_column('promotion', 'media_type', schema='ads_alert')
    op.drop_column('promotion', 'media_urls', schema='ads_alert')
