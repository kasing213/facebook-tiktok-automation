"""fix_user_token_unique_index

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2025-12-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the old incorrect index (missing tenant_id)
    op.drop_index('idx_ad_token_one_active_user_token', table_name='ad_token')

    # Create the corrected partial unique index with tenant_id included
    # This ensures proper multi-tenant isolation
    op.create_index(
        'idx_ad_token_one_active_user_token',
        'ad_token',
        ['tenant_id', 'user_id', 'platform'],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND token_type = 'user'")
    )


def downgrade() -> None:
    # Drop the corrected index
    op.drop_index('idx_ad_token_one_active_user_token', table_name='ad_token')

    # Recreate the old (incorrect) index for rollback compatibility
    op.create_index(
        'idx_ad_token_one_active_user_token',
        'ad_token',
        ['user_id', 'platform'],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND token_type = 'user'")
    )
