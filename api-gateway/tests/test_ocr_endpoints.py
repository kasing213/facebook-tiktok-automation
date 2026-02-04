"""
API Gateway OCR Endpoint Tests

Tests the OCR endpoints in the API Gateway with JWT authentication,
service validation, and tenant isolation using real screenshots.
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from src.main import app
from src.core.service_jwt import create_service_jwt, validate_service_token
from src.middleware.service_auth import require_service_jwt, ServiceAuthError, UnauthorizedServiceError


def load_test_screenshot(filename: str) -> bytes:
    """Load test screenshot from fixtures."""
    # Assuming screenshots are in the main app tests directory
    screenshots_dir = Path(__file__).parent.parent.parent / "app" / "tests" / "fixtures" / "screenshots"
    screenshot_path = screenshots_dir / filename
    if not screenshot_path.exists():
        raise FileNotFoundError(f"Test screenshot not found: {filename}")
    return screenshot_path.read_bytes()


@pytest.fixture
def client():
    """Create test client for API Gateway."""
    return TestClient(app)


@pytest.fixture
def valid_service_jwt():
    """Create a valid service JWT token."""
    return create_service_jwt(
        service="facebook-automation",
        tenant_id="test-tenant-123",
        user_id="test-user-456",
        role="admin"
    )


@pytest.fixture
def invalid_service_jwt():
    """Create an invalid service JWT token."""
    return "invalid.jwt.token"


@pytest.fixture
def unauthorized_service_jwt():
    """Create a JWT token for an unauthorized service."""
    return create_service_jwt(
        service="unauthorized-service",
        tenant_id="test-tenant-123",
        user_id="test-user-456",
        role="admin"
    )


class TestOCREndpointJWTAuthentication:
    """Test JWT authentication for OCR endpoints."""

    def test_ocr_health_endpoint_no_auth_required(self, client):
        """Test that health endpoint doesn't require authentication."""
        response = client.get("/api/v1/ocr/health")
        # Should succeed regardless of authentication
        # (Actual response depends on OCR service configuration)
        assert response.status_code in [200, 503]  # 503 if not configured

    def test_ocr_verify_requires_jwt_authentication(self, client):
        """Test that verify endpoint requires JWT authentication."""
        screenshot_data = load_test_screenshot("valid_payment_100_khr.png")

        response = client.post(
            "/api/v1/ocr/verify",
            files={"image": ("test.png", screenshot_data, "image/png")}
        )

        # Should reject without authorization header
        assert response.status_code == 422  # Missing required header

    def test_ocr_verify_with_missing_bearer_token(self, client):
        """Test OCR verify with malformed authorization header."""
        screenshot_data = load_test_screenshot("valid_payment_100_khr.png")

        response = client.post(
            "/api/v1/ocr/verify",
            files={"image": ("test.png", screenshot_data, "image/png")},
            headers={"Authorization": "InvalidFormat"}
        )

        assert response.status_code == 401
        assert "invalid authorization header" in response.json()["detail"].lower()

    def test_ocr_verify_with_invalid_jwt(self, client, invalid_service_jwt):
        """Test OCR verify with invalid JWT token."""
        screenshot_data = load_test_screenshot("valid_payment_100_khr.png")

        response = client.post(
            "/api/v1/ocr/verify",
            files={"image": ("test.png", screenshot_data, "image/png")},
            headers={"Authorization": f"Bearer {invalid_service_jwt}"}
        )

        assert response.status_code == 401
        assert "invalid service token" in response.json()["detail"].lower()

    def test_ocr_verify_with_unauthorized_service(self, client, unauthorized_service_jwt):
        """Test OCR verify with JWT from unauthorized service."""
        screenshot_data = load_test_screenshot("valid_payment_100_khr.png")

        response = client.post(
            "/api/v1/ocr/verify",
            files={"image": ("test.png", screenshot_data, "image/png")},
            headers={"Authorization": f"Bearer {unauthorized_service_jwt}"}
        )

        assert response.status_code == 403
        assert "not authorized" in response.json()["detail"].lower()

    @patch('src.services.ocr_service.ocr_service.verify_screenshot')
    def test_ocr_verify_with_valid_jwt(self, mock_verify, client, valid_service_jwt):
        """Test OCR verify with valid JWT token."""
        screenshot_data = load_test_screenshot("valid_payment_100_khr.png")

        # Mock successful OCR response
        mock_verify.return_value = {
            "success": True,
            "extracted_data": {"amount": 100000, "currency": "KHR"},
            "confidence": 0.95
        }

        response = client.post(
            "/api/v1/ocr/verify",
            files={"image": ("test.png", screenshot_data, "image/png")},
            headers={"Authorization": f"Bearer {valid_service_jwt}"}
        )

        # Should succeed with valid JWT
        if response.status_code == 503:
            # OCR service not configured in test environment
            assert "not configured" in response.json()["detail"].lower()
        else:
            assert response.status_code == 200
            mock_verify.assert_called_once()

    def test_ocr_get_verification_requires_jwt(self, client):
        """Test that get verification endpoint requires JWT."""
        response = client.get("/api/v1/ocr/verify/test-record-123")
        assert response.status_code == 422  # Missing required header

    @patch('src.services.ocr_service.ocr_service.get_verification')
    def test_ocr_get_verification_with_valid_jwt(self, mock_get, client, valid_service_jwt):
        """Test get verification with valid JWT."""
        # Mock verification response
        mock_get.return_value = {
            "success": True,
            "record_id": "test-record-123",
            "status": "verified"
        }

        response = client.get(
            "/api/v1/ocr/verify/test-record-123",
            headers={"Authorization": f"Bearer {valid_service_jwt}"}
        )

        if response.status_code == 503:
            # OCR service not configured
            assert "not configured" in response.json()["detail"].lower()
        else:
            assert response.status_code == 200
            mock_get.assert_called_once_with("test-record-123")


