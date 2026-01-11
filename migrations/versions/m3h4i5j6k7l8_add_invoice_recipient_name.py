"""Add recipient_name field to invoice table

Revision ID: m3h4i5j6k7l8
Revises: l2g3h4i5j6k7
Create Date: 2026-01-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'm3h4i5j6k7l8'
down_revision = 'l2g3h4i5j6k7'
branch_labels = None
depends_on = None


def upgrade():
    """Add recipient_name column to invoice table for payment verification."""
    # Add recipient_name column - the name on the merchant's receiving bank account
    op.execute("""
        ALTER TABLE invoice.invoice
        ADD COLUMN IF NOT EXISTS recipient_name VARCHAR(100);
    """)

    # Add comment for documentation
    op.execute("""
        COMMENT ON COLUMN invoice.invoice.recipient_name IS
        'Name on the receiving bank account (merchant account holder name)';
    """)


def downgrade():
    """Remove recipient_name column."""
    op.execute("""
        ALTER TABLE invoice.invoice
        DROP COLUMN IF EXISTS recipient_name;
    """)
