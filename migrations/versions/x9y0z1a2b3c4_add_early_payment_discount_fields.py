"""Add early payment discount fields to invoice table

Revision ID: o5j6k7l8m9n0
Revises: n4i5j6k7l8m9
Create Date: 2026-01-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'x9y0z1a2b3c4'
down_revision = 'w8x9y0z1a2b3'
branch_labels = None
depends_on = None


def upgrade():
    """Add early payment discount fields to invoice table."""
    op.execute("""
        ALTER TABLE invoice.invoice
        ADD COLUMN IF NOT EXISTS early_payment_enabled BOOLEAN DEFAULT FALSE NOT NULL,
        ADD COLUMN IF NOT EXISTS early_payment_discount_percentage NUMERIC(5,2) DEFAULT 10.00,
        ADD COLUMN IF NOT EXISTS early_payment_deadline DATE,
        ADD COLUMN IF NOT EXISTS original_amount NUMERIC(12,2),
        ADD COLUMN IF NOT EXISTS discount_amount NUMERIC(12,2) DEFAULT 0.00,
        ADD COLUMN IF NOT EXISTS final_amount NUMERIC(12,2),
        ADD COLUMN IF NOT EXISTS pro_reward_granted BOOLEAN DEFAULT FALSE NOT NULL,
        ADD COLUMN IF NOT EXISTS pro_reward_granted_at TIMESTAMPTZ;
    """)

    # Add comments for documentation
    op.execute("""
        COMMENT ON COLUMN invoice.invoice.early_payment_enabled IS
        'Whether early payment discount is available for this invoice';

        COMMENT ON COLUMN invoice.invoice.early_payment_discount_percentage IS
        'Discount percentage for early payment (default 10%)';

        COMMENT ON COLUMN invoice.invoice.early_payment_deadline IS
        'Deadline to qualify for early payment discount';

        COMMENT ON COLUMN invoice.invoice.original_amount IS
        'Original invoice amount before discount';

        COMMENT ON COLUMN invoice.invoice.discount_amount IS
        'Discount amount applied for early payment';

        COMMENT ON COLUMN invoice.invoice.final_amount IS
        'Final amount after discount applied';

        COMMENT ON COLUMN invoice.invoice.pro_reward_granted IS
        'Whether free Pro month reward was granted';

        COMMENT ON COLUMN invoice.invoice.pro_reward_granted_at IS
        'When the Pro reward was granted';
    """)

    # Update existing invoices to populate original_amount and final_amount
    op.execute("""
        UPDATE invoice.invoice
        SET original_amount = amount,
            final_amount = amount
        WHERE original_amount IS NULL;
    """)


def downgrade():
    """Remove early payment discount fields."""
    op.execute("""
        ALTER TABLE invoice.invoice
        DROP COLUMN IF EXISTS early_payment_enabled,
        DROP COLUMN IF EXISTS early_payment_discount_percentage,
        DROP COLUMN IF EXISTS early_payment_deadline,
        DROP COLUMN IF EXISTS original_amount,
        DROP COLUMN IF EXISTS discount_amount,
        DROP COLUMN IF EXISTS final_amount,
        DROP COLUMN IF EXISTS pro_reward_granted,
        DROP COLUMN IF EXISTS pro_reward_granted_at;
    """)