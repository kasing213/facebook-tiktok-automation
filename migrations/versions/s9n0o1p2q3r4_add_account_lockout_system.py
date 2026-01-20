"""Add account lockout system

Revision ID: s9n0o1p2q3r4
Revises: r8m9n0o1p2q3
Create Date: 2026-01-18 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 's9n0o1p2q3r4'
down_revision = 'r8m9n0o1p2q3'
branch_labels = None
depends_on = None


def upgrade():
    # Use raw SQL to avoid enum creation conflicts

    # Create enum if it doesn't exist
    op.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE loginatttemptresult AS ENUM ('success', 'failure');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))

    # Create login_attempt table if it doesn't exist
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS login_attempt (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) NOT NULL,
            ip_address VARCHAR(45) NOT NULL,
            user_agent TEXT,
            result loginatttemptresult NOT NULL,
            failure_reason VARCHAR(255),
            attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """))

    # Create indexes for login_attempt table
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_login_attempt_email ON login_attempt (email);"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_login_attempt_ip ON login_attempt (ip_address);"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_login_attempt_attempted_at ON login_attempt (attempted_at);"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_login_attempt_result ON login_attempt (result);"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_login_attempt_email_time ON login_attempt (email, attempted_at);"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_login_attempt_ip_time ON login_attempt (ip_address, attempted_at);"))

    # Create account_lockout table if it doesn't exist
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS account_lockout (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) NOT NULL,
            ip_address VARCHAR(45),
            lockout_reason VARCHAR(255) NOT NULL,
            failed_attempts_count INTEGER NOT NULL DEFAULT 0,
            locked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            unlock_at TIMESTAMPTZ NOT NULL,
            unlocked_at TIMESTAMPTZ,
            unlocked_by VARCHAR(255)
        );
    """))

    # Create indexes for account_lockout table
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_account_lockout_email ON account_lockout (email);"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_account_lockout_unlock_at ON account_lockout (unlock_at);"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_account_lockout_active ON account_lockout (email, unlocked_at);"))


def downgrade():
    # Drop indexes
    op.drop_index('idx_account_lockout_active', table_name='account_lockout')
    op.drop_index('idx_account_lockout_unlock_at', table_name='account_lockout')
    op.drop_index('idx_account_lockout_email', table_name='account_lockout')

    op.drop_index('idx_login_attempt_ip_time', table_name='login_attempt')
    op.drop_index('idx_login_attempt_email_time', table_name='login_attempt')
    op.drop_index('idx_login_attempt_result', table_name='login_attempt')
    op.drop_index('idx_login_attempt_attempted_at', table_name='login_attempt')
    op.drop_index('idx_login_attempt_ip', table_name='login_attempt')
    op.drop_index('idx_login_attempt_email', table_name='login_attempt')

    # Drop tables
    op.drop_table('account_lockout')
    op.drop_table('login_attempt')

    # Drop enum
    postgresql.ENUM('success', 'failure', name='loginatttemptresult').drop(op.get_bind())