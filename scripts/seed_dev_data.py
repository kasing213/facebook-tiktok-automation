#!/usr/bin/env python3
"""
Development seed data script for Facebook/TikTok Automation Project
Creates a test tenant with basic configuration for development.
"""
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.models import Base, Tenant, User, Destination, UserRole, DestinationType

# Database connection
DATABASE_URL = "postgresql+psycopg2://fbauto:kasing@localhost:5432/ad_reporting"

def create_seed_data():
    """Create development seed data"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        # Check if seed data already exists
        existing_tenant = session.query(Tenant).filter_by(slug="dev-test").first()
        if existing_tenant:
            print("Seed data already exists. Skipping creation.")
            return

        # Create test tenant
        tenant = Tenant(
            name="Development Test Tenant",
            slug="dev-test",
            is_active=True,
            settings={
                "timezone": "UTC",
                "default_currency": "USD",
                "notification_preferences": {
                    "daily_reports": True,
                    "error_alerts": True
                }
            }
        )
        session.add(tenant)
        session.flush()  # Get the tenant ID

        print(f"Created tenant: {tenant.name} (ID: {tenant.id})")

        # Create admin user
        admin_user = User(
            tenant_id=tenant.id,
            email="admin@dev-test.local",
            username="admin",
            role=UserRole.admin,
            telegram_user_id="123456789",  # Fake Telegram ID for testing
            is_active=True
        )
        session.add(admin_user)

        # Create regular user
        regular_user = User(
            tenant_id=tenant.id,
            email="user@dev-test.local",
            username="testuser",
            role=UserRole.user,
            telegram_user_id="987654321",  # Fake Telegram ID for testing
            is_active=True
        )
        session.add(regular_user)

        print(f"Created users: {admin_user.username}, {regular_user.username}")

        # Create test destinations
        telegram_destination = Destination(
            tenant_id=tenant.id,
            name="Test Telegram Chat",
            type=DestinationType.telegram_chat,
            config={
                "chat_id": "-1001234567890",  # Fake chat ID for testing
                "bot_token": "1234567890:FAKE_BOT_TOKEN_FOR_TESTING"
            },
            is_active=True
        )
        session.add(telegram_destination)

        webhook_destination = Destination(
            tenant_id=tenant.id,
            name="Test Webhook",
            type=DestinationType.webhook,
            config={
                "url": "https://webhook.site/test-endpoint",
                "headers": {
                    "Authorization": "Bearer test-token",
                    "Content-Type": "application/json"
                },
                "method": "POST"
            },
            is_active=True
        )
        session.add(webhook_destination)

        email_destination = Destination(
            tenant_id=tenant.id,
            name="Test Email Destination",
            type=DestinationType.email,
            config={
                "recipients": ["test@dev-test.local", "admin@dev-test.local"],
                "subject_template": "Facebook/TikTok Report - {date}",
                "smtp_config": {
                    "host": "smtp.example.com",
                    "port": 587,
                    "use_tls": True,
                    "username": "reports@dev-test.local",
                    "password": "fake-password"
                }
            },
            is_active=False  # Disabled by default for testing
        )
        session.add(email_destination)

        print(f"Created destinations: Telegram, Webhook, Email")

        # Commit all changes
        session.commit()
        print("\nSeed data created successfully!")
        print(f"Tenant ID: {tenant.id}")
        print(f"Tenant Slug: {tenant.slug}")
        print(f"Admin User ID: {admin_user.id}")
        print(f"Regular User ID: {regular_user.id}")
        print(f"Active Destinations: {len([d for d in [telegram_destination, webhook_destination, email_destination] if d.is_active])}")

    except Exception as e:
        session.rollback()
        print(f"Error creating seed data: {e}")
        raise
    finally:
        session.close()

def delete_seed_data():
    """Delete development seed data"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        # Find and delete the test tenant (cascade will handle related records)
        tenant = session.query(Tenant).filter_by(slug="dev-test").first()
        if tenant:
            session.delete(tenant)
            session.commit()
            print("Seed data deleted successfully!")
        else:
            print("No seed data found to delete.")
    except Exception as e:
        session.rollback()
        print(f"Error deleting seed data: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage development seed data")
    parser.add_argument("--delete", action="store_true", help="Delete seed data instead of creating it")
    args = parser.parse_args()

    if args.delete:
        delete_seed_data()
    else:
        create_seed_data()