#!/usr/bin/env python3
"""
Create a demo tenant for testing OAuth flows.
Run this after starting the backend server.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import httpx


def create_demo_tenant():
    """Create a demo tenant via the API"""
    api_url = "http://localhost:8000"

    print("Creating demo tenant...")

    tenant_data = {
        "name": "Development Test Tenant",
        "slug": "dev-test-tenant",
        "admin_email": "admin@example.com",
        "admin_username": "dev_admin",
        "settings": {
            "description": "Demo tenant for development and testing"
        }
    }

    try:
        # Check if server is running
        response = httpx.get(f"{api_url}/health", timeout=5.0)
        if response.status_code != 200:
            print("❌ Backend server is not responding properly")
            return False

        print("✓ Backend server is running")

        # Create tenant
        response = httpx.post(
            f"{api_url}/api/tenants",
            json=tenant_data,
            timeout=10.0
        )

        if response.status_code == 200:
            tenant = response.json()
            print(f"\n✓ Demo tenant created successfully!")
            print(f"  ID: {tenant['id']}")
            print(f"  Name: {tenant['name']}")
            print(f"  Slug: {tenant['slug']}")
            print(f"\nYou can now use this tenant for OAuth testing.")
            return True
        elif response.status_code == 400:
            error_detail = response.json().get('detail', 'Unknown error')
            if 'already exists' in error_detail.lower() or 'duplicate' in error_detail.lower():
                print(f"\n⚠️  Tenant might already exist: {error_detail}")
                print("\nListing existing tenants...")
                list_tenants()
            else:
                print(f"\n❌ Failed to create tenant: {error_detail}")
            return False
        else:
            print(f"\n❌ Failed to create tenant: {response.text}")
            return False

    except httpx.ConnectError:
        print("\n❌ Cannot connect to backend server at http://localhost:8000")
        print("   Please start the backend server first:")
        print("   > uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def list_tenants():
    """List all existing tenants"""
    api_url = "http://localhost:8000"

    try:
        response = httpx.get(f"{api_url}/api/tenants", timeout=5.0)
        if response.status_code == 200:
            tenants = response.json()
            if tenants:
                print(f"\nExisting tenants ({len(tenants)}):")
                for tenant in tenants:
                    print(f"  - {tenant['name']} (ID: {tenant['id']}, Slug: {tenant['slug']})")
            else:
                print("\n⚠️  No tenants found in database")
            return True
        else:
            print(f"❌ Failed to list tenants: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error listing tenants: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("Demo Tenant Creator")
    print("=" * 50)
    print()

    success = create_demo_tenant()

    print()
    print("=" * 50)
    sys.exit(0 if success else 1)