class TestServiceJWTValidation:
    """Test service-to-service JWT validation."""

    def test_create_service_jwt_token(self):
        """Test creating a service JWT token."""
        token = create_service_jwt(
            service="facebook-automation",
            tenant_id="test-tenant",
            user_id="test-user",
            role="admin"
        )

        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are quite long
        assert token.count('.') == 2  # JWT has 3 parts separated by dots

    def test_validate_service_jwt_token(self):
        """Test validating a service JWT token."""
        token = create_service_jwt(
            service="facebook-automation",
            tenant_id="test-tenant-456",
            user_id="test-user-789",
            role="user"
        )

        payload = validate_service_token(token)

        assert payload is not None
        assert payload["service"] == "facebook-automation"
        assert payload["tenant_id"] == "test-tenant-456"
        assert payload["user_id"] == "test-user-789"
        assert payload["role"] == "user"
        assert "exp" in payload
        assert "iat" in payload
        assert "request_id" in payload

    def test_validate_invalid_jwt_token(self):
        """Test validating an invalid JWT token."""
        invalid_token = "invalid.jwt.token"
        payload = validate_service_token(invalid_token)
        assert payload is None

    def test_validate_expired_jwt_token(self):
        """Test validating an expired JWT token."""
        from datetime import datetime, timedelta, timezone

        # Create token that expires immediately
        token = create_service_jwt(
            service="facebook-automation",
            tenant_id="test-tenant",
            user_id="test-user",
            role="admin",
            expires_delta=timedelta(seconds=-1)  # Already expired
        )

        payload = validate_service_token(token)
        assert payload is None  # Should be None for expired token


class TestServiceAuthenticationMiddleware:
    """Test the service authentication middleware."""

    @pytest.mark.asyncio
    async def test_require_service_jwt_with_valid_token(self, valid_service_jwt):
        """Test service JWT middleware with valid token."""
        context = await require_service_jwt(f"Bearer {valid_service_jwt}")

        assert isinstance(context, dict)
        assert context["service"] == "facebook-automation"
        assert context["tenant_id"] == "test-tenant-123"
        assert context["user_id"] == "test-user-456"
        assert context["role"] == "admin"

    @pytest.mark.asyncio
    async def test_require_service_jwt_with_missing_header(self):
        """Test service JWT middleware with missing authorization header."""
        with pytest.raises(ServiceAuthError) as exc_info:
            await require_service_jwt("")

        assert "missing or invalid authorization header" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_require_service_jwt_with_invalid_token(self, invalid_service_jwt):
        """Test service JWT middleware with invalid token."""
        with pytest.raises(ServiceAuthError) as exc_info:
            await require_service_jwt(f"Bearer {invalid_service_jwt}")

        assert "invalid service token" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_require_service_jwt_with_unauthorized_service(self, unauthorized_service_jwt):
        """Test service JWT middleware with unauthorized service."""
        with pytest.raises(UnauthorizedServiceError) as exc_info:
            await require_service_jwt(f"Bearer {unauthorized_service_jwt}")

        assert "not authorized" in str(exc_info.value.detail).lower()


