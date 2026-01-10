"""Add due_date field to invoice table

Revision ID: n4i5j6k7l8m9
Revises: m3h4i5j6k7l8
Create Date: 2026-01-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'n4i5j6k7l8m9'
down_revision = 'm3h4i5j6k7l8'
branch_labels = None
depends_on = None


def upgrade():
    """Add due_date column to invoice table."""
    op.execute("""
        ALTER TABLE invoice.invoice
        ADD COLUMN IF NOT EXISTS due_date DATE;
    """)

    op.execute("""
        COMMENT ON COLUMN invoice.invoice.due_date IS
        'Invoice due date for payment';
    """)


def downgrade():
    """Remove due_date column."""
    op.execute("""
        ALTER TABLE invoice.invoice
        DROP COLUMN IF EXISTS due_date;
    """)
