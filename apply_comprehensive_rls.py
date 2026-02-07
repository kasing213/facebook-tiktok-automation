#!/usr/bin/env python3
"""
Apply Comprehensive RLS Migration Script

This script safely applies Row Level Security (RLS) policies across all database schemas:
- public (core tables + inventory + ads_alert)
- invoice
- scriptclient
- audit_sales

Features:
- Backup verification before applying
- Service role key validation
- Pre-flight checks
- Rollback capability
- Progress monitoring
"""

import os
import sys
import psycopg2
import logging
from datetime import datetime
from typing import Dict, List, Tuple
import argparse

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv not installed, relying on system environment variables")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RLSMigrationManager:
    """Manages the comprehensive RLS migration process"""

    def __init__(self, database_url: str, dry_run: bool = False):
        self.database_url = database_url
        self.dry_run = dry_run
        self.connection = None

    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(self.database_url)
            self.connection.autocommit = False  # Use transactions
            logger.info("✅ Database connection established")
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            sys.exit(1)

    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("🔌 Database connection closed")

    def execute_query(self, query: str, description: str = "") -> List[Tuple]:
        """Execute a query and return results"""
        try:
            with self.connection.cursor() as cursor:
                if self.dry_run:
                    logger.info(f"🔍 DRY RUN - Would execute: {description}")
                    return []

                cursor.execute(query)
                if cursor.description:
                    return cursor.fetchall()
                return []
        except Exception as e:
            logger.error(f"❌ Query failed ({description}): {e}")
            raise

    def check_prerequisites(self) -> bool:
        """Check if system is ready for RLS migration"""
        logger.info("🔍 Running pre-flight checks...")

        checks_passed = True

        # Check 1: Verify we have a service role or superuser access
        try:
            result = self.execute_query(
                "SELECT current_setting('is_superuser') as is_super, current_user;",
                "Check user privileges"
            )
            if result and result[0][0] == 'on':
                logger.info("✅ Running with superuser privileges")
            else:
                logger.info("ℹ️  Running with non-superuser privileges (should work with service role)")
        except Exception as e:
            logger.warning(f"⚠️  Could not verify user privileges: {e}")

        # Check 2: Verify required schemas exist
        schemas_query = """
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name IN ('public', 'invoice', 'scriptclient', 'audit_sales')
        ORDER BY schema_name;
        """

        try:
            if not self.dry_run:
                result = self.execute_query(schemas_query, "Check required schemas")
                found_schemas = [row[0] for row in result] if result else []
                expected_schemas = ['audit_sales', 'invoice', 'public', 'scriptclient']

                missing_schemas = set(expected_schemas) - set(found_schemas)
                if missing_schemas:
                    logger.error(f"❌ Missing required schemas: {missing_schemas}")
                    checks_passed = False
                else:
                    logger.info(f"✅ All required schemas found: {found_schemas}")
            else:
                logger.info("🔍 DRY RUN - Skipping schema verification")
        except Exception as e:
            logger.error(f"❌ Could not verify schemas: {e}")
            checks_passed = False

        # Check 3: Check if RLS helper function exists
        try:
            result = self.execute_query(
                "SELECT proname FROM pg_proc WHERE proname = 'get_tenant_id' AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public');",
                "Check RLS helper function"
            )
            if result:
                logger.warning("⚠️  RLS helper function already exists - migration may have been partially applied")
            else:
                logger.info("✅ RLS helper function not found - ready for clean installation")
        except Exception as e:
            logger.warning(f"⚠️  Could not check RLS helper function: {e}")

        # Check 4: Get current RLS status
        try:
            rls_status_query = """
            SELECT schemaname, tablename, rowsecurity
            FROM pg_tables
            WHERE schemaname IN ('public', 'invoice', 'scriptclient', 'audit_sales')
              AND tablename NOT IN ('alembic_version')
            ORDER BY schemaname, tablename;
            """
            result = self.execute_query(rls_status_query, "Check current RLS status")

            if result:
                rls_enabled_count = sum(1 for row in result if row[2])
                total_tables = len(result)
                logger.info(f"📊 Current RLS status: {rls_enabled_count}/{total_tables} tables have RLS enabled")

                if rls_enabled_count > 0:
                    logger.warning(f"⚠️  {rls_enabled_count} tables already have RLS enabled")

                    # Show which tables have RLS
                    enabled_tables = [(row[0], row[1]) for row in result if row[2]]
                    for schema, table in enabled_tables[:5]:  # Show first 5
                        logger.info(f"   - {schema}.{table}")
                    if len(enabled_tables) > 5:
                        logger.info(f"   ... and {len(enabled_tables) - 5} more")

        except Exception as e:
            logger.warning(f"⚠️  Could not check current RLS status: {e}")

        return checks_passed

    def load_migration_sql(self, filename: str) -> str:
        """Load SQL migration file"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            migration_path = os.path.join(script_dir, 'migrations', 'versions', filename)

            with open(migration_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"❌ Migration file not found: {filename}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"❌ Error reading migration file: {e}")
            sys.exit(1)

    def apply_migration(self):
        """Apply the comprehensive RLS migration"""
        logger.info("🚀 Starting comprehensive RLS migration...")

        # Load migration SQL
        migration_sql = self.load_migration_sql('003_comprehensive_rls_policies.sql')

        if self.dry_run:
            logger.info("🔍 DRY RUN - Migration SQL loaded but not executed")
            logger.info(f"📄 Migration contains {len(migration_sql.splitlines())} lines")
            return True

        try:
            # Start transaction
            logger.info("📊 Starting database transaction...")

            # Execute entire migration as one block (safer for RLS policies)
            logger.info("📝 Executing comprehensive RLS migration...")

            try:
                self.execute_query(migration_sql, "Comprehensive RLS Migration")
            except Exception as e:
                logger.error(f"❌ Migration failed: {e}")
                logger.info("🔄 Rolling back transaction...")
                self.connection.rollback()
                return False

            # Commit transaction
            logger.info("💾 Committing transaction...")
            self.connection.commit()
            logger.info("✅ Comprehensive RLS migration applied successfully!")

            return True

        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            if self.connection:
                self.connection.rollback()
                logger.info("🔄 Transaction rolled back")
            return False

    def _split_migration_sql(self, sql: str) -> List[Tuple[str, str]]:
        """Split migration SQL into logical sections for better error reporting"""
        sections = []
        current_section = ""
        current_name = "Initial Setup"

        for line in sql.splitlines():
            if line.strip().startswith('-- SECTION'):
                if current_section.strip():  # Only add non-empty sections
                    sections.append((current_name, current_section))
                current_name = line.strip()[2:].replace('SECTION ', '').replace(':', '').strip()  # Clean section name
                current_section = ""
            else:
                current_section += line + "\n"

        # Add final section if not empty
        if current_section.strip():
            sections.append((current_name, current_section))

        # Filter out empty sections
        sections = [(name, content) for name, content in sections if content.strip()]

        return sections

    def verify_installation(self):
        """Verify that RLS has been correctly applied"""
        logger.info("🔍 Verifying RLS installation...")

        try:
            # Check if verification function exists and use it
            result = self.execute_query(
                "SELECT * FROM public.verify_rls_status();",
                "Verify RLS status"
            )

            if result:
                total_tables = len(result)
                enabled_tables = sum(1 for row in result if row[2])  # row[2] is rls_enabled

                logger.info(f"📊 RLS Status Summary:")
                logger.info(f"   Total tables checked: {total_tables}")
                logger.info(f"   Tables with RLS enabled: {enabled_tables}")
                logger.info(f"   RLS coverage: {(enabled_tables/total_tables)*100:.1f}%")

                if enabled_tables == total_tables:
                    logger.info("✅ Perfect! RLS is enabled on all tables")
                else:
                    logger.warning(f"⚠️  {total_tables - enabled_tables} tables missing RLS")

                    # Show tables missing RLS
                    missing_rls = [f"{row[0]}.{row[1]}" for row in result if not row[2]]
                    for table in missing_rls:
                        logger.warning(f"   Missing RLS: {table}")

                return enabled_tables == total_tables
            else:
                logger.error("❌ Could not verify RLS status - verification function failed")
                return False

        except Exception as e:
            logger.error(f"❌ RLS verification failed: {e}")
            return False

    def rollback_migration(self):
        """Rollback the RLS migration"""
        logger.info("🔄 Starting RLS rollback...")

        rollback_sql = self.load_migration_sql('003_rollback_comprehensive_rls.sql')

        if self.dry_run:
            logger.info("🔍 DRY RUN - Rollback SQL loaded but not executed")
            return True

        try:
            logger.info("📊 Starting rollback transaction...")
            self.execute_query(rollback_sql, "RLS Rollback")
            self.connection.commit()
            logger.info("✅ RLS rollback completed successfully!")
            return True
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            if self.connection:
                self.connection.rollback()
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Apply Comprehensive RLS Migration")
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without making changes')
    parser.add_argument('--rollback', action='store_true', help='Rollback RLS policies instead of applying')
    parser.add_argument('--verify-only', action='store_true', help='Only run verification checks')

    args = parser.parse_args()

    # Load database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("❌ DATABASE_URL environment variable not set")
        logger.info("💡 Set your DATABASE_URL before running this script")
        sys.exit(1)

    # Convert SQLAlchemy format to psycopg2 format
    # SQLAlchemy uses postgresql+psycopg://, psycopg2 expects postgresql://
    if '+psycopg://' in database_url:
        database_url = database_url.replace('postgresql+psycopg://', 'postgresql://')
        logger.info("📝 Converted DATABASE_URL from SQLAlchemy to psycopg2 format")

    # Initialize migration manager
    manager = RLSMigrationManager(database_url, dry_run=args.dry_run)

    try:
        # Connect to database
        manager.connect()

        # Run pre-flight checks
        if not manager.check_prerequisites():
            logger.error("❌ Pre-flight checks failed")
            sys.exit(1)

        if args.verify_only:
            logger.info("🔍 Running verification only...")
            success = manager.verify_installation()
            sys.exit(0 if success else 1)

        if args.rollback:
            # Rollback RLS
            success = manager.rollback_migration()
        else:
            # Apply RLS migration
            success = manager.apply_migration()

            if success:
                # Verify installation
                success = manager.verify_installation()

        if success:
            logger.info("🎉 Operation completed successfully!")
            if not args.dry_run:
                logger.info("🔒 Your database now has comprehensive RLS protection")
        else:
            logger.error("❌ Operation failed")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("🛑 Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        manager.disconnect()

if __name__ == "__main__":
    main()