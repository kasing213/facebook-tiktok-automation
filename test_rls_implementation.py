#!/usr/bin/env python3
"""
RLS Implementation Test Suite

This script validates that Row Level Security (RLS) is working correctly
by testing tenant isolation across all schemas and tables.

Test scenarios:
1. Verify RLS is enabled on all tables
2. Test tenant isolation works correctly
3. Test service role bypass functionality
4. Validate helper functions work
5. Performance impact assessment
"""

import os
import sys
import psycopg2
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import argparse

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv not installed, relying on system environment variables")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RLSTestSuite:
    """Comprehensive test suite for RLS implementation"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.connection = None
        self.test_tenant_a_id = str(uuid.uuid4())
        self.test_tenant_b_id = str(uuid.uuid4())
        self.test_results = []

    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(self.database_url)
            self.connection.autocommit = True  # For testing convenience
            logger.info("✅ Database connection established")
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            sys.exit(1)

    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("🔌 Database connection closed")

    def execute_query(self, query: str, description: str = "", fetch_results: bool = True) -> Optional[List[Tuple]]:
        """Execute a query and return results"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                if fetch_results and cursor.description:
                    return cursor.fetchall()
                return []
        except Exception as e:
            logger.error(f"❌ Query failed ({description}): {e}")
            raise

    def log_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        if details:
            logger.info(f"   {details}")

        self.test_results.append({
            'test_name': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.utcnow()
        })

    def test_rls_enabled_status(self) -> bool:
        """Test 1: Verify RLS is enabled on all expected tables"""
        logger.info("🧪 Test 1: Checking RLS enabled status...")

        try:
            # Use the verification function created by migration
            result = self.execute_query(
                "SELECT * FROM public.verify_rls_status();",
                "Check RLS status"
            )

            if not result:
                self.log_test_result("RLS Status Check", False, "No tables found or verification function missing")
                return False

            total_tables = len(result)
            enabled_tables = sum(1 for row in result if row[2])  # row[2] is rls_enabled

            # Expected minimum number of tables (should be around 30+)
            expected_min_tables = 25

            if total_tables < expected_min_tables:
                self.log_test_result(
                    "RLS Status Check", False,
                    f"Only {total_tables} tables found, expected at least {expected_min_tables}"
                )
                return False

            if enabled_tables == total_tables:
                self.log_test_result(
                    "RLS Status Check", True,
                    f"All {total_tables} tables have RLS enabled"
                )
                return True
            else:
                missing_count = total_tables - enabled_tables
                self.log_test_result(
                    "RLS Status Check", False,
                    f"{missing_count} out of {total_tables} tables missing RLS"
                )

                # Show some missing tables
                missing_tables = [f"{row[0]}.{row[1]}" for row in result if not row[2]]
                for table in missing_tables[:3]:
                    logger.warning(f"   Missing RLS: {table}")

                return False

        except Exception as e:
            self.log_test_result("RLS Status Check", False, f"Error: {e}")
            return False

    def test_helper_functions(self) -> bool:
        """Test 2: Verify RLS helper functions work correctly"""
        logger.info("🧪 Test 2: Testing RLS helper functions...")

        try:
            # Test 1: get_tenant_id() with no context (should return NULL)
            result = self.execute_query("SELECT public.get_tenant_id();", "Test get_tenant_id() without context")

            if result and result[0][0] is None:
                self.log_test_result("get_tenant_id() - no context", True, "Returns NULL as expected")
            else:
                self.log_test_result("get_tenant_id() - no context", False, f"Unexpected result: {result}")
                return False

            # Test 2: set_tenant_context() and get_tenant_id()
            test_tenant_id = str(uuid.uuid4())
            self.execute_query(
                f"SELECT public.set_tenant_context('{test_tenant_id}');",
                "Set tenant context",
                fetch_results=False
            )

            result = self.execute_query("SELECT public.get_tenant_id();", "Test get_tenant_id() with context")

            if result and str(result[0][0]) == test_tenant_id:
                self.log_test_result("set/get tenant context", True, "Tenant context works correctly")
            else:
                self.log_test_result("set/get tenant context", False, f"Context mismatch: expected {test_tenant_id}, got {result}")
                return False

            return True

        except Exception as e:
            self.log_test_result("Helper Functions Test", False, f"Error: {e}")
            return False

    def setup_test_data(self) -> bool:
        """Setup test data for tenant isolation testing"""
        logger.info("🧪 Setting up test data...")

        try:
            # Create test tenants (using service role bypass)
            tenant_a_query = f"""
            INSERT INTO tenant (id, name, slug, is_active)
            VALUES ('{self.test_tenant_a_id}', 'Test Tenant A', 'test-tenant-a', true)
            ON CONFLICT (id) DO NOTHING;
            """

            tenant_b_query = f"""
            INSERT INTO tenant (id, name, slug, is_active)
            VALUES ('{self.test_tenant_b_id}', 'Test Tenant B', 'test-tenant-b', true)
            ON CONFLICT (id) DO NOTHING;
            """

            self.execute_query(tenant_a_query, "Create test tenant A", fetch_results=False)
            self.execute_query(tenant_b_query, "Create test tenant B", fetch_results=False)

            # Create test users
            user_a_query = f"""
            INSERT INTO "user" (id, tenant_id, username, email, is_active)
            VALUES ('{uuid.uuid4()}', '{self.test_tenant_a_id}', 'user_a', 'user_a@test.com', true)
            ON CONFLICT DO NOTHING;
            """

            user_b_query = f"""
            INSERT INTO "user" (id, tenant_id, username, email, is_active)
            VALUES ('{uuid.uuid4()}', '{self.test_tenant_b_id}', 'user_b', 'user_b@test.com', true)
            ON CONFLICT DO NOTHING;
            """

            self.execute_query(user_a_query, "Create test user A", fetch_results=False)
            self.execute_query(user_b_query, "Create test user B", fetch_results=False)

            # Create test data in invoice schema if it exists
            try:
                customer_a_query = f"""
                INSERT INTO invoice.customer (id, tenant_id, name, email)
                VALUES ('{uuid.uuid4()}', '{self.test_tenant_a_id}', 'Customer A', 'customer_a@test.com')
                ON CONFLICT DO NOTHING;
                """

                customer_b_query = f"""
                INSERT INTO invoice.customer (id, tenant_id, name, email)
                VALUES ('{uuid.uuid4()}', '{self.test_tenant_b_id}', 'Customer B', 'customer_b@test.com')
                ON CONFLICT DO NOTHING;
                """

                self.execute_query(customer_a_query, "Create test customer A", fetch_results=False)
                self.execute_query(customer_b_query, "Create test customer B", fetch_results=False)

            except Exception as e:
                logger.warning(f"Could not create invoice test data: {e}")

            self.log_test_result("Test Data Setup", True, "Test data created successfully")
            return True

        except Exception as e:
            self.log_test_result("Test Data Setup", False, f"Error: {e}")
            return False

    def test_tenant_isolation(self) -> bool:
        """Test 3: Verify tenant isolation works correctly"""
        logger.info("🧪 Test 3: Testing tenant isolation...")

        try:
            # Test isolation in public schema (user table)
            isolation_passed = True

            # Set context to tenant A
            self.execute_query(
                f"SELECT public.set_tenant_context('{self.test_tenant_a_id}');",
                "Set context to tenant A",
                fetch_results=False
            )

            # Query users - should only see tenant A users
            result_a = self.execute_query(
                'SELECT username FROM "user" WHERE username LIKE \'user_%\';',
                "Query users as tenant A"
            )

            tenant_a_users = [row[0] for row in result_a] if result_a else []

            # Set context to tenant B
            self.execute_query(
                f"SELECT public.set_tenant_context('{self.test_tenant_b_id}');",
                "Set context to tenant B",
                fetch_results=False
            )

            # Query users - should only see tenant B users
            result_b = self.execute_query(
                'SELECT username FROM "user" WHERE username LIKE \'user_%\';',
                "Query users as tenant B"
            )

            tenant_b_users = [row[0] for row in result_b] if result_b else []

            # Verify isolation
            if 'user_a' in tenant_a_users and 'user_a' not in tenant_b_users:
                self.log_test_result("User Isolation - Tenant A", True, "Can see own user, cannot see other tenant's user")
            else:
                self.log_test_result("User Isolation - Tenant A", False, f"Tenant A users: {tenant_a_users}, Tenant B users: {tenant_b_users}")
                isolation_passed = False

            if 'user_b' in tenant_b_users and 'user_b' not in tenant_a_users:
                self.log_test_result("User Isolation - Tenant B", True, "Can see own user, cannot see other tenant's user")
            else:
                self.log_test_result("User Isolation - Tenant B", False, f"Tenant A users: {tenant_a_users}, Tenant B users: {tenant_b_users}")
                isolation_passed = False

            # Test isolation in invoice schema if available
            try:
                # Set context to tenant A
                self.execute_query(
                    f"SELECT public.set_tenant_context('{self.test_tenant_a_id}');",
                    "Set context to tenant A for invoice test",
                    fetch_results=False
                )

                result_invoice_a = self.execute_query(
                    "SELECT name FROM invoice.customer WHERE name LIKE 'Customer %';",
                    "Query invoice customers as tenant A"
                )

                # Set context to tenant B
                self.execute_query(
                    f"SELECT public.set_tenant_context('{self.test_tenant_b_id}');",
                    "Set context to tenant B for invoice test",
                    fetch_results=False
                )

                result_invoice_b = self.execute_query(
                    "SELECT name FROM invoice.customer WHERE name LIKE 'Customer %';",
                    "Query invoice customers as tenant B"
                )

                customers_a = [row[0] for row in result_invoice_a] if result_invoice_a else []
                customers_b = [row[0] for row in result_invoice_b] if result_invoice_b else []

                if 'Customer A' in customers_a and 'Customer A' not in customers_b:
                    self.log_test_result("Invoice Isolation", True, "Invoice schema isolation working correctly")
                else:
                    self.log_test_result("Invoice Isolation", False, f"Customers A: {customers_a}, Customers B: {customers_b}")
                    isolation_passed = False

            except Exception as e:
                logger.warning(f"Could not test invoice isolation: {e}")

            return isolation_passed

        except Exception as e:
            self.log_test_result("Tenant Isolation Test", False, f"Error: {e}")
            return False

    def test_service_role_bypass(self) -> bool:
        """Test 4: Verify service role can bypass RLS (if using service role)"""
        logger.info("🧪 Test 4: Testing service role bypass...")

        try:
            # Clear tenant context
            self.execute_query("SELECT public.set_tenant_context(NULL);", "Clear tenant context", fetch_results=False)

            # Try to query all users without tenant context
            # If using service role, this should work and return all users
            result = self.execute_query(
                'SELECT username FROM "user" WHERE username LIKE \'user_%\' ORDER BY username;',
                "Query all users without tenant context"
            )

            if result:
                all_users = [row[0] for row in result]

                # If we can see both test users, service role bypass is working
                if 'user_a' in all_users and 'user_b' in all_users:
                    self.log_test_result("Service Role Bypass", True, f"Can see all users: {all_users}")
                    return True
                else:
                    self.log_test_result("Service Role Bypass", False, f"Cannot see all users, only: {all_users}")
                    return False
            else:
                # No results could mean RLS is blocking or no data exists
                self.log_test_result("Service Role Bypass", False, "No users returned - RLS may be blocking service role")
                return False

        except Exception as e:
            self.log_test_result("Service Role Bypass Test", False, f"Error: {e}")
            return False

    def test_policy_count(self) -> bool:
        """Test 5: Verify adequate number of policies exist"""
        logger.info("🧪 Test 5: Checking policy count...")

        try:
            # Get policy count by table
            policy_query = """
            SELECT
                schemaname,
                tablename,
                COUNT(*) as policy_count
            FROM pg_policies
            WHERE schemaname IN ('public', 'invoice', 'scriptclient', 'audit_sales')
            GROUP BY schemaname, tablename
            HAVING COUNT(*) >= 4  -- Should have SELECT, INSERT, UPDATE, DELETE policies
            ORDER BY schemaname, tablename;
            """

            result = self.execute_query(policy_query, "Check policy counts")

            if result:
                tables_with_full_policies = len(result)
                total_policies = sum(row[2] for row in result)

                self.log_test_result(
                    "Policy Count Check", True,
                    f"{tables_with_full_policies} tables have complete RLS policies ({total_policies} total policies)"
                )

                # Show some examples
                for row in result[:5]:
                    logger.info(f"   {row[0]}.{row[1]}: {row[2]} policies")

                return True
            else:
                self.log_test_result("Policy Count Check", False, "No RLS policies found")
                return False

        except Exception as e:
            self.log_test_result("Policy Count Test", False, f"Error: {e}")
            return False

    def cleanup_test_data(self):
        """Clean up test data"""
        logger.info("🧹 Cleaning up test data...")

        try:
            # Delete test data (using service role bypass)
            cleanup_queries = [
                f"DELETE FROM \"user\" WHERE tenant_id IN ('{self.test_tenant_a_id}', '{self.test_tenant_b_id}');",
                f"DELETE FROM tenant WHERE id IN ('{self.test_tenant_a_id}', '{self.test_tenant_b_id}');"
            ]

            # Also try to clean invoice schema if it exists
            try:
                cleanup_queries.insert(0, f"DELETE FROM invoice.customer WHERE tenant_id IN ('{self.test_tenant_a_id}', '{self.test_tenant_b_id}');")
            except:
                pass

            for query in cleanup_queries:
                try:
                    self.execute_query(query, "Cleanup", fetch_results=False)
                except Exception as e:
                    logger.warning(f"Cleanup warning: {e}")

            logger.info("✅ Test data cleanup completed")

        except Exception as e:
            logger.warning(f"⚠️  Test data cleanup failed: {e}")

    def run_all_tests(self) -> bool:
        """Run all RLS tests"""
        logger.info("🧪 Starting comprehensive RLS test suite...")

        all_passed = True

        # Test 1: RLS enabled status
        if not self.test_rls_enabled_status():
            all_passed = False

        # Test 2: Helper functions
        if not self.test_helper_functions():
            all_passed = False

        # Test 3: Setup test data
        if not self.setup_test_data():
            all_passed = False
            return False  # Can't continue without test data

        # Test 4: Tenant isolation
        if not self.test_tenant_isolation():
            all_passed = False

        # Test 5: Service role bypass
        if not self.test_service_role_bypass():
            all_passed = False

        # Test 6: Policy count
        if not self.test_policy_count():
            all_passed = False

        # Cleanup
        self.cleanup_test_data()

        return all_passed

    def print_test_summary(self):
        """Print test results summary"""
        logger.info("\n" + "="*60)
        logger.info("🧪 RLS Test Suite Summary")
        logger.info("="*60)

        passed_count = sum(1 for result in self.test_results if result['passed'])
        total_count = len(self.test_results)

        logger.info(f"Total tests: {total_count}")
        logger.info(f"Passed: {passed_count}")
        logger.info(f"Failed: {total_count - passed_count}")
        logger.info(f"Success rate: {(passed_count/total_count)*100:.1f}%")

        logger.info("\nTest Details:")
        for result in self.test_results:
            status = "✅" if result['passed'] else "❌"
            logger.info(f"{status} {result['test_name']}")
            if result['details']:
                logger.info(f"   {result['details']}")

        logger.info("="*60)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Test RLS Implementation")
    parser.add_argument('--quick', action='store_true', help='Run only basic status checks')

    args = parser.parse_args()

    # Load database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("❌ DATABASE_URL environment variable not set")
        logger.info("💡 Set your DATABASE_URL before running this script")
        sys.exit(1)

    # Convert SQLAlchemy format to psycopg2 format
    # SQLAlchemy uses postgresql+psycopg://, psycopg2 expects postgresql://
    if '+psycopg://' in database_url:
        database_url = database_url.replace('postgresql+psycopg://', 'postgresql://')
        logger.info("📝 Converted DATABASE_URL from SQLAlchemy to psycopg2 format")

    # Initialize test suite
    test_suite = RLSTestSuite(database_url)

    try:
        # Connect to database
        test_suite.connect()

        if args.quick:
            # Run only basic checks
            logger.info("🔍 Running quick RLS status check...")
            success = test_suite.test_rls_enabled_status()
        else:
            # Run full test suite
            success = test_suite.run_all_tests()

        # Print summary
        test_suite.print_test_summary()

        if success:
            logger.info("🎉 All RLS tests passed! Your database security is working correctly.")
        else:
            logger.error("❌ Some RLS tests failed. Please review the results above.")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("🛑 Testing cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Test suite error: {e}")
        sys.exit(1)
    finally:
        test_suite.disconnect()

if __name__ == "__main__":
    main()