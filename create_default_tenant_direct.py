"""
Create a default tenant directly in the database
This is needed for user registration to work
"""
import os
from sqlalchemy import create_engine, text

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ DATABASE_URL environment variable not set")
    print("Please set it to your Railway PostgreSQL connection string")
    exit(1)

# Create engine
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        # Check if tenant exists
        result = conn.execute(text("SELECT id, name, slug FROM tenant LIMIT 1"))
        tenant = result.fetchone()

        if tenant:
            print(f"✅ Default tenant already exists:")
            print(f"   ID: {tenant[0]}")
            print(f"   Name: {tenant[1]}")
            print(f"   Slug: {tenant[2]}")
        else:
            # Create default tenant
            result = conn.execute(text("""
                INSERT INTO tenant (name, slug, is_active, created_at, updated_at)
                VALUES ('Default Organization', 'default', true, NOW(), NOW())
                RETURNING id, name, slug
            """))
            conn.commit()
            tenant = result.fetchone()
            print(f"✅ Created default tenant:")
            print(f"   ID: {tenant[0]}")
            print(f"   Name: {tenant[1]}")
            print(f"   Slug: {tenant[2]}")

except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

print("\n✅ Done! You can now register users.")
