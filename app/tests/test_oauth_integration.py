# app/tests/test_oauth_integration.py
"""
Integration tests for OAuth endpoints and their dependency injection.
"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from cryptography.fernet import Fernet

from app.main import app
from app.deps import get_db, get_token_encryptor, get_facebook_oauth, get_tiktok_oauth
from app.services import AuthService
from app.integrations.oauth import FacebookOAuth, TikTokOAuth


class TestOAuthEndpoints:
    """Test OAuth endpoints with proper dependency injection"""

    def setup_method(self):
        """Set up test environment"""
        self.client = TestClient(app)

        # Generate test encryption key
        self.test_key = Fernet.generate_key().decode()

        # Override dependencies for testing
        self.mock_db = Mock()
        self.mock_encryptor = Mock()
        self.mock_facebook_oauth = Mock(spec=FacebookOAuth)
        self.mock_tiktok_oauth = Mock(spec=TikTokOAuth)
        self.mock_auth_service = Mock(spec=AuthService)

        def mock_get_db():
            yield self.mock_db

        def mock_get_auth_service():
            return self.mock_auth_service

        app.dependency_overrides[get_db] = mock_get_db
        app.dependency_overrides[get_token_encryptor] = lambda: self.mock_encryptor
        app.dependency_overrides[get_facebook_oauth] = lambda: self.mock_facebook_oauth
        app.dependency_overrides[get_tiktok_oauth] = lambda: self.mock_tiktok_oauth

        # Import and override auth service dependency
        from app.deps import get_auth_service
        app.dependency_overrides[get_auth_service] = mock_get_auth_service

    def teardown_method(self):
        """Clean up after tests"""
        app.dependency_overrides.clear()

    def test_facebook_authorize_endpoint(self):
        """Test Facebook OAuth authorization endpoint"""
        # Setup mock
        self.mock_facebook_oauth.auth_url.return_value = "https://facebook.com/oauth/authorize?test=1"

        # Make request with follow_redirects=False to see the redirect
        response = self.client.get("/auth/facebook/authorize?tenant_id=test-tenant", follow_redirects=False)

        # Verify response (307 Temporary Redirect is also valid)
        assert response.status_code in [302, 307]  # Redirect response
        assert "facebook.com" in response.headers["location"]

        # Verify dependency injection worked
        self.mock_facebook_oauth.auth_url.assert_called_once_with("test-tenant")

    def test_tiktok_authorize_endpoint(self):
        """Test TikTok OAuth authorization endpoint"""
        # Setup mock
        self.mock_tiktok_oauth.auth_url.return_value = "https://tiktok.com/oauth/authorize?test=1"

        # Make request
        response = self.client.get("/auth/tiktok/authorize?tenant_id=test-tenant", follow_redirects=False)

        # Verify response (307 Temporary Redirect is also valid)
        assert response.status_code in [302, 307]  # Redirect response
        assert "tiktok.com" in response.headers["location"]

        # Verify dependency injection worked
        self.mock_tiktok_oauth.auth_url.assert_called_once_with("test-tenant")

    def test_oauth_status_endpoint(self):
        """Test OAuth status endpoint"""
        from app.core.models import Platform

        # Setup mocks - return empty list for tokens
        self.mock_auth_service.get_tenant_tokens.return_value = []

        # Make request
        response = self.client.get("/auth/status/test-tenant")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "tenant_id" in data
        assert "facebook" in data
        assert "tiktok" in data
        assert data["tenant_id"] == "test-tenant"

        # Verify service calls (called once for each platform)
        assert self.mock_auth_service.get_tenant_tokens.call_count == 2

    def test_facebook_callback_with_error_handling(self):
        """Test Facebook OAuth callback with error handling"""
        # Setup mock to raise exception
        self.mock_facebook_oauth.validate_state.side_effect = ValueError("Invalid state")

        # Make request
        response = self.client.get("/auth/facebook/callback?code=test&state=invalid")

        # Verify error handling
        assert response.status_code == 400
        assert "Invalid state" in response.json()["detail"]

    def test_tiktok_callback_with_error_handling(self):
        """Test TikTok OAuth callback with error handling"""
        # Setup mock to raise exception
        self.mock_tiktok_oauth.validate_state.side_effect = ValueError("Invalid state")

        # Make request
        response = self.client.get("/auth/tiktok/callback?code=test&state=invalid")

        # Verify error handling
        assert response.status_code == 400
        assert "Invalid state" in response.json()["detail"]

    def test_dependency_injection_chain(self):
        """Test that the full dependency injection chain works"""
        # This test verifies that all dependencies are properly resolved
        # by checking that the endpoints can be called without dependency errors

        # Setup mocks for authorize endpoints
        self.mock_facebook_oauth.auth_url.return_value = "https://facebook.com/test"
        self.mock_tiktok_oauth.auth_url.return_value = "https://tiktok.com/test"

        test_cases = [
            ("/auth/facebook/authorize?tenant_id=test", [302, 307]),  # Should redirect
            ("/auth/tiktok/authorize?tenant_id=test", [302, 307]),    # Should redirect
            ("/auth/status/test-tenant", [200])                      # Should return status
        ]

        for endpoint, expected_codes in test_cases:
            response = self.client.get(endpoint, follow_redirects=False)
            assert response.status_code in expected_codes, f"Unexpected status {response.status_code} for {endpoint}"
            # Most importantly, should not get dependency injection errors (500)
            assert response.status_code != 500, f"Dependency injection failed for {endpoint}"

    def test_error_logging_integration(self):
        """Test that error logging works with dependency injection"""
        # Setup mock to raise exception
        self.mock_facebook_oauth.auth_url.side_effect = Exception("Test error")

        # Make request (should log error and return 500)
        response = self.client.get("/auth/facebook/authorize?tenant_id=test")

        # Verify error response
        assert response.status_code == 500
        assert "OAuth initiation failed" in response.json()["detail"]


class TestOAuthEndpointValidation:
    """Test OAuth endpoint parameter validation"""

    def setup_method(self):
        """Set up test client"""
        self.client = TestClient(app)

    def test_missing_tenant_id_validation(self):
        """Test that missing tenant_id parameter is handled correctly"""
        response = self.client.get("/auth/facebook/authorize")

        # Should return validation error
        assert response.status_code == 422  # Unprocessable Entity
        assert "tenant_id" in response.json()["detail"][0]["loc"]

    def test_missing_callback_parameters(self):
        """Test that missing callback parameters are handled correctly"""
        # Missing code parameter
        response = self.client.get("/auth/facebook/callback?state=test")
        assert response.status_code == 422

        # Missing state parameter
        response = self.client.get("/auth/facebook/callback?code=test")
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])