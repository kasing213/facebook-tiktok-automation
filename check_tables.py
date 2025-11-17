#!/usr/bin/env python3
"""Quick script to check if database tables exist"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Connecting to: {DATABASE_URL[:50]}...")

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check tables
    result = conn.execute(text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """))

    tables = [row[0] for row in result]

    print(f"\n✅ Found {len(tables)} tables in database:")
    for table in tables:
        print(f"  - {table}")

    # Check if our expected tables exist
    expected = ['tenant', 'user', 'ad_token', 'automation', 'automation_run', 'destination']
    missing = [t for t in expected if t not in tables]

    if missing:
        print(f"\n❌ Missing tables: {missing}")
    else:
        print(f"\n✅ All expected tables exist!")
