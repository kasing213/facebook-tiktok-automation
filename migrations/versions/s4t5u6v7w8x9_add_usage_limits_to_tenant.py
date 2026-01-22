"""Add usage limits to tenant table

Revision ID: s4t5u6v7w8x9
Revises:
Create Date: 2026-01-22 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 's4t5u6v7w8x9'
down_revision = 'v2w3x4y5z6a7'  # Current head revision
branch_labels = None
depends_on = None

def upgrade():
    """Add usage limit columns to tenant table"""

    # Usage limits (per tier)
    op.add_column('tenant', sa.Column('invoice_limit', sa.Integer(), nullable=False, server_default='50'))
    op.add_column('tenant', sa.Column('product_limit', sa.Integer(), nullable=False, server_default='100'))
    op.add_column('tenant', sa.Column('customer_limit', sa.Integer(), nullable=False, server_default='50'))
    op.add_column('tenant', sa.Column('team_member_limit', sa.Integer(), nullable=False, server_default='3'))
    op.add_column('tenant', sa.Column('storage_limit_mb', sa.Integer(), nullable=False, server_default='500'))
    op.add_column('tenant', sa.Column('api_calls_limit_hourly', sa.Integer(), nullable=False, server_default='100'))

    # Monthly usage counters (reset on 1st of month)
    op.add_column('tenant', sa.Column('current_month_invoices', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('tenant', sa.Column('current_month_exports', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('tenant', sa.Column('current_month_reset_at', sa.DateTime(timezone=True), nullable=True))

    # Storage tracking (cumulative, does not reset)
    op.add_column('tenant', sa.Column('storage_used_mb', sa.Numeric(10, 2), nullable=False, server_default='0'))

def downgrade():
    """Remove usage limit columns from tenant table"""

    # Remove storage tracking
    op.drop_column('tenant', 'storage_used_mb')

    # Remove monthly usage counters
    op.drop_column('tenant', 'current_month_reset_at')
    op.drop_column('tenant', 'current_month_exports')
    op.drop_column('tenant', 'current_month_invoices')

    # Remove usage limits
    op.drop_column('tenant', 'api_calls_limit_hourly')
    op.drop_column('tenant', 'storage_limit_mb')
    op.drop_column('tenant', 'team_member_limit')
    op.drop_column('tenant', 'customer_limit')
    op.drop_column('tenant', 'product_limit')
    op.drop_column('tenant', 'invoice_limit')