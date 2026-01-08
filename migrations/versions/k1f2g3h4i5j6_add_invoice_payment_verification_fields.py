"""Add payment verification fields to invoice table

Revision ID: k1f2g3h4i5j6
Revises: j0e1f2g3h4i5
Create Date: 2026-01-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'k1f2g3h4i5j6'
down_revision: Union[str, None] = 'j0e1f2g3h4i5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add payment verification fields to invoice.invoice table
    op.add_column('invoice', sa.Column('bank', sa.String(length=100), nullable=True), schema='invoice')
    op.add_column('invoice', sa.Column('expected_account', sa.String(length=100), nullable=True), schema='invoice')
    op.add_column('invoice', sa.Column('currency', sa.String(length=10), nullable=False, server_default='KHR'), schema='invoice')
    op.add_column('invoice', sa.Column('verification_status', sa.String(length=20), nullable=False, server_default='pending'), schema='invoice')
    op.add_column('invoice', sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True), schema='invoice')
    op.add_column('invoice', sa.Column('verified_by', sa.String(length=100), nullable=True), schema='invoice')
    op.add_column('invoice', sa.Column('verification_note', sa.Text(), nullable=True), schema='invoice')

    # Add index on verification_status for filtering
    op.create_index('idx_invoice_verification_status', 'invoice', ['verification_status'], schema='invoice')


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_invoice_verification_status', table_name='invoice', schema='invoice')

    # Drop columns
    op.drop_column('invoice', 'verification_note', schema='invoice')
    op.drop_column('invoice', 'verified_by', schema='invoice')
    op.drop_column('invoice', 'verified_at', schema='invoice')
    op.drop_column('invoice', 'verification_status', schema='invoice')
    op.drop_column('invoice', 'currency', schema='invoice')
    op.drop_column('invoice', 'expected_account', schema='invoice')
    op.drop_column('invoice', 'bank', schema='invoice')
