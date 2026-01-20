#!/usr/bin/env python3
"""
Quick test script to verify account lockout functionality.
"""
import requests
import time
import sys

# Configuration
API_BASE = "http://localhost:8000"
TEST_EMAIL = "test@example.com"
WRONG_PASSWORD = "wrong_password"

def test_account_lockout():
    print("🔒 Testing Account Lockout System")
    print("=" * 50)

    login_url = f"{API_BASE}/auth/login"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    print(f"Target: {login_url}")
    print(f"Testing with email: {TEST_EMAIL}")
    print(f"Using wrong password: {WRONG_PASSWORD}")
    print()

    # Test failed login attempts
    for attempt in range(1, 8):  # Try 7 times (should lock after 5)
        print(f"Attempt {attempt}: ", end="", flush=True)

        data = {
            "username": TEST_EMAIL,
            "password": WRONG_PASSWORD
        }

        try:
            response = requests.post(login_url, data=data, headers=headers, timeout=10)

            if response.status_code == 401:
                print("❌ Failed (expected)")
            elif response.status_code == 423:
                print("🔒 LOCKED!")
                print(f"   Response: {response.json()}")
                break
            else:
                print(f"⚠️  Unexpected status: {response.status_code}")
                print(f"   Response: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"❗ Request failed: {e}")
            print("   Make sure the server is running on http://localhost:8000")
            return False

        # Small delay between attempts
        time.sleep(0.5)

    print()
    print("✅ Account lockout test completed!")
    print("   - First 4 attempts should return 401 (Unauthorized)")
    print("   - 5th attempt should trigger lockout and return 423 (Locked)")
    return True

def test_server_connection():
    """Test if the server is running"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            return True
    except requests.exceptions.RequestException:
        pass

    print("❌ Server is not running or not accessible")
    print("   Please start the server with: uvicorn app.main:app --reload")
    return False

if __name__ == "__main__":
    print("🚀 Account Lockout Test Script")
    print()

    if not test_server_connection():
        sys.exit(1)

    test_account_lockout()