"""Add foreign key indexes for performance optimization

Revision ID: 05e3e980e152
Revises: 001
Create Date: 2025-09-27 13:09:36.099270

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05e3e980e152'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add indexes on foreign key columns for better query performance
    # Note: Some foreign keys already have composite indexes that serve similar purposes

    # Add index on ad_token.tenant_id (not covered by existing indexes)
    op.create_index('idx_ad_token_tenant', 'ad_token', ['tenant_id'], unique=False)

    # Add index on automation.destination_id (not covered by existing indexes)
    op.create_index('idx_automation_destination', 'automation', ['destination_id'], unique=False)

    # Add index on user.tenant_id (not covered by existing indexes)
    op.create_index('idx_user_tenant', 'user', ['tenant_id'], unique=False)

    # Note: Other foreign keys are already covered by composite indexes:
    # - automation.tenant_id is covered by idx_automation_tenant_status
    # - destination.tenant_id is covered by idx_destination_tenant_type
    # - automation_run.automation_id is covered by idx_automation_run_automation_status


def downgrade() -> None:
    # Drop the foreign key indexes
    op.drop_index('idx_user_tenant', table_name='user')
    op.drop_index('idx_automation_destination', table_name='automation')
    op.drop_index('idx_ad_token_tenant', table_name='ad_token')
