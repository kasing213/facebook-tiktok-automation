"""Add customer telegram fields and client link code table

Revision ID: l2g3h4i5j6k7
Revises: k1f2g3h4i5j6
Create Date: 2026-01-08 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'l2g3h4i5j6k7'
down_revision: Union[str, None] = 'k1f2g3h4i5j6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add merchant_id and telegram fields to invoice.customer
    op.add_column(
        'customer',
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=True),
        schema='invoice'
    )
    op.add_column(
        
        'customer',
        sa.Column('telegram_chat_id', sa.String(length=50), nullable=True),
        schema='invoice'
    )
    op.add_column(
        'customer',
        sa.Column('telegram_username', sa.String(length=100), nullable=True),
        schema='invoice'
    )
    op.add_column(
        'customer',
        sa.Column('telegram_linked_at', sa.DateTime(timezone=True), nullable=True),
        schema='invoice'
    )

    # Add foreign key for merchant_id
    op.create_foreign_key(
        'fk_customer_merchant',
        'customer',
        'user',
        ['merchant_id'],
        ['id'],
        source_schema='invoice',
        referent_schema='public',
        ondelete='CASCADE'
    )

    # Global uniqueness constraint on telegram_chat_id (one Telegram user = one client)
    # Using partial unique index where telegram_chat_id is not null
    op.execute("""
        CREATE UNIQUE INDEX uq_customer_telegram_chat_id
        ON invoice.customer (telegram_chat_id)
        WHERE telegram_chat_id IS NOT NULL
    """)

    # Performance indexes
    op.create_index(
        'idx_customer_merchant',
        'customer',
        ['merchant_id'],
        schema='invoice'
    )
    op.create_index(
        'idx_customer_tenant_merchant',
        'customer',
        ['tenant_id', 'merchant_id'],
        schema='invoice'
    )

    # Create client_link_code table for secure registration tokens
    op.create_table(
        'client_link_code',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('code', sa.String(length=64), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now() + interval '7 days'")),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['public.tenant.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['merchant_id'], ['public.user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['invoice.customer.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_client_link_code'),
        schema='invoice'
    )

    # Index for fast token lookup (only unused codes)
    op.execute("""
        CREATE INDEX idx_link_code_lookup
        ON invoice.client_link_code (code)
        WHERE used_at IS NULL
    """)

    # Add merchant_id to invoice table for ownership validation
    op.add_column(
        'invoice',
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=True),
        schema='invoice'
    )
    op.create_foreign_key(
        'fk_invoice_merchant',
        'invoice',
        'user',
        ['merchant_id'],
        ['id'],
        source_schema='invoice',
        referent_schema='public',
        ondelete='CASCADE'
    )
    op.create_index(
        'idx_invoice_merchant',
        'invoice',
        ['merchant_id'],
        schema='invoice'
    )


def downgrade() -> None:
    # Drop invoice.merchant_id
    op.drop_index('idx_invoice_merchant', table_name='invoice', schema='invoice')
    op.drop_constraint('fk_invoice_merchant', 'invoice', schema='invoice', type_='foreignkey')
    op.drop_column('invoice', 'merchant_id', schema='invoice')

    # Drop client_link_code table
    op.execute('DROP INDEX IF EXISTS invoice.idx_link_code_lookup')
    op.drop_table('client_link_code', schema='invoice')

    # Drop customer indexes and constraints
    op.drop_index('idx_customer_tenant_merchant', table_name='customer', schema='invoice')
    op.drop_index('idx_customer_merchant', table_name='customer', schema='invoice')
    op.execute('DROP INDEX IF EXISTS invoice.uq_customer_telegram_chat_id')
    op.drop_constraint('fk_customer_merchant', 'customer', schema='invoice', type_='foreignkey')

    # Drop customer columns
    op.drop_column('customer', 'telegram_linked_at', schema='invoice')
    op.drop_column('customer', 'telegram_username', schema='invoice')
    op.drop_column('customer', 'telegram_chat_id', schema='invoice')
    op.drop_column('customer', 'merchant_id', schema='invoice')
