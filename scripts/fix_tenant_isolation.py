"""
Fix legacy data tenant isolation issues.

This script fixes data that was created before tenant isolation was properly enforced.
It updates tenant_id values to match the merchant/creator's tenant.
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool


def get_engine():
    """Create database engine."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not set")

    # Convert to psycopg3 format if needed
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    return create_engine(
        database_url,
        poolclass=NullPool,
        isolation_level="AUTOCOMMIT",
        connect_args={
            "prepare_threshold": None,  # Completely disable prepared statements
            "autocommit": True,
        }
    )


def fix_invoice_tenant_id(engine):
    """Fix invoices: set tenant_id to match the merchant (creator) user's tenant."""
    print("\n=== Step 1: Fixing Invoice tenant_id ===")

    with engine.connect() as conn:
        # Check current state
        result = conn.execute(text("""
            SELECT
                i.tenant_id as invoice_tenant,
                u.tenant_id as user_tenant,
                COUNT(*) as count
            FROM invoice.invoice i
            LEFT JOIN public.user u ON i.merchant_id = u.id
            GROUP BY i.tenant_id, u.tenant_id
        """))
        rows = result.fetchall()
        print("Current invoice tenant distribution:")
        for row in rows:
            match = "✅ MATCH" if str(row[0]) == str(row[1]) else "❌ MISMATCH"
            print(f"  Invoice tenant: {row[0]}, User tenant: {row[1]}, Count: {row[2]} {match}")

        # Fix mismatches
        result = conn.execute(text("""
            UPDATE invoice.invoice i
            SET tenant_id = u.tenant_id
            FROM public.user u
            WHERE i.merchant_id = u.id
              AND (i.tenant_id IS NULL OR i.tenant_id != u.tenant_id)
            RETURNING i.id
        """))
        fixed = result.fetchall()
        conn.commit()
        print(f"Fixed {len(fixed)} invoices")


def fix_customer_tenant_id(engine):
    """Fix customers: set tenant_id based on their invoices' merchant."""
    print("\n=== Step 2: Fixing Customer tenant_id ===")

    with engine.connect() as conn:
        # Check current state
        result = conn.execute(text("""
            SELECT tenant_id, COUNT(*) as count
            FROM invoice.customer
            GROUP BY tenant_id
        """))
        rows = result.fetchall()
        print("Current customer tenant distribution:")
        for row in rows:
            print(f"  Tenant: {row[0]}, Count: {row[1]}")

        # Fix based on invoice merchant relationship
        result = conn.execute(text("""
            UPDATE invoice.customer c
            SET tenant_id = u.tenant_id
            FROM invoice.invoice i
            JOIN public.user u ON i.merchant_id = u.id
            WHERE c.id = i.customer_id
              AND (c.tenant_id IS NULL OR c.tenant_id != u.tenant_id)
            RETURNING c.id
        """))
        fixed = result.fetchall()
        conn.commit()
        print(f"Fixed {len(fixed)} customers")


def fix_product_tenant_id(engine):
    """Fix products tenant_id - check and report."""
    print("\n=== Step 3: Checking Product tenant_id ===")

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT tenant_id, COUNT(*) as count,
                   STRING_AGG(name, ', ' ORDER BY name) as sample_products
            FROM inventory.products
            GROUP BY tenant_id
        """))
        rows = result.fetchall()
        print("Current product tenant distribution:")
        for row in rows:
            products = row[2][:100] + "..." if len(row[2]) > 100 else row[2]
            print(f"  Tenant: {row[0]}, Count: {row[1]}, Products: {products}")

        if len(rows) > 1:
            print("\n⚠️  Products exist in multiple tenants!")
            print("   Manual review needed to determine correct tenant_id")
        else:
            print("\n✅ All products belong to single tenant - no fix needed")


def fix_stock_movement_tenant_id(engine):
    """Fix stock movements to match product tenant."""
    print("\n=== Step 4: Fixing Stock Movement tenant_id ===")

    with engine.connect() as conn:
        # Fix based on product tenant
        result = conn.execute(text("""
            UPDATE inventory.stock_movements sm
            SET tenant_id = p.tenant_id
            FROM inventory.products p
            WHERE sm.product_id = p.id
              AND sm.tenant_id != p.tenant_id
            RETURNING sm.id
        """))
        fixed = result.fetchall()
        conn.commit()
        print(f"Fixed {len(fixed)} stock movements")


def verify_isolation(engine):
    """Verify data is properly isolated."""
    print("\n=== Step 5: Verification ===")

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                'invoices' as table_name,
                tenant_id::text,
                COUNT(*)::text as count
            FROM invoice.invoice
            GROUP BY tenant_id
            UNION ALL
            SELECT
                'customers',
                tenant_id::text,
                COUNT(*)::text
            FROM invoice.customer
            GROUP BY tenant_id
            UNION ALL
            SELECT
                'products',
                tenant_id::text,
                COUNT(*)::text
            FROM inventory.products
            GROUP BY tenant_id
            ORDER BY 1, 2
        """))
        rows = result.fetchall()

        print("\nFinal data distribution by tenant:")
        current_table = None
        for row in rows:
            if row[0] != current_table:
                current_table = row[0]
                print(f"\n  {row[0]}:")
            print(f"    Tenant {row[1]}: {row[2]} records")

        # Check for any tenant mismatches in invoices
        result = conn.execute(text("""
            SELECT COUNT(*) FROM invoice.invoice i
            LEFT JOIN public.user u ON i.merchant_id = u.id
            WHERE i.tenant_id != u.tenant_id OR i.tenant_id IS NULL
        """))
        mismatches = result.scalar()

        if mismatches == 0:
            print("\n✅ All invoices have correct tenant_id!")
        else:
            print(f"\n❌ {mismatches} invoices still have incorrect tenant_id")


def main():
    print("=" * 60)
    print("Fix Legacy Data Tenant Isolation")
    print("=" * 60)

    engine = get_engine()

    fix_invoice_tenant_id(engine)
    fix_customer_tenant_id(engine)
    fix_product_tenant_id(engine)
    fix_stock_movement_tenant_id(engine)
    verify_isolation(engine)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
