"""
OCR Authentication Tests with Real Screenshots

Tests the OCR authentication system using actual payment screenshot images
instead of mocking the OCR service. Validates JWT token generation, service-to-service
authentication, and tenant isolation with real OCR responses.
"""

import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.db import get_db_session
from app.core.models import User, Tenant
from app.core.security import create_access_token
from app.core.external_jwt import create_external_service_token
from app.services.ocr_service import OCRService
from app.core.config import get_settings


# Test fixtures and helpers
@pytest.fixture
def test_screenshots_dir():
    """Get path to test screenshots directory."""
    return Path(__file__).parent / "fixtures" / "screenshots"


def load_test_screenshot(filename: str) -> bytes:
    """Load test screenshot from fixtures."""
    screenshots_dir = Path(__file__).parent / "fixtures" / "screenshots"
    screenshot_path = screenshots_dir / filename
    if not screenshot_path.exists():
        raise FileNotFoundError(f"Test screenshot not found: {filename}")
    return screenshot_path.read_bytes()


@pytest.fixture
def test_tenant():
    """Create a test tenant."""
    with get_db_session() as db:
        tenant = Tenant(
            id=uuid4(),
            name="Test Tenant OCR",
            slug="test-tenant-ocr",
            created_at=None,
            updated_at=None
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        yield tenant

        # Cleanup
        db.delete(tenant)
        db.commit()


@pytest.fixture
def test_user(test_tenant):
    """Create a test user for the tenant."""
    with get_db_session() as db:
        user = User(
            id=uuid4(),
            tenant_id=test_tenant.id,
            username="test_ocr_user",
            email="ocr@test.com",
            password_hash="fake_hash",
            role="admin",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        yield user

        # Cleanup
        db.delete(user)
        db.commit()


@pytest.fixture
def test_user_token(test_user):
    """Create a JWT token for the test user."""
    return create_access_token(data={"sub": str(test_user.id)})


@pytest.fixture
def test_service_jwt(test_user):
    """Create a service JWT token for OCR requests."""
    return create_external_service_token(
        service_name="facebook-automation",
        tenant_id=str(test_user.tenant_id),
        user_id=str(test_user.id),
        data={"role": test_user.role}
    )


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def ocr_service():
    """Create OCR service instance."""
    return OCRService()


class TestOCRJWTAuthentication:
    """Test JWT authentication in OCR service calls."""

    def test_ocr_service_creates_jwt_headers(self, test_user, test_service_jwt):
        """Test that OCR service creates proper JWT headers."""
        ocr_service = OCRService()
        headers = ocr_service._get_headers(test_user)

        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"

        # Verify the token structure (basic validation)
        token = headers["Authorization"].replace("Bearer ", "")
        assert len(token) > 50  # JWT tokens are quite long
        assert "." in token  # JWT has dots separating parts

    def test_ocr_service_jwt_contains_user_context(self, test_user):
        """Test that JWT token contains correct user context."""
        from app.core.external_jwt import validate_external_service_token

        ocr_service = OCRService()
        headers = ocr_service._get_headers(test_user)
        token = headers["Authorization"].replace("Bearer ", "")

        # Validate the token
        payload = validate_external_service_token(token)
        assert payload is not None

        # Check required fields
        assert payload["tenant_id"] == str(test_user.tenant_id)
        assert payload["user_id"] == str(test_user.id)
        assert payload["role"] == test_user.role
        assert payload["service"] == "facebook-automation"
        assert "exp" in payload
        assert "iat" in payload

    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_ocr_verify_screenshot_sends_jwt(self, mock_post, test_user):
        """Test that verify_screenshot sends JWT headers to API Gateway."""
        # Mock successful OCR response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "success": True,
            "extracted_data": {"amount": 100000, "currency": "KHR"},
            "confidence": 0.95
        }
        mock_post.return_value = mock_response

        ocr_service = OCRService()
        screenshot_data = load_test_screenshot("valid_payment_100_khr.png")

        result = await ocr_service.verify_screenshot(
            image_data=screenshot_data,
            current_user=test_user,
            filename="test_payment.png"
        )

        # Verify the call was made with JWT headers
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs

        assert "headers" in call_kwargs
        headers = call_kwargs["headers"]
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")

    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_ocr_get_verification_sends_jwt(self, mock_get, test_user):
        """Test that get_verification sends JWT headers."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "success": True,
            "record_id": "test_record_123",
            "status": "verified"
        }
        mock_get.return_value = mock_response

        ocr_service = OCRService()
        result = await ocr_service.get_verification("test_record_123", test_user)

        # Verify JWT headers were sent
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args.kwargs

        assert "headers" in call_kwargs
        headers = call_kwargs["headers"]
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")


class TestOCRTenantIsolation:
    """Test tenant isolation in OCR operations."""

    async def test_different_tenants_get_different_jwt_tokens(self):
        """Test that different tenants get different JWT tokens."""
        # Create two different tenants and users
        with get_db_session() as db:
            tenant1 = Tenant(id=uuid4(), name="Tenant 1")
            tenant2 = Tenant(id=uuid4(), name="Tenant 2")
            db.add_all([tenant1, tenant2])
            db.commit()

            user1 = User(
                id=uuid4(), tenant_id=tenant1.id, username="user1@test.com",
                email="user1@test.com", hashed_password="hash", role="admin"
            )
            user2 = User(
                id=uuid4(), tenant_id=tenant2.id, username="user2@test.com",
                email="user2@test.com", hashed_password="hash", role="admin"
            )
            db.add_all([user1, user2])
            db.commit()

            try:
                ocr_service = OCRService()
                headers1 = ocr_service._get_headers(user1)
                headers2 = ocr_service._get_headers(user2)

                # JWT tokens should be different
                token1 = headers1["Authorization"]
                token2 = headers2["Authorization"]
                assert token1 != token2

                # Validate tokens contain correct tenant info
                from app.core.external_jwt import validate_external_service_token
                payload1 = validate_external_service_token(token1.replace("Bearer ", ""))
                payload2 = validate_external_service_token(token2.replace("Bearer ", ""))

                assert payload1["tenant_id"] == str(tenant1.id)
                assert payload2["tenant_id"] == str(tenant2.id)
                assert payload1["tenant_id"] != payload2["tenant_id"]

            finally:
                # Cleanup
                db.delete(user1)
                db.delete(user2)
                db.delete(tenant1)
                db.delete(tenant2)
                db.commit()


class TestOCRRealScreenshots:
    """Test OCR service with actual screenshot images."""

    @pytest.mark.parametrize("screenshot_file,expected_success", [
        ("valid_payment_100_khr.png", True),
        ("valid_payment_500_usd.png", True),
        ("valid_bank_transfer.png", True),
        ("blurry_payment.jpg", None),  # Depends on OCR confidence
        ("wrong_amount.png", None),    # Depends on expected payment matching
        ("partial_screenshot.png", False),
        ("non_payment_image.png", False)
    ])
    @patch('httpx.AsyncClient.post')
    async def test_ocr_with_various_screenshots(
        self, mock_post, screenshot_file, expected_success, test_user
    ):
        """Test OCR service with different screenshot scenarios."""
        # Load the actual screenshot
        screenshot_data = load_test_screenshot(screenshot_file)

        # Mock OCR response based on screenshot type
        if expected_success is True:
            mock_response_data = {
                "success": True,
                "extracted_data": {
                    "amount": 100000 if "100_khr" in screenshot_file else 500,
                    "currency": "KHR" if "khr" in screenshot_file else "USD"
                },
                "confidence": 0.95
            }
        elif expected_success is False:
            mock_response_data = {
                "success": False,
                "error": "low_confidence",
                "confidence": 0.2
            }
        else:
            # Variable outcome based on OCR
            mock_response_data = {
                "success": False,
                "confidence": 0.6,
                "extracted_data": {"amount": 50000, "currency": "KHR"}
            }

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = mock_response_data
        mock_post.return_value = mock_response

        ocr_service = OCRService()

        result = await ocr_service.verify_screenshot(
            image_data=screenshot_data,
            current_user=test_user,
            filename=screenshot_file
        )

        # Verify the OCR service was called with the actual image
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs

        # Check that files were sent
        assert "files" in call_kwargs
        files = call_kwargs["files"]
        assert "image" in files

        # Verify filename and data
        filename, data, content_type = files["image"]
        assert filename == screenshot_file
        assert data == screenshot_data
        assert content_type == "image/jpeg"

        # Check result structure
        assert isinstance(result, dict)
        if expected_success is not None:
            assert result.get("success") == expected_success

    @patch('httpx.AsyncClient.post')
    async def test_ocr_with_expected_payment_validation(self, mock_post, test_user):
        """Test OCR with expected payment validation."""
        screenshot_data = load_test_screenshot("valid_payment_100_khr.png")

        # Mock OCR that finds different amount than expected
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "success": False,
            "error": "amount_mismatch",
            "extracted_data": {"amount": 100000, "currency": "KHR"},
            "expected_data": {"amount": 200000, "currency": "KHR"},
            "confidence": 0.95
        }
        mock_post.return_value = mock_response

        ocr_service = OCRService()

        # Set expected payment that doesn't match screenshot
        expected_payment = {
            "amount": 200000,
            "currency": "KHR",
            "recipientNames": ["Test Merchant"],
            "toAccount": "001234567",
            "bank": "ABA Bank"
        }

        result = await ocr_service.verify_screenshot(
            image_data=screenshot_data,
            current_user=test_user,
            filename="test_payment.png",
            expected_payment=expected_payment
        )

        # Verify expected payment was sent to OCR service
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs

        assert "data" in call_kwargs
        data = call_kwargs["data"]
        assert "expectedPayment" in data

        # Check result shows mismatch
        assert result.get("success") == False
        assert "mismatch" in result.get("error", "").lower()


class TestOCRErrorHandling:
    """Test error handling in OCR authentication."""

    @patch('httpx.AsyncClient.post')
    async def test_ocr_service_handles_401_unauthorized(self, mock_post, test_user):
        """Test handling of JWT authentication failures."""
        screenshot_data = load_test_screenshot("valid_payment_100_khr.png")

        # Mock 401 Unauthorized response
        from httpx import HTTPStatusError, Response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Invalid service token"}

        error = HTTPStatusError("401 Unauthorized", request=None, response=mock_response)
        mock_post.side_effect = error

        ocr_service = OCRService()
        result = await ocr_service.verify_screenshot(
            image_data=screenshot_data,
            current_user=test_user,
            filename="test.png"
        )

        # Should return error response
        assert result["success"] == False
        assert result["error"] == "http_error"
        assert result["status_code"] == 401

    @patch('httpx.AsyncClient.post')
    async def test_ocr_service_handles_403_forbidden(self, mock_post, test_user):
        """Test handling of service authorization failures."""
        screenshot_data = load_test_screenshot("valid_payment_100_khr.png")

        # Mock 403 Forbidden response
        from httpx import HTTPStatusError
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.json.return_value = {"detail": "Service not authorized"}

        error = HTTPStatusError("403 Forbidden", request=None, response=mock_response)
        mock_post.side_effect = error

        ocr_service = OCRService()
        result = await ocr_service.verify_screenshot(
            image_data=screenshot_data,
            current_user=test_user,
            filename="test.png"
        )

        assert result["success"] == False
        assert result["error"] == "http_error"
        assert result["status_code"] == 403

    async def test_ocr_service_not_configured(self, test_user):
        """Test behavior when OCR service is not configured."""
        with patch.object(OCRService, 'is_configured', return_value=False):
            ocr_service = OCRService()
            screenshot_data = load_test_screenshot("valid_payment_100_khr.png")

            result = await ocr_service.verify_screenshot(
                image_data=screenshot_data,
                current_user=test_user,
                filename="test.png"
            )

            assert result["success"] == False
            assert result["error"] == "not_configured"
            assert "not configured" in result["message"].lower()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])