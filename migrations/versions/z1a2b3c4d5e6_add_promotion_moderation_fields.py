"""Add moderation fields to AdsAlertPromotion

Revision ID: z1a2b3c4d5e6
Revises: y0z1a2b3c4d5
Create Date: 2026-01-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'z1a2b3c4d5e6'
down_revision = 'y0z1a2b3c4d5'
branch_labels = None
depends_on = None


def upgrade():
    """Add moderation fields to ads_alert.promotion table for content compliance."""

    # Create enum for moderation status
    moderation_status_enum = sa.Enum(
        'pending', 'approved', 'rejected', 'flagged', 'skipped',
        name='moderationstatus',
        schema='ads_alert'
    )
    moderation_status_enum.create(op.get_bind())

    # Add moderation columns to promotion table
    with op.batch_alter_table('promotion', schema='ads_alert') as batch_op:
        # Moderation workflow status
        batch_op.add_column(sa.Column(
            'moderation_status',
            moderation_status_enum,
            nullable=False,
            default='pending',
            comment='Content moderation status: pending review, approved, rejected, flagged for manual review'
        ))

        # Detailed moderation analysis result
        batch_op.add_column(sa.Column(
            'moderation_result',
            postgresql.JSON,
            nullable=True,
            comment='Detailed moderation analysis including violation types, confidence scores, extracted text'
        ))

        # Overall confidence score (0-100)
        batch_op.add_column(sa.Column(
            'moderation_score',
            sa.Float,
            nullable=True,
            comment='Moderation confidence score (0-100): higher scores indicate higher confidence in violation detection'
        ))

        # When moderation was performed
        batch_op.add_column(sa.Column(
            'moderated_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Timestamp when content moderation was performed'
        ))

        # Who performed manual moderation (if applicable)
        batch_op.add_column(sa.Column(
            'moderated_by',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment='User ID who performed manual moderation (admin/moderator)'
        ))

        # Human-readable rejection reason
        batch_op.add_column(sa.Column(
            'rejection_reason',
            sa.Text,
            nullable=True,
            comment='Human-readable explanation of why content was rejected or flagged'
        ))

        # Whether this promotion requires moderation
        batch_op.add_column(sa.Column(
            'requires_moderation',
            sa.Boolean,
            nullable=False,
            default=True,
            comment='Whether this promotion should go through moderation check before sending'
        ))

    # Add foreign key for moderated_by column
    op.create_foreign_key(
        'fk_promotion_moderated_by',
        'promotion', 'user',
        ['moderated_by'], ['id'],
        source_schema='ads_alert',
        ondelete='SET NULL'
    )

    # Add indexes for moderation queries
    op.create_index(
        'idx_promotion_moderation_status',
        'promotion',
        ['tenant_id', 'moderation_status'],
        schema='ads_alert'
    )

    op.create_index(
        'idx_promotion_moderation_pending',
        'promotion',
        ['tenant_id', 'moderated_at'],
        schema='ads_alert',
        postgresql_where=sa.text("moderation_status IN ('pending', 'flagged')")
    )

    op.create_index(
        'idx_promotion_moderation_score',
        'promotion',
        ['moderation_score'],
        schema='ads_alert',
        postgresql_where=sa.text("moderation_score IS NOT NULL")
    )


def downgrade():
    """Remove moderation fields from ads_alert.promotion table."""

    # Drop indexes
    op.drop_index('idx_promotion_moderation_score', table_name='promotion', schema='ads_alert')
    op.drop_index('idx_promotion_moderation_pending', table_name='promotion', schema='ads_alert')
    op.drop_index('idx_promotion_moderation_status', table_name='promotion', schema='ads_alert')

    # Drop foreign key
    op.drop_constraint('fk_promotion_moderated_by', 'promotion', schema='ads_alert', type_='foreignkey')

    # Remove columns from promotion table
    with op.batch_alter_table('promotion', schema='ads_alert') as batch_op:
        batch_op.drop_column('requires_moderation')
        batch_op.drop_column('rejection_reason')
        batch_op.drop_column('moderated_by')
        batch_op.drop_column('moderated_at')
        batch_op.drop_column('moderation_score')
        batch_op.drop_column('moderation_result')
        batch_op.drop_column('moderation_status')

    # Drop enum type
    sa.Enum(name='moderationstatus', schema='ads_alert').drop(op.get_bind())