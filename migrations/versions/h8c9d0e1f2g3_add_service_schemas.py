"""Add service schemas for invoice, scriptclient, audit_sales, ads_alert

Revision ID: h8c9d0e1f2g3
Revises: g7b8c9d0e1f2
Create Date: 2026-01-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'h8c9d0e1f2g3'
down_revision: Union[str, None] = 'g7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create schemas
    op.execute('CREATE SCHEMA IF NOT EXISTS invoice')
    op.execute('CREATE SCHEMA IF NOT EXISTS scriptclient')
    op.execute('CREATE SCHEMA IF NOT EXISTS audit_sales')
    op.execute('CREATE SCHEMA IF NOT EXISTS ads_alert')

    # Invoice Schema - Customer table
    op.create_table(
        'customer',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('meta', postgresql.JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['public.tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='invoice'
    )

    # Invoice Schema - Invoice table
    op.create_table(
        'invoice',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invoice_number', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('items', postgresql.JSONB(), nullable=True, server_default=sa.text("'[]'::jsonb")),
        sa.Column('meta', postgresql.JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['public.tenant.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['invoice.customer.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='invoice'
    )

    # Scriptclient Schema - Screenshot table
    op.create_table(
        'screenshot',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('file_url', sa.Text(), nullable=True),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('meta', postgresql.JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['public.tenant.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['verified_by'], ['public.user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        schema='scriptclient'
    )

    # Audit Sales Schema - Sale table
    op.create_table(
        'sale',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('meta', postgresql.JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['public.tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='audit_sales'
    )

    # Ads Alert Schema - Chat table
    op.create_table(
        'chat',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('chat_id', sa.String(length=100), nullable=False),
        sa.Column('chat_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('meta', postgresql.JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['public.tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='ads_alert'
    )

    # Ads Alert Schema - Promotion table
    op.create_table(
        'promotion',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('meta', postgresql.JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['public.tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='ads_alert'
    )

    # Ads Alert Schema - Promo Status table
    op.create_table(
        'promo_status',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_sent', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_scheduled', sa.DateTime(timezone=True), nullable=True),
        sa.Column('meta', postgresql.JSONB(), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['public.tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='ads_alert'
    )

    # Create indexes
    # Invoice schema indexes
    op.create_index('idx_invoice_customer_tenant', 'customer', ['tenant_id'], schema='invoice')
    op.create_index('idx_invoice_customer_name', 'customer', ['name'], schema='invoice')
    op.create_index('idx_invoice_invoice_tenant', 'invoice', ['tenant_id'], schema='invoice')
    op.create_index('idx_invoice_invoice_customer', 'invoice', ['customer_id'], schema='invoice')
    op.create_index('idx_invoice_invoice_created', 'invoice', ['created_at'], schema='invoice')

    # Scriptclient schema indexes
    op.create_index('idx_scriptclient_screenshot_tenant', 'screenshot', ['tenant_id'], schema='scriptclient')
    op.create_index('idx_scriptclient_screenshot_verified', 'screenshot', ['verified'], schema='scriptclient')

    # Audit sales schema indexes
    op.create_index('idx_audit_sales_sale_tenant', 'sale', ['tenant_id'], schema='audit_sales')
    op.create_index('idx_audit_sales_sale_date', 'sale', ['date'], schema='audit_sales')

    # Ads alert schema indexes
    op.create_index('idx_ads_alert_chat_tenant', 'chat', ['tenant_id'], schema='ads_alert')
    op.create_index('idx_ads_alert_promotion_tenant', 'promotion', ['tenant_id'], schema='ads_alert')
    op.create_index('idx_ads_alert_promotion_created', 'promotion', ['created_at'], schema='ads_alert')
    op.create_index('idx_ads_alert_promo_status_tenant', 'promo_status', ['tenant_id'], schema='ads_alert')


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_ads_alert_promo_status_tenant', table_name='promo_status', schema='ads_alert')
    op.drop_index('idx_ads_alert_promotion_created', table_name='promotion', schema='ads_alert')
    op.drop_index('idx_ads_alert_promotion_tenant', table_name='promotion', schema='ads_alert')
    op.drop_index('idx_ads_alert_chat_tenant', table_name='chat', schema='ads_alert')
    op.drop_index('idx_audit_sales_sale_date', table_name='sale', schema='audit_sales')
    op.drop_index('idx_audit_sales_sale_tenant', table_name='sale', schema='audit_sales')
    op.drop_index('idx_scriptclient_screenshot_verified', table_name='screenshot', schema='scriptclient')
    op.drop_index('idx_scriptclient_screenshot_tenant', table_name='screenshot', schema='scriptclient')
    op.drop_index('idx_invoice_invoice_created', table_name='invoice', schema='invoice')
    op.drop_index('idx_invoice_invoice_customer', table_name='invoice', schema='invoice')
    op.drop_index('idx_invoice_invoice_tenant', table_name='invoice', schema='invoice')
    op.drop_index('idx_invoice_customer_name', table_name='customer', schema='invoice')
    op.drop_index('idx_invoice_customer_tenant', table_name='customer', schema='invoice')

    # Drop tables in reverse order of creation (due to foreign keys)
    op.drop_table('promo_status', schema='ads_alert')
    op.drop_table('promotion', schema='ads_alert')
    op.drop_table('chat', schema='ads_alert')
    op.drop_table('sale', schema='audit_sales')
    op.drop_table('screenshot', schema='scriptclient')
    op.drop_table('invoice', schema='invoice')
    op.drop_table('customer', schema='invoice')

    # Drop schemas
    op.execute('DROP SCHEMA IF EXISTS ads_alert CASCADE')
    op.execute('DROP SCHEMA IF EXISTS audit_sales CASCADE')
    op.execute('DROP SCHEMA IF EXISTS scriptclient CASCADE')
    op.execute('DROP SCHEMA IF EXISTS invoice CASCADE')
