#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authentication API Testing Script
Tests user registration, login, JWT tokens, and protected endpoints
"""
import sys
import io
import requests
import json
from uuid import uuid4

# Fix Windows console encoding for emojis
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration
BASE_URL = "http://localhost:8000"
TENANT_ID = None  # Will be created during test

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_result(test_name, success, response=None):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"\n{status} | {test_name}")
    if response:
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response: {response.text}")

    # Print error details for failed tests
    if not success and response and response.status_code >= 400:
        print(f"⚠️  Error Details: Status {response.status_code}")

def test_health_check():
    """Test 1: Health Check"""
    print_section("Test 1: Health Check")

    response = requests.get(f"{BASE_URL}/health")
    success = response.status_code == 200 and response.json().get("status") == "healthy"
    print_result("Health Check", success, response)

    return success

def test_create_tenant():
    """Test 2: Get or Create Tenant"""
    print_section("Test 2: Get or Create Tenant")

    global TENANT_ID

    # First, try to get existing tenants
    response = requests.get(f"{BASE_URL}/api/tenants")
    if response.status_code == 200 and len(response.json()) > 0:
        # Use the first existing tenant
        TENANT_ID = response.json()[0]["id"]
        print(f"Using existing Tenant ID: {TENANT_ID}")
        print_result("Get Existing Tenant", True, response)
        return True

    # If no tenants exist, create one
    tenant_data = {
        "name": "Test Organization",
        "slug": f"test-org-{uuid4().hex[:8]}",
        "admin_email": "admin@test.com",
        "admin_username": "test_admin"
    }

    response = requests.post(f"{BASE_URL}/api/tenants", json=tenant_data)
    success = response.status_code == 200

    if success:
        TENANT_ID = response.json().get("id")
        print(f"Created Tenant ID: {TENANT_ID}")

    print_result("Create Tenant", success, response)
    return success

def test_list_tenants():
    """Test 3: List Tenants"""
    print_section("Test 3: List Tenants")

    response = requests.get(f"{BASE_URL}/api/tenants")
    success = response.status_code == 200 and isinstance(response.json(), list)
    print_result("List Tenants", success, response)

    return success

def test_user_registration():
    """Test 4: User Registration"""
    print_section("Test 4: User Registration")

    if not TENANT_ID:
        print("❌ SKIP | No tenant ID available")
        return False

    user_data = {
        "tenant_id": TENANT_ID,
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "SecurePassword123!"
    }

    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    success = response.status_code == 201
    print_result("User Registration", success, response)

    return success

def test_duplicate_registration():
    """Test 5: Duplicate Registration (Should Fail)"""
    print_section("Test 5: Duplicate Registration (Should Fail)")

    if not TENANT_ID:
        print("❌ SKIP | No tenant ID available")
        return False

    user_data = {
        "tenant_id": TENANT_ID,
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "SecurePassword123!"
    }

    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    success = response.status_code == 400  # Should fail with 400
    print_result("Duplicate Registration Block", success, response)

    return success

def test_user_login():
    """Test 6: User Login"""
    print_section("Test 6: User Login")

    login_data = {
        "username": "testuser",
        "password": "SecurePassword123!"
    }

    # OAuth2PasswordRequestForm expects form data, not JSON
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data=login_data  # Use data instead of json for form data
    )

    success = response.status_code == 200 and "access_token" in response.json()
    print_result("User Login", success, response)

    if success:
        return response.json().get("access_token")
    return None

def test_invalid_login():
    """Test 7: Invalid Login (Wrong Password)"""
    print_section("Test 7: Invalid Login (Should Fail)")

    login_data = {
        "username": "testuser",
        "password": "WrongPassword123!"
    }

    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    success = response.status_code == 401  # Should fail with 401
    print_result("Invalid Login Block", success, response)

    return success

def test_get_current_user(token):
    """Test 8: Get Current User (Protected Endpoint)"""
    print_section("Test 8: Get Current User (Protected Endpoint)")

    if not token:
        print("❌ SKIP | No token available")
        return False

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)

    success = response.status_code == 200 and "username" in response.json()
    print_result("Get Current User", success, response)

    return success

def test_unauthorized_access():
    """Test 9: Unauthorized Access (No Token)"""
    print_section("Test 9: Unauthorized Access (Should Fail)")

    response = requests.get(f"{BASE_URL}/auth/me")
    success = response.status_code == 401  # Should fail without token
    print_result("Unauthorized Access Block", success, response)

    return success

def test_change_password(token):
    """Test 10: Change Password"""
    print_section("Test 10: Change Password")

    if not token:
        print("❌ SKIP | No token available")
        return False

    password_data = {
        "current_password": "SecurePassword123!",
        "new_password": "NewSecurePassword456!"
    }

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/auth/change-password",
        json=password_data,
        headers=headers
    )

    success = response.status_code == 200
    print_result("Change Password", success, response)

    return success

def test_login_with_new_password():
    """Test 11: Login with New Password"""
    print_section("Test 11: Login with New Password")

    login_data = {
        "username": "testuser",
        "password": "NewSecurePassword456!"
    }

    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    success = response.status_code == 200 and "access_token" in response.json()
    print_result("Login with New Password", success, response)

    return success

def test_oauth_auth_status():
    """Test 12: Get OAuth Authentication Status"""
    print_section("Test 12: Get OAuth Authentication Status")

    if not TENANT_ID:
        print("❌ SKIP | No tenant ID available")
        return False

    response = requests.get(f"{BASE_URL}/api/tenants/{TENANT_ID}/auth-status")
    success = response.status_code == 200 and "platforms" in response.json()
    print_result("OAuth Auth Status", success, response)

    return success

def run_all_tests():
    """Run all tests"""
    print("\n" + "🧪" * 35)
    print("  FACEBOOK/TIKTOK AUTOMATION - AUTHENTICATION TESTS")
    print("🧪" * 35)

    results = []
    token = None

    # Run tests in sequence
    results.append(("Health Check", test_health_check()))
    results.append(("Create Tenant", test_create_tenant()))
    results.append(("List Tenants", test_list_tenants()))
    results.append(("User Registration", test_user_registration()))
    results.append(("Duplicate Registration Block", test_duplicate_registration()))

    token = test_user_login()
    results.append(("User Login", token is not None))

    results.append(("Invalid Login Block", test_invalid_login()))
    results.append(("Get Current User", test_get_current_user(token)))
    results.append(("Unauthorized Access Block", test_unauthorized_access()))
    results.append(("Change Password", test_change_password(token)))
    results.append(("Login with New Password", test_login_with_new_password()))
    results.append(("OAuth Auth Status", test_oauth_auth_status()))

    # Print summary
    print_section("TEST SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\n📊 Results: {passed}/{total} tests passed")
    print("\nDetailed Results:")
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} | {test_name}")

    success_rate = (passed / total) * 100
    print(f"\n📈 Success Rate: {success_rate:.1f}%")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

    print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    try:
        run_all_tests()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
