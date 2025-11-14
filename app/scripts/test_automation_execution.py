#!/usr/bin/env python3
"""
Example script to test automation execution.

This script demonstrates how to:
1. Create an automation
2. Execute it manually
3. View the results
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.core.db import get_db
from app.core.models import AutomationType, Platform
from app.services.automation_service import AutomationService
from app.repositories.tenant import TenantRepository
from app.repositories.destination import DestinationRepository


async def create_test_automation(db: Session):
    """Create a test automation for demonstration"""

    # Get first available tenant
    tenant_repo = TenantRepository(db)
    tenants = tenant_repo.find_by(is_active=True)

    if not tenants:
        print("❌ No active tenants found. Please create a tenant first.")
        return None

    tenant = tenants[0]
    print(f"✅ Using tenant: {tenant.name} ({tenant.id})")

    # Get or create a destination
    dest_repo = DestinationRepository(db)
    destinations = dest_repo.get_active_destinations(tenant.id)

    if not destinations:
        # Create a test webhook destination
        print("📝 Creating test webhook destination...")
        destination = dest_repo.create_webhook_destination(
            tenant_id=tenant.id,
            name="Test Webhook",
            webhook_url="https://webhook.site/unique-id",  # Replace with your webhook.site URL
            headers={"Content-Type": "application/json"}
        )
        db.commit()
        print(f"✅ Created destination: {destination.name} ({destination.id})")
    else:
        destination = destinations[0]
        print(f"✅ Using destination: {destination.name} ({destination.id})")

    # Create automation
    automation_service = AutomationService(db)

    print("\n📊 Creating scheduled report automation...")
    automation = automation_service.create_automation(
        tenant_id=tenant.id,
        destination_id=destination.id,
        name="Daily Facebook Report",
        automation_type=AutomationType.scheduled_report,
        schedule_config={
            "type": "daily",
            "hour": 9  # Run at 9 AM UTC
        },
        automation_config={
            "period": "daily",
            "days": 7,
            "metric_types": ["ad_account", "pages"],
            "format": "text"
        },
        platforms=["facebook"]
    )

    print(f"✅ Created automation: {automation.name} ({automation.id})")
    print(f"   Type: {automation.type.value}")
    print(f"   Status: {automation.status.value}")
    print(f"   Next run: {automation.next_run}")

    return automation


async def execute_automation(db: Session, automation_id: UUID):
    """Execute an automation and display results"""

    automation_service = AutomationService(db)

    print(f"\n🚀 Executing automation {automation_id}...")
    print("=" * 60)

    try:
        run = await automation_service.execute_automation(automation_id)

        print(f"✅ Automation executed successfully!")
        print(f"   Run ID: {run.id}")
        print(f"   Status: {run.status}")
        print(f"   Started: {run.started_at}")
        print(f"   Completed: {run.completed_at}")

        if run.result:
            print("\n📊 Result:")
            print(f"   Status: {run.result.get('status', 'N/A')}")

            # Display logs if available
            logs = run.result.get("logs", [])
            if logs:
                print(f"\n📝 Execution Logs ({len(logs)} entries):")
                for log in logs[:10]:  # Show first 10 logs
                    print(f"   [{log['level'].upper()}] {log['message']}")

            # Display delivery result
            delivery = run.result.get("delivery")
            if delivery:
                print(f"\n📬 Delivery Result:")
                print(f"   Success: {delivery.get('success', False)}")
                if delivery.get('success'):
                    print(f"   Destination Type: {delivery.get('destination_type', 'N/A')}")
                else:
                    print(f"   Error: {delivery.get('error', 'N/A')}")

            # Display formatted output
            formatted_output = run.result.get("formatted_output", "")
            if formatted_output:
                print(f"\n📄 Formatted Output (first 500 chars):")
                print("-" * 60)
                print(formatted_output[:500])
                if len(formatted_output) > 500:
                    print("... (truncated)")
                print("-" * 60)

        if run.error_message:
            print(f"\n❌ Error: {run.error_message}")

    except Exception as e:
        print(f"❌ Error executing automation: {str(e)}")
        import traceback
        traceback.print_exc()


async def view_automation_history(db: Session, automation_id: UUID):
    """View execution history for an automation"""

    automation_service = AutomationService(db)

    print(f"\n📜 Viewing execution history for {automation_id}...")
    print("=" * 60)

    history = automation_service.get_automation_history(automation_id, limit=10)

    if not history:
        print("No execution history found.")
        return

    print(f"Found {len(history)} recent executions:\n")

    for i, run in enumerate(history, 1):
        print(f"{i}. Run {run.id}")
        print(f"   Started: {run.started_at}")
        print(f"   Status: {run.status}")
        if run.completed_at:
            duration = (run.completed_at - run.started_at).total_seconds()
            print(f"   Duration: {duration:.2f}s")
        if run.error_message:
            print(f"   Error: {run.error_message[:100]}")
        print()


async def main():
    """Main function"""

    print("🤖 Automation Execution Test Script")
    print("=" * 60)

    # Get database session
    db = next(get_db())

    try:
        # Step 1: Create test automation (or use existing)
        print("\n📋 Step 1: Create/Find Test Automation")
        print("-" * 60)

        # Uncomment to create a new automation
        # automation = await create_test_automation(db)
        # if not automation:
        #     return

        # Or use an existing automation ID
        automation_id_str = input("\nEnter automation ID to test (or press Enter to create new): ").strip()

        if automation_id_str:
            automation_id = UUID(automation_id_str)
        else:
            automation = await create_test_automation(db)
            if not automation:
                return
            automation_id = automation.id

        # Step 2: Execute the automation
        print("\n📋 Step 2: Execute Automation")
        print("-" * 60)
        await execute_automation(db, automation_id)

        # Step 3: View execution history
        print("\n📋 Step 3: View Execution History")
        print("-" * 60)
        await view_automation_history(db, automation_id)

        print("\n✅ Test completed successfully!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
