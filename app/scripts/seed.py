"""
Database seeding script for development and testing.

This script populates the database with sample data including tenants,
users, destinations, and automations for development and testing purposes.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.db import async_session_maker
from app.core.models import Tenant, User, Destination, Automation, AdToken
from app.core.security import get_password_hash


async def create_demo_tenant(session: AsyncSession) -> Tenant:
    """
    Create a demo tenant.

    Args:
        session: Database session

    Returns:
        Created tenant
    """
    tenant = Tenant(
        id=uuid4(),
        name="Demo Company",
        slug="demo-company",
        is_active=True,
        settings={
            "theme": "dark",
            "notifications_enabled": True,
            "timezone": "America/New_York"
        }
    )
    session.add(tenant)
    await session.commit()
    await session.refresh(tenant)
    logger.info(f"Created demo tenant: {tenant.name} ({tenant.id})")
    return tenant


async def create_demo_users(session: AsyncSession, tenant: Tenant) -> list[User]:
    """
    Create demo users for the tenant.

    Args:
        session: Database session
        tenant: Parent tenant

    Returns:
        List of created users
    """
    users = [
        User(
            id=uuid4(),
            tenant_id=tenant.id,
            username="admin",
            email="admin@demo.com",
            password_hash=get_password_hash("password123"),
            role="admin",
            is_active=True,
            email_verified=True,
            profile_data={"full_name": "Admin User"}
        ),
        User(
            id=uuid4(),
            tenant_id=tenant.id,
            username="user1",
            email="user1@demo.com",
            password_hash=get_password_hash("password123"),
            role="user",
            is_active=True,
            email_verified=True,
            profile_data={"full_name": "John Doe"}
        ),
        User(
            id=uuid4(),
            tenant_id=tenant.id,
            username="viewer",
            email="viewer@demo.com",
            password_hash=get_password_hash("password123"),
            role="viewer",
            is_active=True,
            email_verified=True,
            profile_data={"full_name": "Jane Viewer"}
        )
    ]

    for user in users:
        session.add(user)

    await session.commit()

    for user in users:
        await session.refresh(user)
        logger.info(f"Created user: {user.username} ({user.role})")

    return users


async def create_demo_destinations(session: AsyncSession, tenant: Tenant) -> list[Destination]:
    """
    Create demo destinations for the tenant.

    Args:
        session: Database session
        tenant: Parent tenant

    Returns:
        List of created destinations
    """
    destinations = [
        Destination(
            id=uuid4(),
            tenant_id=tenant.id,
            name="Telegram Notifications",
            type="telegram_chat",
            config={
                "chat_id": "-1001234567890",
                "parse_mode": "HTML"
            },
            is_active=True
        ),
        Destination(
            id=uuid4(),
            tenant_id=tenant.id,
            name="Webhook Endpoint",
            type="webhook",
            config={
                "url": "https://example.com/webhook",
                "method": "POST",
                "headers": {"Content-Type": "application/json"}
            },
            is_active=True
        ),
        Destination(
            id=uuid4(),
            tenant_id=tenant.id,
            name="Email Reports",
            type="email",
            config={
                "recipients": ["reports@demo.com"],
                "subject_template": "Daily Report - {date}"
            },
            is_active=False
        )
    ]

    for dest in destinations:
        session.add(dest)

    await session.commit()

    for dest in destinations:
        await session.refresh(dest)
        logger.info(f"Created destination: {dest.name} ({dest.type})")

    return destinations


async def create_demo_automations(
    session: AsyncSession,
    tenant: Tenant,
    destinations: list[Destination]
) -> list[Automation]:
    """
    Create demo automations for the tenant.

    Args:
        session: Database session
        tenant: Parent tenant
        destinations: Available destinations

    Returns:
        List of created automations
    """
    now = datetime.utcnow()

    automations = [
        Automation(
            id=uuid4(),
            tenant_id=tenant.id,
            destination_id=destinations[0].id,
            name="Daily Facebook Report",
            type="scheduled_report",
            status="active",
            schedule_config={
                "type": "cron",
                "cron": "0 9 * * *",  # 9 AM daily
                "timezone": "America/New_York"
            },
            automation_config={
                "report_type": "summary",
                "metrics": ["impressions", "clicks", "spend", "ctr"],
                "include_charts": True
            },
            platforms=["facebook"],
            next_run=now + timedelta(hours=1),
            run_count=0,
            error_count=0
        ),
        Automation(
            id=uuid4(),
            tenant_id=tenant.id,
            destination_id=destinations[1].id,
            name="TikTok Performance Alert",
            type="alert",
            status="active",
            schedule_config={
                "type": "interval",
                "interval_minutes": 60
            },
            automation_config={
                "alert_type": "performance_threshold",
                "conditions": [
                    {"metric": "ctr", "operator": "less_than", "value": 0.5}
                ],
                "notification_message": "TikTok CTR below 0.5%"
            },
            platforms=["tiktok"],
            next_run=now + timedelta(minutes=30),
            run_count=0,
            error_count=0
        ),
        Automation(
            id=uuid4(),
            tenant_id=tenant.id,
            destination_id=destinations[0].id,
            name="Weekly Multi-Platform Summary",
            type="scheduled_report",
            status="paused",
            schedule_config={
                "type": "cron",
                "cron": "0 10 * * 1",  # Monday 10 AM
                "timezone": "America/New_York"
            },
            automation_config={
                "report_type": "detailed",
                "metrics": ["impressions", "clicks", "spend", "conversions"],
                "comparison_period": "previous_week"
            },
            platforms=["facebook", "tiktok"],
            next_run=None,
            run_count=0,
            error_count=0
        )
    ]

    for automation in automations:
        session.add(automation)

    await session.commit()

    for automation in automations:
        await session.refresh(automation)
        logger.info(f"Created automation: {automation.name} ({automation.status})")

    return automations


async def seed_database():
    """
    Main seeding function.

    Creates demo tenant with users, destinations, and automations.
    """
    logger.info("Starting database seeding...")

    async with async_session_maker() as session:
        try:
            # Create tenant
            tenant = await create_demo_tenant(session)

            # Create users
            users = await create_demo_users(session, tenant)

            # Create destinations
            destinations = await create_demo_destinations(session, tenant)

            # Create automations
            automations = await create_demo_automations(session, tenant, destinations)

            logger.success(
                f"Database seeded successfully! "
                f"Created: 1 tenant, {len(users)} users, "
                f"{len(destinations)} destinations, {len(automations)} automations"
            )

            logger.info("\nDemo credentials:")
            logger.info("  Admin: username=admin, password=password123")
            logger.info("  User: username=user1, password=password123")
            logger.info("  Viewer: username=viewer, password=password123")

        except Exception as e:
            logger.error(f"Error seeding database: {e}")
            await session.rollback()
            raise


async def clear_database():
    """
    Clear all data from the database.

    WARNING: This will delete all data!
    """
    logger.warning("Clearing database...")

    async with async_session_maker() as session:
        try:
            # Delete in reverse order of dependencies
            await session.execute("DELETE FROM automation_run")
            await session.execute("DELETE FROM automation")
            await session.execute("DELETE FROM ad_token")
            await session.execute("DELETE FROM destination")
            await session.execute("DELETE FROM \"user\"")
            await session.execute("DELETE FROM tenant")

            await session.commit()
            logger.success("Database cleared successfully!")

        except Exception as e:
            logger.error(f"Error clearing database: {e}")
            await session.rollback()
            raise


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Database seeding script")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear all data before seeding"
    )
    parser.add_argument(
        "--clear-only",
        action="store_true",
        help="Only clear data, do not seed"
    )

    args = parser.parse_args()

    if args.clear_only:
        asyncio.run(clear_database())
    elif args.clear:
        asyncio.run(clear_database())
        asyncio.run(seed_database())
    else:
        asyncio.run(seed_database())


if __name__ == "__main__":
    main()
