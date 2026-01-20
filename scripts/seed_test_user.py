"""
Test User Seed Script for Playwright E2E Tests

Creates a test user with verified email and sample data for testing.

Usage:
    python scripts/seed_test_user.py

The test user credentials are:
    Email: test@example.com
    Password: TestPassword123!
    Username: testuser
"""

import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Test user configuration
TEST_USER = {
    "email": "test@example.com",
    "password": "TestPassword123!",
    "username": "testuser",
}

# Sample data configuration
SAMPLE_PRODUCTS = [
    {
        "name": "Widget A",
        "sku": "W01",  # Max 3 chars per DB schema
        "unit_price": 29.99,
        "cost_price": 15.00,
        "current_stock": 100,
        "low_stock_threshold": 10,
    },
    {
        "name": "Gadget B",
        "sku": "G02",
        "unit_price": 49.99,
        "cost_price": 25.00,
        "current_stock": 50,
        "low_stock_threshold": 5,
    },
    {
        "name": "Service C",
        "sku": "S03",
        "unit_price": 99.99,
        "cost_price": 0,
        "current_stock": 0,
        "low_stock_threshold": 0,
        "track_stock": False,
    },
]

SAMPLE_CUSTOMERS = [
    {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1234567890",
        "address": "123 Test Street",
    },
    {
        "name": "Jane Smith",
        "email": "jane@example.com",
        "phone": "+0987654321",
        "address": "456 Demo Avenue",
    },
]


def get_database_url():
    """Get database URL from environment or .env file"""
    # Try environment variable first
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        return db_url

    # Try loading from .env file
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DATABASE_URL="):
                    return line.split("=", 1)[1].strip('"').strip("'")

    raise ValueError("DATABASE_URL not found in environment or .env file")


def seed_test_user():
    """Create test user and sample data"""
    db_url = get_database_url()
    engine = create_engine(db_url)

    with engine.connect() as conn:
        # Check if test user already exists
        result = conn.execute(
            text("SELECT id FROM public.user WHERE email = :email"),
            {"email": TEST_USER["email"]},
        )
        existing_user = result.fetchone()

        if existing_user:
            print(f"Test user already exists with ID: {existing_user[0]}")
            user_id = existing_user[0]

            # Get tenant_id
            result = conn.execute(
                text("SELECT tenant_id FROM public.user WHERE id = :id"),
                {"id": user_id},
            )
            tenant_id = result.fetchone()[0]
        else:
            # Create tenant first
            tenant_id = str(uuid4())
            conn.execute(
                text("""
                    INSERT INTO public.tenant (id, name, created_at)
                    VALUES (:id, :name, :created_at)
                """),
                {
                    "id": tenant_id,
                    "name": "Test Tenant",
                    "created_at": datetime.now(timezone.utc),
                },
            )
            print(f"Created tenant: {tenant_id}")

            # Create user
            user_id = str(uuid4())
            password_hash = pwd_context.hash(TEST_USER["password"])
            conn.execute(
                text("""
                    INSERT INTO public.user (id, email, username, hashed_password, tenant_id, role, is_active, email_verified_at, created_at)
                    VALUES (:id, :email, :username, :password, :tenant_id, :role, :is_active, :verified_at, :created_at)
                """),
                {
                    "id": user_id,
                    "email": TEST_USER["email"],
                    "username": TEST_USER["username"],
                    "password": password_hash,
                    "tenant_id": tenant_id,
                    "role": "admin",
                    "is_active": True,
                    "verified_at": datetime.now(timezone.utc),
                    "created_at": datetime.now(timezone.utc),
                },
            )
            print(f"Created test user: {TEST_USER['email']} (ID: {user_id})")

        # Create sample products
        for product in SAMPLE_PRODUCTS:
            try:
                result = conn.execute(
                    text("SELECT id FROM inventory.products WHERE sku = :sku AND tenant_id = CAST(:tenant_id AS UUID)"),
                    {"sku": product["sku"], "tenant_id": str(tenant_id)},
                )
                if result.fetchone():
                    print(f"Product already exists: {product['sku']}")
                    continue
            except Exception as e:
                print(f"Note: Could not check if product exists: {e}")

            try:
                product_id = str(uuid4())
                conn.execute(
                    text("""
                        INSERT INTO inventory.products (id, tenant_id, name, sku, unit_price, cost_price, currency, current_stock, low_stock_threshold, track_stock, is_active, created_at, updated_at)
                        VALUES (:id, CAST(:tenant_id AS UUID), :name, :sku, :unit_price, :cost_price, :currency, :current_stock, :low_stock_threshold, :track_stock, :is_active, :created_at, :updated_at)
                    """),
                    {
                        "id": product_id,
                        "tenant_id": str(tenant_id),
                        "name": product["name"],
                        "sku": product["sku"],
                        "unit_price": product["unit_price"],
                        "cost_price": product["cost_price"],
                        "currency": "USD",  # 3-char currency code
                        "current_stock": product["current_stock"],
                        "low_stock_threshold": product["low_stock_threshold"],
                        "track_stock": product.get("track_stock", True),
                        "is_active": True,
                        "created_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc),
                    },
                )
                print(f"Created product: {product['name']} ({product['sku']})")
            except Exception as e:
                print(f"Warning: Could not create product {product['name']}: {e}")

        # Create sample customers
        for customer in SAMPLE_CUSTOMERS:
            try:
                result = conn.execute(
                    text("SELECT id FROM invoice.customer WHERE email = :email AND tenant_id = CAST(:tenant_id AS UUID)"),
                    {"email": customer["email"], "tenant_id": str(tenant_id)},
                )
                if result.fetchone():
                    print(f"Customer already exists: {customer['email']}")
                    continue
            except Exception as e:
                print(f"Note: Could not check if customer exists: {e}")

            try:
                customer_id = str(uuid4())
                conn.execute(
                    text("""
                        INSERT INTO invoice.customer (id, tenant_id, name, email, phone, address, created_at)
                        VALUES (:id, CAST(:tenant_id AS UUID), :name, :email, :phone, :address, :created_at)
                    """),
                    {
                        "id": customer_id,
                        "tenant_id": str(tenant_id),
                        "name": customer["name"],
                        "email": customer["email"],
                        "phone": customer["phone"],
                        "address": customer["address"],
                        "created_at": datetime.now(timezone.utc),
                    },
                )
                print(f"Created customer: {customer['name']} ({customer['email']})")
            except Exception as e:
                print(f"Warning: Could not create customer {customer['name']}: {e}")

        # Commit all changes
        conn.commit()

    print("\n✅ Test data seeded successfully!")
    print(f"\nTest user credentials:")
    print(f"  Email:    {TEST_USER['email']}")
    print(f"  Password: {TEST_USER['password']}")
    print(f"  Username: {TEST_USER['username']}")


