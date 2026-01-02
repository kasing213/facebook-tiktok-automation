"""
Verify data integrity after index fix
Checks for duplicates, NULL values, and proper token relationships
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
print("DATA INTEGRITY VERIFICATION")
print("=" * 80)

with engine.connect() as conn:
    # Check 1: Duplicates (should return 0)
    print("\n1. Checking for duplicate active user tokens...")
    result = conn.execute(text("""
        SELECT tenant_id, user_id, platform, COUNT(*) as count
        FROM ad_token
        WHERE deleted_at IS NULL AND token_type = 'user'
        GROUP BY tenant_id, user_id, platform
        HAVING COUNT(*) > 1;
    """))

    duplicates = result.fetchall()
    if duplicates:
        print(f"   [ERROR] Found {len(duplicates)} duplicate(s):")
        for dup in duplicates:
            print(f"   - tenant={dup[0]}, user={dup[1]}, platform={dup[2]}, count={dup[3]}")
    else:
        print("   [OK] No duplicates found!")

    # Check 2: NULL values in critical fields (should return 0)
    print("\n2. Checking for NULL values in critical fields...")
    result = conn.execute(text("""
        SELECT COUNT(*)
        FROM ad_token
        WHERE (tenant_id IS NULL OR user_id IS NULL OR platform IS NULL)
        AND deleted_at IS NULL;
    """))

    null_count = result.scalar()
    if null_count > 0:
        print(f"   [ERROR] Found {null_count} record(s) with NULL critical fields!")
    else:
        print("   [OK] No NULL values in critical fields!")

    # Check 3: User tokens have social_identity_id
    print("\n3. Checking user tokens have social_identity_id...")
    result = conn.execute(text("""
        SELECT COUNT(*)
        FROM ad_token
        WHERE token_type = 'user'
        AND deleted_at IS NULL
        AND social_identity_id IS NULL;
    """))

    missing_si = result.scalar()
    if missing_si > 0:
        print(f"   [WARNING] Found {missing_si} user token(s) without social_identity_id")
    else:
        print("   [OK] All user tokens have social_identity_id!")

    # Check 4: Page tokens have facebook_page_id
    print("\n4. Checking page tokens have facebook_page_id...")
    result = conn.execute(text("""
        SELECT COUNT(*)
        FROM ad_token
        WHERE token_type = 'page'
        AND deleted_at IS NULL
        AND facebook_page_id IS NULL;
    """))

    missing_fp = result.scalar()
    if missing_fp > 0:
        print(f"   [WARNING] Found {missing_fp} page token(s) without facebook_page_id")
    else:
        print("   [OK] All page tokens have facebook_page_id!")

    # Check 5: Token statistics
    print("\n5. Token statistics:")
    result = conn.execute(text("""
        SELECT
            token_type,
            platform,
            COUNT(*) as total_count,
            COUNT(DISTINCT tenant_id) as tenant_count,
            COUNT(DISTINCT user_id) as user_count
        FROM ad_token
        WHERE deleted_at IS NULL
        GROUP BY token_type, platform
        ORDER BY token_type, platform;
    """))

    stats = result.fetchall()
    if stats:
        print("\n   Active Tokens by Type:")
        print(f"   {'Type':<10} {'Platform':<10} {'Total':<10} {'Tenants':<10} {'Users':<10}")
        print("   " + "-" * 50)
        for stat in stats:
            print(f"   {stat[0]:<10} {stat[1]:<10} {stat[2]:<10} {stat[3]:<10} {stat[4]:<10}")
    else:
        print("   [INFO] No active tokens found")

    # Check 6: Soft-deleted tokens
    print("\n6. Soft-deleted tokens:")
    result = conn.execute(text("""
        SELECT
            token_type,
            COUNT(*) as deleted_count
        FROM ad_token
        WHERE deleted_at IS NOT NULL
        GROUP BY token_type
        ORDER BY token_type;
    """))

    deleted = result.fetchall()
    if deleted:
        print("\n   Soft-Deleted Tokens:")
        for del_stat in deleted:
            print(f"   - {del_stat[0]}: {del_stat[1]} token(s)")
    else:
        print("   [INFO] No soft-deleted tokens")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