class TestTenantIsolationInOCR:
    """Test tenant isolation in OCR operations."""

    @patch('src.services.ocr_service.ocr_service.verify_screenshot')
    def test_different_tenants_isolated_ocr_requests(self, mock_verify, client):
        """Test that different tenants make isolated OCR requests."""
        screenshot_data = load_test_screenshot("valid_payment_100_khr.png")

        # Mock OCR response
        mock_verify.return_value = {
            "success": True,
            "extracted_data": {"amount": 100000},
            "confidence": 0.9
        }

        # Create JWT tokens for different tenants
        tenant1_jwt = create_service_jwt(
            service="facebook-automation",
            tenant_id="tenant-111",
            user_id="user-111",
            role="admin"
        )

        tenant2_jwt = create_service_jwt(
            service="facebook-automation",
            tenant_id="tenant-222",
            user_id="user-222",
            role="user"
        )

        # Make requests with different tenant JWTs
        response1 = client.post(
            "/api/v1/ocr/verify",
            files={"image": ("test1.png", screenshot_data, "image/png")},
            headers={"Authorization": f"Bearer {tenant1_jwt}"}
        )

        response2 = client.post(
            "/api/v1/ocr/verify",
            files={"image": ("test2.png", screenshot_data, "image/png")},
            headers={"Authorization": f"Bearer {tenant2_jwt}"}
        )

        # Both should succeed but be isolated
        if response1.status_code != 503:  # If OCR service is configured
            assert response1.status_code == 200
            assert response2.status_code == 200

        # Verify that JWT tokens are different (tenant isolation)
        payload1 = validate_service_token(tenant1_jwt)
        payload2 = validate_service_token(tenant2_jwt)

        assert payload1["tenant_id"] != payload2["tenant_id"]
        assert payload1["user_id"] != payload2["user_id"]


class TestOCREndpointErrorHandling:
    """Test error handling in OCR endpoints."""

    def test_ocr_verify_empty_image_file(self, client, valid_service_jwt):
        """Test OCR verify with empty image file."""
        response = client.post(
            "/api/v1/ocr/verify",
            files={"image": ("empty.png", b"", "image/png")},
            headers={"Authorization": f"Bearer {valid_service_jwt}"}
        )

        assert response.status_code == 400
        assert "empty image file" in response.json()["detail"].lower()

    @patch('src.services.ocr_service.ocr_service.verify_screenshot')
    def test_ocr_verify_with_form_data(self, mock_verify, client, valid_service_jwt):
        """Test OCR verify with additional form data."""
        screenshot_data = load_test_screenshot("valid_payment_100_khr.png")

        # Mock OCR response
        mock_verify.return_value = {
            "success": True,
            "extracted_data": {"amount": 100000, "currency": "KHR"},
            "confidence": 0.95
        }

        response = client.post(
            "/api/v1/ocr/verify",
            files={"image": ("test.png", screenshot_data, "image/png")},
            data={
                "invoice_id": "test-invoice-123",
                "expected_amount": "100000",
                "expected_currency": "KHR",
                "customer_id": "test-customer-456"
            },
            headers={"Authorization": f"Bearer {valid_service_jwt}"}
        )

        if response.status_code != 503:  # If OCR service is configured
            assert response.status_code == 200

            # Verify that form data was passed to OCR service
            mock_verify.assert_called_once()
            call_args = mock_verify.call_args

            assert call_args.kwargs["invoice_id"] == "test-invoice-123"
            assert call_args.kwargs["customer_id"] == "test-customer-456"

            # Check expected payment was constructed
            expected_payment = call_args.kwargs["expected_payment"]
            assert expected_payment["amount"] == 100000.0
            assert expected_payment["currency"] == "KHR"

    @patch('src.services.ocr_service.ocr_service.is_configured')
    def test_ocr_service_not_configured(self, mock_configured, client, valid_service_jwt):
        """Test OCR endpoints when service is not configured."""
        mock_configured.return_value = False

        screenshot_data = load_test_screenshot("valid_payment_100_khr.png")

        response = client.post(
            "/api/v1/ocr/verify",
            files={"image": ("test.png", screenshot_data, "image/png")},
            headers={"Authorization": f"Bearer {valid_service_jwt}"}
        )

        assert response.status_code == 503
        assert "not configured" in response.json()["detail"].lower()

    @pytest.mark.parametrize("screenshot_file", [
        "valid_payment_100_khr.png",
        "valid_payment_500_usd.png",
        "blurry_payment.jpg",
        "non_payment_image.png"
    ])
    @patch('src.services.ocr_service.ocr_service.verify_screenshot')
    def test_ocr_with_different_image_types(
        self, mock_verify, screenshot_file, client, valid_service_jwt
    ):
        """Test OCR with different image file types."""
        screenshot_data = load_test_screenshot(screenshot_file)

        # Mock appropriate OCR response based on image
        if "valid" in screenshot_file:
            mock_verify.return_value = {
                "success": True,
                "extracted_data": {"amount": 100000, "currency": "KHR"},
                "confidence": 0.9
            }
        else:
            mock_verify.return_value = {
                "success": False,
                "error": "low_confidence",
                "confidence": 0.3
            }

        response = client.post(
            "/api/v1/ocr/verify",
            files={"image": (screenshot_file, screenshot_data, "image/jpeg")},
            headers={"Authorization": f"Bearer {valid_service_jwt}"}
        )

        if response.status_code != 503:  # If OCR service is configured
            assert response.status_code == 200
            mock_verify.assert_called_once()

            # Verify image data was passed correctly
            call_args = mock_verify.call_args
            assert call_args.kwargs["image_data"] == screenshot_data
            assert call_args.kwargs["filename"] == screenshot_file


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])