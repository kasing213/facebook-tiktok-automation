"""Link ads_alert.chat to invoice.customer for customer targeting

Revision ID: v2w3x4y5z6a7
Revises: u1v2w3x4y5z6
Create Date: 2026-01-20 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'v2w3x4y5z6a7'
down_revision: Union[str, None] = 'u1v2w3x4y5z6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add customer_id to ads_alert.chat to link with invoice.customer
    # This enables merchants to target invoice customers with promotions
    op.add_column(
        'chat',
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        schema='ads_alert'
    )

    # Add foreign key constraint with CASCADE delete
    # When a customer is deleted, their ads_alert.chat record is also deleted
    op.create_foreign_key(
        'fk_ads_alert_chat_customer',
        'chat', 'customer',
        ['customer_id'], ['id'],
        source_schema='ads_alert',
        referent_schema='invoice',
        ondelete='CASCADE'
    )

    # Create index for efficient customer lookups
    op.create_index(
        'idx_ads_alert_chat_customer',
        'chat',
        ['customer_id', 'tenant_id'],
        schema='ads_alert'
    )

    # Add customer targeting fields to promotion table
    # target_customer_type: 'none' (use chat targeting), 'all_customers', 'selected_customers'
    op.add_column(
        'promotion',
        sa.Column('target_customer_type', sa.String(length=20), nullable=False, server_default='none'),
        schema='ads_alert'
    )

    # Array of invoice.customer IDs for 'selected_customers' targeting
    op.add_column(
        'promotion',
        sa.Column('target_customer_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True, server_default=sa.text("'{}'::uuid[]")),
        schema='ads_alert'
    )

    # Index for promotions that target customers (for efficient queries)
    op.execute("""
        CREATE INDEX idx_ads_alert_promotion_customer_targeting
        ON ads_alert.promotion (target_customer_type)
        WHERE target_customer_type != 'none'
    """)


def downgrade() -> None:
    # Drop customer targeting index
    op.execute('DROP INDEX IF EXISTS ads_alert.idx_ads_alert_promotion_customer_targeting')

    # Drop customer targeting columns from promotion
    op.drop_column('promotion', 'target_customer_ids', schema='ads_alert')
    op.drop_column('promotion', 'target_customer_type', schema='ads_alert')

    # Drop customer_id index
    op.drop_index('idx_ads_alert_chat_customer', table_name='chat', schema='ads_alert')

    # Drop foreign key constraint
    op.drop_constraint('fk_ads_alert_chat_customer', 'chat', schema='ads_alert', type_='foreignkey')

    # Drop customer_id column from chat
    op.drop_column('chat', 'customer_id', schema='ads_alert')
