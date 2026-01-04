"""Add telegram user linking

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-01-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'g7b8c9d0e1f2'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add telegram_username and telegram_linked_at columns to user table
    op.add_column('user', sa.Column('telegram_username', sa.String(length=100), nullable=True))
    op.add_column('user', sa.Column('telegram_linked_at', sa.DateTime(timezone=True), nullable=True))

    # Create telegram_link_code table for temporary linking codes
    op.create_table('telegram_link_code',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('telegram_user_id', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_telegram_link_code_code')
    )

    # Create indexes for telegram_link_code
    op.create_index('idx_telegram_link_code_code', 'telegram_link_code', ['code'], unique=True)
    op.create_index('idx_telegram_link_code_expires', 'telegram_link_code', ['expires_at'], unique=False)
    op.create_index('idx_telegram_link_code_user', 'telegram_link_code', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_telegram_link_code_user', table_name='telegram_link_code')
    op.drop_index('idx_telegram_link_code_expires', table_name='telegram_link_code')
    op.drop_index('idx_telegram_link_code_code', table_name='telegram_link_code')

    # Drop table
    op.drop_table('telegram_link_code')

    # Drop columns from user table
    op.drop_column('user', 'telegram_linked_at')
    op.drop_column('user', 'telegram_username')
