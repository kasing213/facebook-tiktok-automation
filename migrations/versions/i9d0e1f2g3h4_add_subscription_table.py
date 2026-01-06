"""Add subscription table for Stripe integration

Revision ID: i9d0e1f2g3h4
Revises: h8c9d0e1f2g3
Create Date: 2026-01-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'i9d0e1f2g3h4'
down_revision: Union[str, None] = 'h8c9d0e1f2g3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create subscription tier enum
    subscription_tier = postgresql.ENUM('free', 'pro', name='subscriptiontier', create_type=False)
    subscription_tier.create(op.get_bind(), checkfirst=True)

    # Create subscription status enum
    subscription_status = postgresql.ENUM('active', 'cancelled', 'past_due', 'incomplete', name='subscriptionstatus', create_type=False)
    subscription_status.create(op.get_bind(), checkfirst=True)

    # Create subscription table
    op.create_table(
        'subscription',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
        sa.Column('tier', postgresql.ENUM('free', 'pro', name='subscriptiontier', create_type=False), nullable=False, server_default='free'),
        sa.Column('status', postgresql.ENUM('active', 'cancelled', 'past_due', 'incomplete', name='subscriptionstatus', create_type=False), nullable=True),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_subscription_user'),
        sa.UniqueConstraint('stripe_customer_id', name='uq_subscription_stripe_customer'),
        sa.UniqueConstraint('stripe_subscription_id', name='uq_subscription_stripe_sub')
    )

    # Create indexes
    op.create_index('idx_subscription_user', 'subscription', ['user_id'], unique=True)
    op.create_index('idx_subscription_tenant', 'subscription', ['tenant_id'])
    op.create_index('idx_subscription_stripe_customer', 'subscription', ['stripe_customer_id'])
    op.create_index('idx_subscription_stripe_sub', 'subscription', ['stripe_subscription_id'])
    op.create_index('idx_subscription_tier', 'subscription', ['tier'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_subscription_tier', table_name='subscription')
    op.drop_index('idx_subscription_stripe_sub', table_name='subscription')
    op.drop_index('idx_subscription_stripe_customer', table_name='subscription')
    op.drop_index('idx_subscription_tenant', table_name='subscription')
    op.drop_index('idx_subscription_user', table_name='subscription')

    # Drop table
    op.drop_table('subscription')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS subscriptionstatus')
    op.execute('DROP TYPE IF EXISTS subscriptiontier')
