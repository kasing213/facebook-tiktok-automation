#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply RLS (Row Level Security) migration to Supabase database

This script applies the RLS policies to ensure proper tenant isolation.
Run this ONLY when you're ready to enable RLS on your database.

Usage:
    python apply_rls_migration.py

Requirements:
    - DATABASE_URL environment variable set
    - Or Supabase credentials in .env file
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load environment variables
load_dotenv()

def get_database_url():
    """Get database URL from environment"""
    # Try direct DATABASE_URL first
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url

    # Try constructing from Supabase vars
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if supabase_url:
        # Extract project ref from Supabase URL
        # Format: https://<project-ref>.supabase.co
        project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")
        db_password = os.getenv("SUPABASE_DB_PASSWORD", "")

        if db_password:
            return f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"

    return None

def apply_migration():
    """Apply the RLS migration"""
    db_url = get_database_url()

    if not db_url:
        print("❌ ERROR: Could not find database connection details.")
        print("Please set one of the following:")
        print("  - DATABASE_URL")
        print("  - SUPABASE_URL + SUPABASE_DB_PASSWORD")
        sys.exit(1)

    # Read the migration file
    migration_file = Path(__file__).parent / "migrations" / "versions" / "002_enable_rls_policies.sql"

    if not migration_file.exists():
        print(f"❌ ERROR: Migration file not found: {migration_file}")
        sys.exit(1)

    print(f"📖 Reading migration from: {migration_file}")
    migration_sql = migration_file.read_text()

    # Confirm before applying
    print("\n" + "="*80)
    print("⚠️  WARNING: This will enable Row Level Security on all tables!")
    print("="*80)
    print("\nThis migration will:")
    print("  ✓ Enable RLS on: tenant, user, ad_token, destination, automation, automation_run")
    print("  ✓ Create tenant isolation policies")
    print("  ✓ Restrict data access to current tenant only")
    print("\nIMPORTANT:")
    print("  - Your backend API must use service_role key to bypass RLS")
    print("  - Test thoroughly in development before production!")
    print("  - Backup your database before proceeding!")
    print("\n" + "="*80)

    response = input("\nDo you want to continue? (yes/no): ").strip().lower()

    if response != "yes":
        print("❌ Migration cancelled.")
        sys.exit(0)

    # Connect and apply migration
    try:
        print("\n🔌 Connecting to database...")
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cursor = conn.cursor()

        print("🚀 Applying RLS migration...")
        cursor.execute(migration_sql)

        conn.commit()
        print("✅ RLS migration applied successfully!")

        # Verify RLS is enabled
        print("\n🔍 Verifying RLS status...")
        cursor.execute("""
            SELECT
                schemaname,
                tablename,
                rowsecurity
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename IN ('tenant', 'user', 'ad_token', 'destination', 'automation', 'automation_run')
            ORDER BY tablename;
        """)

        results = cursor.fetchall()
        print("\nRLS Status:")
        print("-" * 60)
        for schema, table, rls_enabled in results:
            status = "✅ ENABLED" if rls_enabled else "❌ DISABLED"
            print(f"  {table:25} {status}")

        cursor.close()
        conn.close()

        print("\n" + "="*80)
        print("✅ SUCCESS: RLS is now enabled on your database!")
        print("="*80)
        print("\nNext steps:")
        print("  1. Test your API endpoints to ensure they still work")
        print("  2. Verify tenant isolation is working correctly")
        print("  3. Check Supabase dashboard for any security warnings")
        print("\nNote: Your backend should use the service_role key for database operations.")

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"\n❌ ERROR applying migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    apply_migration()
