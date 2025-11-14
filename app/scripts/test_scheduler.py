#!/usr/bin/env python3
"""
Test script for the automation scheduler.

This script creates a test automation and verifies that the scheduler
executes it correctly.
"""
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.db import get_db_session
from app.core.models import AutomationType, AutomationStatus, DestinationType
from app.services.automation_service import AutomationService
from app.repositories import TenantRepository, DestinationRepository
from app.jobs.automation_scheduler import AutomationScheduler


async def create_test_automation():
    """Create a test automation for scheduler testing"""
    print("🔧 Setting up test automation...")

    with get_db_session() as db:
        tenant_repo = TenantRepository(db)
        dest_repo = DestinationRepository(db)
        automation_service = AutomationService(db)

        # Get or create test tenant
        tenant = tenant_repo.get_by_slug("test-tenant")
        if not tenant:
            print("❌ Test tenant not found. Create one first using create_demo_tenant.py")
            return None

        print(f"✅ Using tenant: {tenant.name} (ID: {tenant.id})")

        # Get or create a test destination (Telegram or webhook)
        destinations = dest_repo.get_tenant_destinations(tenant.id)
        if not destinations:
            print("📝 Creating test destination...")
            destination = dest_repo.create_destination(
                tenant_id=tenant.id,
                name="Test Telegram Channel",
                destination_type=DestinationType.telegram_chat,
                config={
                    "chat_id": "test_chat_123",
                    "parse_mode": "Markdown"
                }
            )
            db.commit()
        else:
            destination = destinations[0]

        print(f"✅ Using destination: {destination.name} (Type: {destination.type.value})")

        # Create a scheduled report automation that runs every 2 minutes
        automation = automation_service.create_automation(
            tenant_id=tenant.id,
            destination_id=destination.id,
            name="Test Scheduled Report (2-min interval)",
            automation_type=AutomationType.scheduled_report,
            schedule_config={
                "type": "interval",
                "interval_minutes": 2  # Run every 2 minutes
            },
            automation_config={
                "period": "daily",
                "days": 7,
                "metric_types": ["ad_account"],
                "format": "text"
            },
            platforms=["facebook"]
        )

        print(f"✅ Created automation: {automation.name}")
        print(f"   ID: {automation.id}")
        print(f"   Type: {automation.type.value}")
        print(f"   Status: {automation.status.value}")
        print(f"   Next run: {automation.next_run}")

        return automation


async def test_scheduler_manual():
    """Manually test the scheduler by running it once"""
    print("\n🧪 Testing automation scheduler manually...\n")

    scheduler = AutomationScheduler(check_interval=30)

    # Run one check cycle
    print("🔍 Checking for due automations...")
    await scheduler.check_and_execute_automations()

    print("\n✅ Manual scheduler test completed")


async def test_scheduler_loop():
    """Test the scheduler in a continuous loop for a few minutes"""
    print("\n🔄 Running scheduler in loop mode (will run for 5 minutes)...\n")

    scheduler = AutomationScheduler(check_interval=30)

    # Run scheduler for 5 minutes
    try:
        task = asyncio.create_task(scheduler.run_scheduler())

        # Wait for 5 minutes
        await asyncio.sleep(300)

        # Stop the scheduler
        scheduler.stop()
        await task

    except asyncio.CancelledError:
        pass

    print("\n✅ Loop scheduler test completed")


async def main():
    """Main test function"""
    print("=" * 60)
    print("Automation Scheduler Test")
    print("=" * 60)

    # Step 1: Create test automation
    automation = await create_test_automation()
    if not automation:
        return

    print("\n" + "=" * 60)
    print("Choose a test mode:")
    print("1. Manual test (run scheduler once)")
    print("2. Loop test (run scheduler for 5 minutes)")
    print("3. Skip testing (just setup)")
    print("=" * 60)

    choice = input("\nEnter your choice (1-3): ").strip()

    if choice == "1":
        await test_scheduler_manual()
    elif choice == "2":
        await test_scheduler_loop()
    elif choice == "3":
        print("✅ Setup completed. Automation created successfully.")
    else:
        print("❌ Invalid choice")

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
    print("\nℹ️  To view automation execution logs, start the FastAPI server:")
    print("   uvicorn app.main:app --reload")
    print("\nℹ️  Check automation runs in the database:")
    print("   SELECT * FROM automation_run WHERE automation_id = '<automation_id>';")


if __name__ == "__main__":
    asyncio.run(main())
