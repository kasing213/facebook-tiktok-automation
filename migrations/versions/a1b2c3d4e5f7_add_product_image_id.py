"""Add image_id column to inventory.products for MongoDB GridFS

Revision ID: a1b2c3d4e5f7
Revises: z1a2b3c4d5e6
Create Date: 2026-01-26 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f7'
down_revision = 'z1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    """Add image_id column to products table for MongoDB GridFS reference."""

    # Add image_id column to products table
    # Stores MongoDB GridFS ObjectId as string (24 hex characters)
    # Nullable because product images are optional
    op.add_column(
        'products',
        sa.Column('image_id', sa.String(255), nullable=True),
        schema='inventory'
    )

    # Add index for image_id lookups (e.g., when serving images)
    op.create_index(
        'idx_products_image_id',
        'products',
        ['image_id'],
        schema='inventory'
    )


def downgrade():
    """Remove image_id column from products table."""

    op.drop_index('idx_products_image_id', table_name='products', schema='inventory')
    op.drop_column('products', 'image_id', schema='inventory')
