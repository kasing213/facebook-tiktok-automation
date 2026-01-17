"""Add email verification token table

Revision ID: p6k7l8m9n0o1
Revises: o5j6k7l8m9n0
Create Date: 2026-01-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'p6k7l8m9n0o1'
down_revision = 'o5j6k7l8m9n0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create email verification token table
    op.create_table(
        'email_verification_token',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(64), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes
    op.create_index('idx_email_verification_token', 'email_verification_token', ['token'], unique=True)
    op.create_index('idx_email_verification_user', 'email_verification_token', ['user_id'])
    op.create_index('idx_email_verification_expires', 'email_verification_token', ['expires_at'])


def downgrade() -> None:
    op.drop_index('idx_email_verification_expires')
    op.drop_index('idx_email_verification_user')
    op.drop_index('idx_email_verification_token')
    op.drop_table('email_verification_token')
