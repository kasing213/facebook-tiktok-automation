"""Add email_verified_at to user table

Revision ID: q7l8m9n0o1p2
Revises: p6k7l8m9n0o1
Create Date: 2026-01-15
"""
from alembic import op
import sqlalchemy as sa


revision = 'q7l8m9n0o1p2'
down_revision = 'p6k7l8m9n0o1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add email_verified_at column to user table
    op.add_column('user', sa.Column('email_verified_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove email_verified_at column from user table
    op.drop_column('user', 'email_verified_at')