def cleanup_test_user():
    """Remove test user and associated data"""
    db_url = get_database_url()
    engine = create_engine(db_url)

    with engine.connect() as conn:
        # Get test user
        result = conn.execute(
            text("SELECT id, tenant_id FROM public.user WHERE email = :email"),
            {"email": TEST_USER["email"]},
        )
        row = result.fetchone()

        if not row:
            print("Test user not found")
            return

        user_id, tenant_id = row

        # Delete in order to respect foreign keys
        conn.execute(
            text("DELETE FROM inventory.stock_movements WHERE tenant_id = :tenant_id"),
            {"tenant_id": tenant_id},
        )
        conn.execute(
            text("DELETE FROM inventory.products WHERE tenant_id = :tenant_id"),
            {"tenant_id": tenant_id},
        )
        conn.execute(
            text("DELETE FROM invoice.invoice WHERE tenant_id = :tenant_id"),
            {"tenant_id": tenant_id},
        )
        conn.execute(
            text("DELETE FROM invoice.customer WHERE tenant_id = :tenant_id"),
            {"tenant_id": tenant_id},
        )
        conn.execute(
            text("DELETE FROM public.refresh_token WHERE user_id = :user_id"),
            {"user_id": user_id},
        )
        conn.execute(
            text("DELETE FROM public.user WHERE id = :id"),
            {"id": user_id},
        )
        conn.execute(
            text("DELETE FROM public.tenant WHERE id = :id"),
            {"id": tenant_id},
        )

        conn.commit()

    print("✅ Test user and data cleaned up")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed test user for E2E tests")
    parser.add_argument("--cleanup", action="store_true", help="Remove test user instead of creating")
    args = parser.parse_args()

    if args.cleanup:
        cleanup_test_user()
    else:
        seed_test_user()
