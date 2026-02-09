"""Add OCR verification audit trail table

Revision ID: 005_add_ocr_audit_trail
Revises: 004_add_tenant_to_security_tables
Create Date: 2026-02-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005_add_ocr_audit_trail'
down_revision: Union[str, None] = '004_add_tenant_to_security_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create OCR verification audit trail table
    op.create_table(
        'ocr_verification_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('screenshot_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=30), nullable=False),
        sa.Column('previous_status', sa.String(length=20), nullable=True),
        sa.Column('new_status', sa.String(length=20), nullable=False),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('verified_by_name', sa.String(length=255), nullable=True),
        sa.Column('verification_method', sa.String(length=50), nullable=True),
        sa.Column('ocr_response', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['public.tenant.id'], ),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoice.invoice.id'], ),
        sa.ForeignKeyConstraint(['verified_by'], ['public.user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='audit_sales'
    )

    # Create indexes for performance
    op.create_index('idx_ocr_log_tenant', 'ocr_verification_log', ['tenant_id'], schema='audit_sales')
    op.create_index('idx_ocr_log_invoice', 'ocr_verification_log', ['invoice_id'], schema='audit_sales')
    op.create_index('idx_ocr_log_created', 'ocr_verification_log', [sa.text('created_at DESC')], schema='audit_sales')
    op.create_index('idx_ocr_log_status', 'ocr_verification_log', ['action', 'new_status'], schema='audit_sales')


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_ocr_log_status', table_name='ocr_verification_log', schema='audit_sales')
    op.drop_index('idx_ocr_log_created', table_name='ocr_verification_log', schema='audit_sales')
    op.drop_index('idx_ocr_log_invoice', table_name='ocr_verification_log', schema='audit_sales')
    op.drop_index('idx_ocr_log_tenant', table_name='ocr_verification_log', schema='audit_sales')

    # Drop table
    op.drop_table('ocr_verification_log', schema='audit_sales')