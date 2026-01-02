"""
Verify that the idx_ad_token_one_active_user_token index was created correctly
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine
engine = create_engine(DATABASE_URL)

print("=" * 80)
print("VERIFYING INDEX: idx_ad_token_one_active_user_token")
print("=" * 80)

with engine.connect() as conn:
    # Query to get index definition
    result = conn.execute(text("""
        SELECT
            indexname,
            indexdef
        FROM pg_indexes
        WHERE tablename = 'ad_token'
        AND indexname = 'idx_ad_token_one_active_user_token';
    """))

    row = result.fetchone()

    if row:
        print(f"\n[OK] Index found!")
        print(f"\nIndex Name: {row[0]}")
        print(f"\nIndex Definition:")
        print(f"{row[1]}")

        # Check if it has tenant_id
        if 'tenant_id' in row[1]:
            print(f"\n[OK] Index includes tenant_id - CORRECT!")
        else:
            print(f"\n[ERROR] Index missing tenant_id - INCORRECT!")

        # Check if it has the WHERE clause
        if 'WHERE' in row[1] and "deleted_at IS NULL" in row[1] and "token_type = 'user'" in row[1]:
            print(f"[OK] Partial index condition is correct!")
        else:
            print(f"[ERROR] Partial index condition is missing or incorrect!")
    else:
        print("\n[ERROR] Index NOT found!")

print("\n" + "=" * 80)
