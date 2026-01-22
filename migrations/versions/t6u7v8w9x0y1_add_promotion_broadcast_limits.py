"""Add promotion and broadcast limits for anti-abuse

Revision ID: t6u7v8w9x0y1
Revises: s4t5u6v7w8x9
Create Date: 2026-01-22 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 't6u7v8w9x0y1'
down_revision = 's4t5u6v7w8x9'
branch_labels = None
depends_on = None

def upgrade():
    """Add promotion and broadcast limit columns to tenant table"""

    # Marketing/Promotion limits (anti-abuse for Telegram)
    op.add_column('tenant', sa.Column('promotion_limit', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('tenant', sa.Column('broadcast_recipient_limit', sa.Integer(), nullable=False, server_default='0'))

    # Monthly usage counters for promotions/broadcasts
    op.add_column('tenant', sa.Column('current_month_promotions', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('tenant', sa.Column('current_month_broadcasts', sa.Integer(), nullable=False, server_default='0'))

def downgrade():
    """Remove promotion and broadcast limit columns from tenant table"""

    # Remove monthly usage counters
    op.drop_column('tenant', 'current_month_broadcasts')
    op.drop_column('tenant', 'current_month_promotions')

    # Remove limits
    op.drop_column('tenant', 'broadcast_recipient_limit')
    op.drop_column('tenant', 'promotion_limit')