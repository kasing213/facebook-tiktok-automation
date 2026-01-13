"""Add inventory system

Revision ID: l2g3h4i5j6k7
Revises: k1f2g3h4i5j6
Create Date: 2026-01-13 09:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'o5j6k7l8m9n0'
down_revision = 'n4i5j6k7l8m9'
branch_labels = None
depends_on = None


def upgrade():
    # Create inventory schema
    op.execute("CREATE SCHEMA IF NOT EXISTS inventory")

    # Products table
    op.create_table('products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenant.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('sku', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False, server_default='0.00'),
        sa.Column('cost_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('currency', sa.String(3), nullable=False, server_default="'KHR'"),
        sa.Column('current_stock', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('low_stock_threshold', sa.Integer(), nullable=True, server_default='10'),
        sa.Column('track_stock', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        schema='inventory'
    )

    # Stock movements table
    op.create_table('stock_movements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenant.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('inventory.products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('movement_type', sa.String(20), nullable=False),  # 'in', 'out', 'adjustment'
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('reference_type', sa.String(50), nullable=True),  # 'invoice', 'manual', 'initial'
        sa.Column('reference_id', sa.String(255), nullable=True),  # invoice_id or other reference
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        schema='inventory'
    )

    # Indexes for performance
    op.create_index('idx_products_tenant', 'products', ['tenant_id'], schema='inventory')
    op.create_index('idx_products_sku', 'products', ['sku'], schema='inventory')
    op.create_index('idx_products_active', 'products', ['is_active'], schema='inventory')
    op.create_index('idx_products_stock', 'products', ['current_stock'], schema='inventory')

    op.create_index('idx_stock_movements_tenant', 'stock_movements', ['tenant_id'], schema='inventory')
    op.create_index('idx_stock_movements_product', 'stock_movements', ['product_id'], schema='inventory')
    op.create_index('idx_stock_movements_type', 'stock_movements', ['movement_type'], schema='inventory')
    op.create_index('idx_stock_movements_reference', 'stock_movements', ['reference_type', 'reference_id'], schema='inventory')
    op.create_index('idx_stock_movements_created', 'stock_movements', ['created_at'], schema='inventory')

    # Unique constraint for SKU per tenant
    op.create_unique_constraint('uq_products_tenant_sku', 'products', ['tenant_id', 'sku'], schema='inventory')


def downgrade():
    op.drop_table('stock_movements', schema='inventory')
    op.drop_table('products', schema='inventory')
    op.execute("DROP SCHEMA IF EXISTS inventory CASCADE")