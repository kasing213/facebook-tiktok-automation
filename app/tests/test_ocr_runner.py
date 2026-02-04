#!/usr/bin/env python3
"""
OCR Authentication Test Runner

Runs all OCR authentication tests with real screenshots.
Provides convenient commands for testing different aspects of the OCR system.
"""

import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional


class OCRTestRunner:
    """Test runner for OCR authentication tests."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_dir = self.project_root / "tests"

    def run_command(self, cmd: List[str], description: str = "") -> int:
        """Run a command and return exit code."""
        if description:
            print(f"\n{'='*50}")
            print(f"📋 {description}")
            print(f"{'='*50}")

        print(f"🔧 Running: {' '.join(cmd)}")
        print("-" * 30)

        try:
            result = subprocess.run(cmd, cwd=self.project_root, check=False)
            if result.returncode == 0:
                print(f"✅ {description or 'Command'} completed successfully")
            else:
                print(f"❌ {description or 'Command'} failed with exit code {result.returncode}")
            return result.returncode
        except Exception as e:
            print(f"💥 Error running command: {e}")
            return 1

    def run_ocr_auth_tests(self) -> int:
        """Run OCR authentication tests."""
        return self.run_command([
            "python", "-m", "pytest",
            "tests/test_ocr_authentication_real.py",
            "-v", "--tb=short"
        ], "OCR Authentication Tests with Real Screenshots")

    def run_payment_verification_tests(self) -> int:
        """Run payment verification tests."""
        return self.run_command([
            "python", "-m", "pytest",
            "tests/test_payment_verification_real.py",
            "-v", "--tb=short"
        ], "Payment Verification Tests with Real OCR")

    def run_api_gateway_tests(self) -> int:
        """Run API Gateway OCR endpoint tests."""
        api_gateway_dir = self.project_root.parent / "api-gateway"
        return self.run_command([
            "python", "-m", "pytest",
            "tests/test_ocr_endpoints.py",
            "-v", "--tb=short"
        ], "API Gateway OCR Endpoint Tests")

    def run_all_ocr_tests(self) -> int:
        """Run all OCR-related tests."""
        print("\n🚀 Running Complete OCR Authentication Test Suite")
        print("=" * 60)

        exit_codes = []

        # Run main app OCR tests
        exit_codes.append(self.run_ocr_auth_tests())
        exit_codes.append(self.run_payment_verification_tests())

        # Run API Gateway tests
        # Note: Skip if API Gateway tests directory doesn't exist
        api_gateway_test_file = self.project_root.parent / "api-gateway" / "tests" / "test_ocr_endpoints.py"
        if api_gateway_test_file.exists():
            exit_codes.append(self.run_api_gateway_tests())
        else:
            print("\n⚠️ Skipping API Gateway tests (test file not found)")

        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)

        failed_tests = sum(1 for code in exit_codes if code != 0)
        total_tests = len(exit_codes)

        if failed_tests == 0:
            print("🎉 All OCR authentication tests passed!")
            return 0
        else:
            print(f"❌ {failed_tests}/{total_tests} test suites failed")
            return 1

    def run_specific_test(self, test_name: str) -> int:
        """Run a specific test by name."""
        # Find test files containing the test name
        test_files = [
            "tests/test_ocr_authentication_real.py",
            "tests/test_payment_verification_real.py"
        ]

        for test_file in test_files:
            if (self.project_root / test_file).exists():
                return self.run_command([
                    "python", "-m", "pytest",
                    test_file,
                    "-k", test_name,
                    "-v", "--tb=short"
                ], f"Running specific test: {test_name}")

        print(f"❌ Test '{test_name}' not found in any test file")
        return 1

    def check_test_environment(self) -> int:
        """Check if test environment is set up correctly."""
        print("🔍 Checking OCR Test Environment")
        print("=" * 40)

        checks_passed = 0
        total_checks = 0

        # Check if screenshot fixtures exist
        screenshots_dir = self.test_dir / "fixtures" / "screenshots"
        total_checks += 1
        if screenshots_dir.exists():
            screenshot_count = len(list(screenshots_dir.glob("*.png")) + list(screenshots_dir.glob("*.jpg")))
            print(f"✅ Screenshot fixtures directory exists ({screenshot_count} images)")
            checks_passed += 1
        else:
            print("❌ Screenshot fixtures directory missing")

        # Check if required dependencies are installed
        total_checks += 1
        try:
            import pytest
            import PIL
            import httpx
            print("✅ Required dependencies (pytest, PIL, httpx) installed")
            checks_passed += 1
        except ImportError as e:
            print(f"❌ Missing required dependency: {e}")

        # Check if test database configuration exists
        total_checks += 1
        try:
            from app.core.db import get_db_session
            print("✅ Database configuration available")
            checks_passed += 1
        except Exception as e:
            print(f"⚠️ Database configuration issue: {e}")

        # Check if JWT configuration is available
        total_checks += 1
        try:
            from app.core.external_jwt import create_external_service_token
            print("✅ JWT authentication configuration available")
            checks_passed += 1
        except Exception as e:
            print(f"❌ JWT configuration issue: {e}")

        print(f"\n📋 Environment Check: {checks_passed}/{total_checks} checks passed")

        if checks_passed == total_checks:
            print("🎉 Test environment is ready!")
            return 0
        else:
            print("⚠️ Some environment issues detected")
            return 1

    def list_available_tests(self) -> int:
        """List all available OCR tests."""
        print("📋 Available OCR Tests")
        print("=" * 30)

        test_categories = {
            "OCR Authentication Tests": [
                "test_ocr_service_creates_jwt_headers",
                "test_ocr_service_jwt_contains_user_context",
                "test_ocr_verify_screenshot_sends_jwt",
                "test_different_tenants_get_different_jwt_tokens",
                "test_ocr_with_various_screenshots"
            ],
            "Payment Verification Tests": [
                "test_verify_invoice_payment_with_valid_screenshot",
                "test_verify_invoice_payment_amount_mismatch",
                "test_verify_subscription_payment_success",
                "test_complete_invoice_to_payment_flow"
            ],
            "API Gateway Tests": [
                "test_ocr_verify_requires_jwt_authentication",
                "test_ocr_verify_with_valid_jwt",
                "test_service_jwt_validation",
                "test_tenant_isolation_in_ocr"
            ]
        }

        for category, tests in test_categories.items():
            print(f"\n🔹 {category}:")
            for test in tests:
                print(f"   • {test}")

        print(f"\n💡 Run specific test with: python {__file__} --test <test_name>")
        return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="OCR Authentication Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_ocr_runner.py                    # Run all OCR tests
  python test_ocr_runner.py --auth             # Run authentication tests only
  python test_ocr_runner.py --payment          # Run payment verification tests only
  python test_ocr_runner.py --gateway          # Run API Gateway tests only
  python test_ocr_runner.py --check            # Check test environment
  python test_ocr_runner.py --list             # List available tests
  python test_ocr_runner.py --test jwt_headers # Run specific test
        """
    )

    parser.add_argument("--auth", action="store_true",
                       help="Run OCR authentication tests only")
    parser.add_argument("--payment", action="store_true",
                       help="Run payment verification tests only")
    parser.add_argument("--gateway", action="store_true",
                       help="Run API Gateway tests only")
    parser.add_argument("--check", action="store_true",
                       help="Check test environment setup")
    parser.add_argument("--list", action="store_true",
                       help="List available tests")
    parser.add_argument("--test", metavar="TEST_NAME",
                       help="Run specific test by name")

    args = parser.parse_args()
    runner = OCRTestRunner()

    if args.check:
        return runner.check_test_environment()
    elif args.list:
        return runner.list_available_tests()
    elif args.test:
        return runner.run_specific_test(args.test)
    elif args.auth:
        return runner.run_ocr_auth_tests()
    elif args.payment:
        return runner.run_payment_verification_tests()
    elif args.gateway:
        return runner.run_api_gateway_tests()
    else:
        # Default: run all tests
        return runner.run_all_ocr_tests()


if __name__ == "__main__":
    sys.exit(main())