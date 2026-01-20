#!/usr/bin/env python3
"""
Verify that account lockout tables were created successfully.
"""
import os
import sys
from sqlalchemy import create_engine, text

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ DATABASE_URL environment variable not set")
    print("   Please set it to your PostgreSQL connection string")
    sys.exit(1)

def verify_tables():
    print("🔍 Verifying Account Lockout Database Tables")
    print("=" * 50)

    try:
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            # Check if enum exists
            result = conn.execute(text(
                "SELECT 1 FROM pg_type WHERE typname = 'loginatttemptresult'"
            ))
            if result.fetchone():
                print("✅ Enum 'loginatttemptresult' exists")
            else:
                print("❌ Enum 'loginatttemptresult' NOT found")

            # Check if login_attempt table exists
            result = conn.execute(text(
                "SELECT 1 FROM information_schema.tables WHERE table_name = 'login_attempt'"
            ))
            if result.fetchone():
                print("✅ Table 'login_attempt' exists")

                # Check table structure
                result = conn.execute(text(
                    "SELECT column_name, data_type FROM information_schema.columns "
                    "WHERE table_name = 'login_attempt' ORDER BY ordinal_position"
                ))
                columns = result.fetchall()
                print("   Columns:", [f"{col[0]} ({col[1]})" for col in columns])
            else:
                print("❌ Table 'login_attempt' NOT found")

            # Check if account_lockout table exists
            result = conn.execute(text(
                "SELECT 1 FROM information_schema.tables WHERE table_name = 'account_lockout'"
            ))
            if result.fetchone():
                print("✅ Table 'account_lockout' exists")

                # Check table structure
                result = conn.execute(text(
                    "SELECT column_name, data_type FROM information_schema.columns "
                    "WHERE table_name = 'account_lockout' ORDER BY ordinal_position"
                ))
                columns = result.fetchall()
                print("   Columns:", [f"{col[0]} ({col[1]})" for col in columns])
            else:
                print("❌ Table 'account_lockout' NOT found")

            # Check indexes
            result = conn.execute(text(
                "SELECT indexname FROM pg_indexes "
                "WHERE tablename IN ('login_attempt', 'account_lockout') "
                "ORDER BY tablename, indexname"
            ))
            indexes = result.fetchall()
            print(f"✅ Found {len(indexes)} indexes:")
            for idx in indexes:
                print(f"   - {idx[0]}")

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

    print()
    print("✅ Database verification completed!")
    return True

if __name__ == "__main__":
    verify_tables()