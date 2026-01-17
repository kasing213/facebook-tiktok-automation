"""Add password reset token table

Revision ID: r8m9n0o1p2q3
Revises: q7l8m9n0o1p2
Create Date: 2026-01-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'r8m9n0o1p2q3'
down_revision = 'q7l8m9n0o1p2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create password reset token table
    op.create_table(
        'password_reset_token',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(64), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes
    op.create_index('idx_password_reset_token', 'password_reset_token', ['token'], unique=True)
    op.create_index('idx_password_reset_user', 'password_reset_token', ['user_id'])
    op.create_index('idx_password_reset_expires', 'password_reset_token', ['expires_at'])


def downgrade() -> None:
    op.drop_index('idx_password_reset_expires')
    op.drop_index('idx_password_reset_user')
    op.drop_index('idx_password_reset_token')
    op.drop_table('password_reset_token')
