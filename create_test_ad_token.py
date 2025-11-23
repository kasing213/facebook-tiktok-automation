#!/usr/bin/env python3
"""
Create a test AdToken in the database for development/testing
This bypasses the OAuth flow when you can't get permissions approved
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_async_session_context
from app.core.models import AdToken, Platform
from app.core.crypto import load_encryptor
from app.core.config import get_settings

async def create_test_ad_token():
    """Create a test Facebook ad token for development"""
    settings = get_settings()
    encryptor = load_encryptor(settings.MASTER_SECRET_KEY.get_secret_value())

    # Get tenant ID (you'll need to replace this with your actual tenant ID)
    tenant_id = input("Enter tenant_id (UUID from database): ").strip()
    if not tenant_id:
        print("❌ Tenant ID is required")
        return

    # Token details
    platform = input("Platform (facebook/tiktok) [facebook]: ").strip() or "facebook"
    account_ref = input("Account reference (e.g., act_123456789): ").strip() or "act_test_123456789"
    account_name = input("Account name: ").strip() or "Test Ad Account"

    # For testing, use a fake token (won't work for real API calls but will test the database)
    access_token = input("Access token (leave empty for fake token): ").strip() or "TEST_TOKEN_" + uuid.uuid4().hex

    print(f"\n📝 Creating test ad token:")
    print(f"  Tenant ID: {tenant_id}")
    print(f"  Platform: {platform}")
    print(f"  Account Ref: {account_ref}")
    print(f"  Account Name: {account_name}")
    print(f"  Token: {access_token[:20]}...")

    confirm = input("\nProceed? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Cancelled")
        return

    try:
        async with get_async_session_context() as session:
            # Encrypt token
            encrypted_token = encryptor.encrypt(access_token.encode()).decode()

            # Create AdToken
            ad_token = AdToken(
                id=uuid.uuid4(),
                tenant_id=uuid.UUID(tenant_id),
                platform=Platform[platform],
                account_ref=account_ref,
                account_name=account_name,
                access_token_enc=encrypted_token,
                refresh_token_enc=None,
                scope="public_profile,email,pages_show_list",
                expires_at=datetime.utcnow() + timedelta(days=60),
                is_valid=True,
                last_validated=datetime.utcnow(),
                meta={"source": "manual_test_creation"}
            )

            session.add(ad_token)
            await session.commit()
            await session.refresh(ad_token)

            print(f"\n✅ Test ad token created successfully!")
            print(f"   Token ID: {ad_token.id}")
            print(f"   Expires: {ad_token.expires_at}")
            print(f"\n💡 You can now test your application with this token")
            print(f"   Note: This is a test token and won't work with real Facebook API calls")

    except Exception as e:
        print(f"\n❌ Error creating test token: {e}")
        import traceback
        traceback.print_exc()

async def list_tenants():
    """List all tenants to help find tenant_id"""
    try:
        async with get_async_session_context() as session:
            from sqlalchemy import select
            from app.core.models import Tenant

            result = await session.execute(select(Tenant))
            tenants = result.scalars().all()

            if not tenants:
                print("❌ No tenants found in database")
                print("💡 Create a tenant first using create_demo_tenant.py")
                return

            print("\n📋 Available Tenants:")
            for tenant in tenants:
                print(f"  • {tenant.name}")
                print(f"    ID: {tenant.id}")
                print(f"    Slug: {tenant.slug}")
                print(f"    Active: {tenant.is_active}")
                print()

    except Exception as e:
        print(f"❌ Error listing tenants: {e}")

async def main():
    """Main entry point"""
    print("=" * 60)
    print("  Test AdToken Creator")
    print("=" * 60)
    print()

    # First, list tenants
    await list_tenants()

    print("\n" + "=" * 60)
    print()

    # Then create token
    await create_test_ad_token()

if __name__ == "__main__":
    asyncio.run(main())
