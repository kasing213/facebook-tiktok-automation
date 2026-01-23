"""Add subscription trial fields

Revision ID: w8x9y0z1a2b3
Revises: t6u7v8w9x0y1
Create Date: 2026-01-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'w8x9y0z1a2b3'
down_revision: Union[str, None] = 't6u7v8w9x0y1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add trial period fields to subscription table."""
    # Add is_trial column (default False for existing subscriptions)
    op.add_column(
        'subscription',
        sa.Column('is_trial', sa.Boolean(), nullable=False, server_default='false')
    )

    # Add trial_ends_at column (nullable - only set for trial subscriptions)
    op.add_column(
        'subscription',
        sa.Column('trial_ends_at', sa.DateTime(timezone=True), nullable=True)
    )

    # Add index for efficient trial expiration checks
    op.create_index(
        'idx_subscription_trial_ends',
        'subscription',
        ['trial_ends_at'],
        unique=False
    )


def downgrade() -> None:
    """Remove trial period fields from subscription table."""
    op.drop_index('idx_subscription_trial_ends', table_name='subscription')
    op.drop_column('subscription', 'trial_ends_at')
    op.drop_column('subscription', 'is_trial')
