"""add_rls_policies_social_identity

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2025-12-24 00:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable RLS on social_identity table
    op.execute("ALTER TABLE social_identity ENABLE ROW LEVEL SECURITY")

    # Create RLS policies for social_identity
    op.execute("""
        CREATE POLICY social_identity_select_policy ON social_identity
          FOR SELECT
          USING (tenant_id = public.get_tenant_id())
    """)

    op.execute("""
        CREATE POLICY social_identity_insert_policy ON social_identity
          FOR INSERT
          WITH CHECK (tenant_id = public.get_tenant_id())
    """)

    op.execute("""
        CREATE POLICY social_identity_update_policy ON social_identity
          FOR UPDATE
          USING (tenant_id = public.get_tenant_id())
          WITH CHECK (tenant_id = public.get_tenant_id())
    """)

    op.execute("""
        CREATE POLICY social_identity_delete_policy ON social_identity
          FOR DELETE
          USING (tenant_id = public.get_tenant_id())
    """)

    # Enable RLS on facebook_page table
    op.execute("ALTER TABLE facebook_page ENABLE ROW LEVEL SECURITY")

    # Create RLS policies for facebook_page (via social_identity join)
    op.execute("""
        CREATE POLICY facebook_page_select_policy ON facebook_page
          FOR SELECT
          USING (
            social_identity_id IN (
              SELECT id FROM social_identity WHERE tenant_id = public.get_tenant_id()
            )
          )
    """)

    op.execute("""
        CREATE POLICY facebook_page_insert_policy ON facebook_page
          FOR INSERT
          WITH CHECK (
            social_identity_id IN (
              SELECT id FROM social_identity WHERE tenant_id = public.get_tenant_id()
            )
          )
    """)

    op.execute("""
        CREATE POLICY facebook_page_update_policy ON facebook_page
          FOR UPDATE
          USING (
            social_identity_id IN (
              SELECT id FROM social_identity WHERE tenant_id = public.get_tenant_id()
            )
          )
          WITH CHECK (
            social_identity_id IN (
              SELECT id FROM social_identity WHERE tenant_id = public.get_tenant_id()
            )
          )
    """)

    op.execute("""
        CREATE POLICY facebook_page_delete_policy ON facebook_page
          FOR DELETE
          USING (
            social_identity_id IN (
              SELECT id FROM social_identity WHERE tenant_id = public.get_tenant_id()
            )
          )
    """)


def downgrade() -> None:
    # Drop facebook_page policies
    op.execute("DROP POLICY IF EXISTS facebook_page_delete_policy ON facebook_page")
    op.execute("DROP POLICY IF EXISTS facebook_page_update_policy ON facebook_page")
    op.execute("DROP POLICY IF EXISTS facebook_page_insert_policy ON facebook_page")
    op.execute("DROP POLICY IF EXISTS facebook_page_select_policy ON facebook_page")
    op.execute("ALTER TABLE facebook_page DISABLE ROW LEVEL SECURITY")

    # Drop social_identity policies
    op.execute("DROP POLICY IF EXISTS social_identity_delete_policy ON social_identity")
    op.execute("DROP POLICY IF EXISTS social_identity_update_policy ON social_identity")
    op.execute("DROP POLICY IF EXISTS social_identity_insert_policy ON social_identity")
    op.execute("DROP POLICY IF EXISTS social_identity_select_policy ON social_identity")
    op.execute("ALTER TABLE social_identity DISABLE ROW LEVEL SECURITY")
