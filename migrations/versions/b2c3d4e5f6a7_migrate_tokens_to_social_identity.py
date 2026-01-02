"""migrate_tokens_to_social_identity

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2025-12-24 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Add new columns to ad_token (all nullable first)
    op.add_column('ad_token', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('ad_token', sa.Column('social_identity_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('ad_token', sa.Column('facebook_page_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Create token_type enum if it doesn't exist
    op.execute("CREATE TYPE token_type_enum AS ENUM ('user', 'page')")
    op.add_column('ad_token', sa.Column('token_type', sa.Enum('user', 'page', name='token_type_enum'), nullable=False, server_default='user'))

    # Step 2: Delete all tokens with NULL user_id (clean slate - testing data)
    op.execute("DELETE FROM ad_token WHERE user_id IS NULL")

    # Step 3: Extract and create social identities from existing tokens
    # For user tokens (not page tokens)
    # Use DISTINCT ON to avoid issues with JSON equality in DISTINCT
    op.execute("""
        INSERT INTO social_identity (tenant_id, user_id, platform, platform_user_id, facebook_user_id, display_name, email, profile_data, created_at, updated_at)
        SELECT DISTINCT ON (tenant_id, user_id, platform)
            at.tenant_id,
            at.user_id,
            at.platform,
            at.account_ref,
            CASE
                WHEN at.platform = 'facebook' AND at.meta->'user' IS NOT NULL AND at.meta->'user'->>'id' IS NOT NULL
                THEN at.meta->'user'->>'id'
                ELSE NULL
            END as facebook_user_id,
            at.account_name,
            CASE
                WHEN at.meta->'user' IS NOT NULL AND at.meta->'user'->>'email' IS NOT NULL
                THEN at.meta->'user'->>'email'
                ELSE NULL
            END as email,
            CASE
                WHEN at.meta->'user' IS NOT NULL
                THEN at.meta->'user'
                ELSE NULL
            END as profile_data,
            at.created_at,
            at.updated_at
        FROM ad_token at
        WHERE at.user_id IS NOT NULL
          AND at.account_ref IS NOT NULL
          AND at.account_ref NOT LIKE 'page_%'
          AND at.deleted_at IS NULL
        ORDER BY tenant_id, user_id, platform, at.updated_at DESC
        ON CONFLICT (platform, platform_user_id) DO NOTHING
    """)

    # Step 4: Create Facebook page entries from page tokens
    # Use DISTINCT ON to avoid issues with JSON equality in DISTINCT
    op.execute("""
        INSERT INTO facebook_page (social_identity_id, page_id, name, category, tasks, page_data, created_at, updated_at)
        SELECT DISTINCT ON (REPLACE(at.account_ref, 'page_', ''))
            si.id,
            REPLACE(at.account_ref, 'page_', ''),
            at.account_name,
            CASE
                WHEN at.meta->>'category' IS NOT NULL
                THEN at.meta->>'category'
                ELSE NULL
            END as category,
            CASE
                WHEN at.meta->'tasks' IS NOT NULL
                THEN ARRAY(SELECT json_array_elements_text(at.meta->'tasks'))
                ELSE NULL
            END as tasks,
            at.meta,
            at.created_at,
            at.updated_at
        FROM ad_token at
        JOIN social_identity si ON si.tenant_id = at.tenant_id
                                AND si.user_id = at.user_id
                                AND si.platform = 'facebook'
        WHERE at.account_ref LIKE 'page_%'
          AND at.platform = 'facebook'
          AND at.deleted_at IS NULL
        ORDER BY REPLACE(at.account_ref, 'page_', ''), at.updated_at DESC
        ON CONFLICT (page_id) DO NOTHING
    """)

    # Step 5: Link ad_tokens to social_identity (for user tokens)
    op.execute("""
        UPDATE ad_token at
        SET social_identity_id = si.id
        FROM social_identity si
        WHERE at.tenant_id = si.tenant_id
          AND at.user_id = si.user_id
          AND at.platform = si.platform
          AND at.account_ref = si.platform_user_id
          AND at.account_ref NOT LIKE 'page_%'
          AND at.deleted_at IS NULL
    """)

    # Link ad_tokens to facebook_page (for page tokens)
    op.execute("""
        UPDATE ad_token at
        SET facebook_page_id = fp.id,
            token_type = 'page',
            social_identity_id = fp.social_identity_id
        FROM facebook_page fp
        JOIN social_identity si ON fp.social_identity_id = si.id
        WHERE at.tenant_id = si.tenant_id
          AND at.user_id = si.user_id
          AND at.platform = 'facebook'
          AND at.account_ref = 'page_' || fp.page_id
          AND at.deleted_at IS NULL
    """)

    # Step 6: Make user_id NOT NULL (all NULL values should be deleted by now)
    op.alter_column('ad_token', 'user_id', nullable=False)

    # Step 7: Add foreign keys
    op.create_foreign_key('fk_ad_token_social_identity', 'ad_token', 'social_identity',
                         ['social_identity_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_ad_token_facebook_page', 'ad_token', 'facebook_page',
                         ['facebook_page_id'], ['id'], ondelete='CASCADE')

    # Step 8: Create indexes
    op.create_index('idx_ad_token_social_identity', 'ad_token', ['social_identity_id'])
    op.create_index('idx_ad_token_facebook_page', 'ad_token', ['facebook_page_id'])
    op.create_index('idx_ad_token_deleted', 'ad_token', ['deleted_at'],
                    postgresql_where=sa.text('deleted_at IS NULL'))

    # Step 9: Enforce one active user token per user/platform (page tokens can be multiple)
    op.create_index(
        'idx_ad_token_one_active_user_token',
        'ad_token',
        ['user_id', 'platform'],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND token_type = 'user'")
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_ad_token_one_active_user_token', table_name='ad_token')
    op.drop_index('idx_ad_token_deleted', table_name='ad_token')
    op.drop_index('idx_ad_token_facebook_page', table_name='ad_token')
    op.drop_index('idx_ad_token_social_identity', table_name='ad_token')

    # Drop foreign keys
    op.drop_constraint('fk_ad_token_facebook_page', 'ad_token', type_='foreignkey')
    op.drop_constraint('fk_ad_token_social_identity', 'ad_token', type_='foreignkey')

    # Make user_id nullable again
    op.alter_column('ad_token', 'user_id', nullable=True)

    # Drop columns
    op.drop_column('ad_token', 'token_type')
    op.execute("DROP TYPE token_type_enum")
    op.drop_column('ad_token', 'facebook_page_id')
    op.drop_column('ad_token', 'social_identity_id')
    op.drop_column('ad_token', 'deleted_at')
