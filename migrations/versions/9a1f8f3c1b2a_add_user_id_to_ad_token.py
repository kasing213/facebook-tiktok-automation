"""add_user_id_to_ad_token

Revision ID: 9a1f8f3c1b2a
Revises: 7cfa2d9130ca
Create Date: 2025-02-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "9a1f8f3c1b2a"
down_revision: Union[str, None] = "7cfa2d9130ca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ad_token", sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_ad_token_user", "ad_token", "user", ["user_id"], ["id"])
    op.drop_constraint("uq_token_tenant_platform_account", "ad_token", type_="unique")
    op.create_unique_constraint(
        "uq_token_tenant_user_platform_account",
        "ad_token",
        ["tenant_id", "user_id", "platform", "account_ref"]
    )
    op.create_index("idx_ad_token_user", "ad_token", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_ad_token_user", table_name="ad_token")
    op.drop_constraint("uq_token_tenant_user_platform_account", "ad_token", type_="unique")
    op.create_unique_constraint(
        "uq_token_tenant_platform_account",
        "ad_token",
        ["tenant_id", "platform", "account_ref"]
    )
    op.drop_constraint("fk_ad_token_user", "ad_token", type_="foreignkey")
    op.drop_column("ad_token", "user_id")
