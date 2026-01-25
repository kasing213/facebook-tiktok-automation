"""Add tenant isolation security indexes

Revision ID: y0z1a2b3c4d5
Revises: x9y0z1a2b3c4
Create Date: 2026-01-25 14:30:00.000000

This migration adds database indexes to support the tenant isolation security fixes
implemented in the application code. These indexes ensure optimal performance for
tenant-filtered queries and provide database-level security enforcement.

Security Changes:
- Adds compound indexes for efficient tenant-filtered lookups
- Improves query performance for tenant isolation checks
- Adds partial indexes for verification status filtering
- Creates covering indexes for critical payment verification queries

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'y0z1a2b3c4d5'
down_revision = 'x9y0z1a2b3c4'
branch_labels = None
depends_on = None


def upgrade():
    """Add tenant isolation security indexes."""

    # ========================================
    # INVOICE SCHEMA SECURITY INDEXES
    # ========================================

    # 1. Critical: Invoice lookup by tenant + ID (most common query)
    op.create_index(
        'idx_invoice_tenant_id_lookup',
        'invoice',
        ['tenant_id', 'id'],
        schema='invoice',
        unique=False,
        postgresql_include=['verification_status', 'status', 'amount']
    )

    # 2. Critical: Invoice lookup by tenant + number (OCR verification)
    op.create_index(
        'idx_invoice_tenant_number_lookup',
        'invoice',
        ['tenant_id', 'invoice_number'],
        schema='invoice',
        unique=False,
        postgresql_include=['verification_status', 'status', 'bank', 'expected_account']
    )

    # 3. Performance: Pending invoices by tenant (client payment selection)
    op.create_index(
        'idx_invoice_tenant_pending_verification',
        'invoice',
        ['tenant_id', 'customer_id'],
        schema='invoice',
        unique=False,
        postgresql_where="verification_status IN ('pending', 'rejected')"
    )

    # 4. Performance: Early payment queries by tenant
    op.create_index(
        'idx_invoice_tenant_early_payment',
        'invoice',
        ['tenant_id', 'early_payment_enabled'],
        schema='invoice',
        unique=False,
        postgresql_where="early_payment_enabled = true",
        postgresql_include=['early_payment_deadline', 'early_payment_discount_percentage']
    )

    # 5. Security: Ensure invoice numbers are unique per tenant
    op.create_index(
        'idx_invoice_tenant_number_unique',
        'invoice',
        ['tenant_id', 'invoice_number'],
        schema='invoice',
        unique=True
    )

    # ========================================
    # CUSTOMER SCHEMA SECURITY INDEXES
    # ========================================

    # 6. Customer lookup by tenant (for invoice creation)
    op.create_index(
        'idx_customer_tenant_lookup',
        'customer',
        ['tenant_id', 'id'],
        schema='invoice',
        unique=False,
        postgresql_include=['name', 'email']
    )

    # 7. Customer search by tenant + name (dashboard search)
    # Note: Using BTREE instead of GIN since UUID doesn't support GIN operator class
    op.create_index(
        'idx_customer_tenant_name_search',
        'customer',
        ['tenant_id', 'name'],
        schema='invoice',
        unique=False,
        postgresql_using='btree'
    )

    # ========================================
    # INVENTORY SCHEMA SECURITY INDEXES
    # ========================================

    # 8. Product lookup by tenant (invoice line items)
    op.create_index(
        'idx_inventory_products_tenant_lookup',
        'products',
        ['tenant_id', 'is_active'],
        schema='inventory',
        unique=False,
        postgresql_include=['name', 'sku', 'unit_price', 'current_stock']
    )

    # 9. Stock movements by tenant + product (audit trail)
    op.create_index(
        'idx_inventory_movements_tenant_product',
        'stock_movements',
        ['tenant_id', 'product_id', 'created_at'],
        schema='inventory',
        unique=False
    )

    # 10. Low stock alerts by tenant (telegram notifications)
    op.create_index(
        'idx_inventory_products_low_stock',
        'products',
        ['tenant_id'],
        schema='inventory',
        unique=False,
        postgresql_where="track_stock = true AND current_stock <= low_stock_threshold",
        postgresql_include=['name', 'sku', 'current_stock', 'low_stock_threshold']
    )

    # ========================================
    # CORE SCHEMA SECURITY INDEXES
    # ========================================

    # 11. User lookup by tenant (authorization checks)
    op.create_index(
        'idx_user_tenant_lookup',
        'user',
        ['tenant_id', 'is_active'],
        schema='public',
        unique=False,
        postgresql_include=['role', 'email', 'telegram_user_id']
    )

    # 12. Tenant subscription lookup (feature gating)
    op.create_index(
        'idx_subscription_tenant_lookup',
        'subscription',
        ['tenant_id'],
        schema='public',
        unique=True,
        postgresql_include=['tier', 'status', 'trial_ends_at']
    )


def downgrade():
    """Remove tenant isolation security indexes."""

    # Remove all indexes in reverse order
    op.drop_index('idx_subscription_tenant_lookup', table_name='subscription', schema='public')
    op.drop_index('idx_user_tenant_lookup', table_name='user', schema='public')
    op.drop_index('idx_inventory_products_low_stock', table_name='products', schema='inventory')
    op.drop_index('idx_inventory_movements_tenant_product', table_name='stock_movements', schema='inventory')
    op.drop_index('idx_inventory_products_tenant_lookup', table_name='products', schema='inventory')
    op.drop_index('idx_customer_tenant_name_search', table_name='customer', schema='invoice')
    op.drop_index('idx_customer_tenant_lookup', table_name='customer', schema='invoice')
    op.drop_index('idx_invoice_tenant_number_unique', table_name='invoice', schema='invoice')
    op.drop_index('idx_invoice_tenant_early_payment', table_name='invoice', schema='invoice')
    op.drop_index('idx_invoice_tenant_pending_verification', table_name='invoice', schema='invoice')
    op.drop_index('idx_invoice_tenant_number_lookup', table_name='invoice', schema='invoice')
    op.drop_index('idx_invoice_tenant_id_lookup', table_name='invoice', schema='invoice')