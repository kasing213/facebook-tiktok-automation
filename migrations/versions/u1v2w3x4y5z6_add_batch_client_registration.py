"""Add batch client registration support

Revision ID: u1v2w3x4y5z6
Revises: t0u1v2w3x4y5
Create Date: 2026-01-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'u1v2w3x4y5z6'
down_revision: Union[str, None] = 't0u1v2w3x4y5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make customer_id nullable for batch codes (batch codes don't have a pre-existing customer)
    op.alter_column(
        'client_link_code',
        'customer_id',
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
        schema='invoice'
    )

    # Add batch-specific columns to client_link_code
    op.add_column(
        'client_link_code',
        sa.Column('is_batch', sa.Boolean(), nullable=False, server_default='false'),
        schema='invoice'
    )
    op.add_column(
        'client_link_code',
        sa.Column('batch_name', sa.String(length=100), nullable=True),
        schema='invoice'
    )
    op.add_column(
        'client_link_code',
        sa.Column('max_uses', sa.Integer(), nullable=True),
        schema='invoice'
    )
    op.add_column(
        'client_link_code',
        sa.Column('use_count', sa.Integer(), nullable=False, server_default='0'),
        schema='invoice'
    )

    # Index for batch code lookup (batch codes only - expiry checked at query time)
    op.execute("""
        CREATE INDEX idx_link_code_batch
        ON invoice.client_link_code (code, is_batch)
        WHERE is_batch = TRUE
    """)

    # Create tenant_client_sequence table for auto-generated client IDs
    op.create_table(
        'tenant_client_sequence',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('current_sequence', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('prefix', sa.String(length=20), nullable=False, server_default="'Client'"),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['public.tenant.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['merchant_id'], ['public.user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'merchant_id', name='uq_tenant_merchant_sequence'),
        schema='invoice'
    )

    # Index for fast sequence lookup
    op.create_index(
        'idx_tenant_client_sequence_lookup',
        'tenant_client_sequence',
        ['tenant_id', 'merchant_id'],
        schema='invoice'
    )


def downgrade() -> None:
    # Drop sequence table
    op.drop_index('idx_tenant_client_sequence_lookup', table_name='tenant_client_sequence', schema='invoice')
    op.drop_table('tenant_client_sequence', schema='invoice')

    # Drop batch index
    op.execute('DROP INDEX IF EXISTS invoice.idx_link_code_batch')

    # Drop batch columns from client_link_code
    op.drop_column('client_link_code', 'use_count', schema='invoice')
    op.drop_column('client_link_code', 'max_uses', schema='invoice')
    op.drop_column('client_link_code', 'batch_name', schema='invoice')
    op.drop_column('client_link_code', 'is_batch', schema='invoice')

    # Make customer_id required again
    op.alter_column(
        'client_link_code',
        'customer_id',
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
        schema='invoice'
    )
