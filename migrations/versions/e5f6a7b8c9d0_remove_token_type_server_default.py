"""remove_token_type_server_default

Fixes SQLAlchemy omitting token_type from INSERT statements.

When both server_default and client default exist, SQLAlchemy detects
the server_default and omits the column from INSERT statements, expecting
the database to fill it in. This causes all tokens to get token_type='user'
regardless of what we pass in Python code.

Removing server_default forces SQLAlchemy to include the column in INSERT,
while the Python default (TokenType.user) still provides a fallback.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2025-12-25 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Remove server_default from token_type column.

    This forces SQLAlchemy to include the column in INSERT statements
    with the value explicitly provided in Python code.
    """
    op.alter_column(
        'ad_token',
        'token_type',
        existing_type=sa.Enum('user', 'page', name='token_type_enum'),
        server_default=None,
        nullable=False
    )


def downgrade() -> None:
    """
    Restore server_default for rollback.

    This reverts to the previous behavior where SQLAlchemy omits
    the column from INSERT statements.
    """
    op.alter_column(
        'ad_token',
        'token_type',
        existing_type=sa.Enum('user', 'page', name='token_type_enum'),
        server_default='user',
        nullable=False
    )
