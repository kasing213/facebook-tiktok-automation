#!/usr/bin/env python3
"""Script to create demo tenant for testing"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.core.db import SessionLocal
from app.services.tenant_service import TenantService

def main():
    db = SessionLocal()
    try:
        tenant_service = TenantService(db)

        # Check if demo-tenant already exists
        existing = tenant_service.get_tenant_by_slug("demo-tenant")
        if existing:
            print(f"✅ Demo tenant already exists!")
            print(f"   ID: {existing.id}")
            print(f"   Name: {existing.name}")
            print(f"   Slug: {existing.slug}")
            return

        # Create demo tenant
        print("Creating demo tenant...")
        tenant, admin = tenant_service.create_tenant_with_admin(
            name="Demo Organization",
            slug="demo-tenant",
            admin_email="admin@demo.com",
            admin_username="demo_admin",
            settings={}
        )

        print(f"✅ Demo tenant created successfully!")
        print(f"   ID: {tenant.id}")
        print(f"   Name: {tenant.name}")
        print(f"   Slug: {tenant.slug}")
        print(f"   Admin: {admin.username} ({admin.email})")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
