# app/services/ocr_service.py
"""OCR Verification service for payment screenshot verification."""

import logging
from typing import Dict, Any, Optional
import json

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class OCRService:
    """Service for interacting with external OCR verification API."""

    def __init__(self):
        settings = get_settings()
        self.base_url = settings.OCR_API_URL.rstrip("/") if settings.OCR_API_URL else ""
        self.api_key = settings.OCR_API_KEY.get_secret_value() if settings.OCR_API_KEY else ""
        self.timeout = 60.0  # OCR can take time

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for OCR API requests."""
        return {"X-API-Key": self.api_key}

    def is_configured(self) -> bool:
        """Check if OCR service is configured."""
        return bool(self.base_url and self.api_key)

    async def health_check(self) -> Dict[str, Any]:
        """Check OCR service health."""
        if not self.is_configured():
            return {
                "status": "not_configured",
                "message": "OCR_API_URL or OCR_API_KEY not set"
            }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/health",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return {
                    "status": "healthy",
                    "ocr_service": response.json()
                }
        except httpx.HTTPStatusError as e:
            logger.error(f"OCR health check HTTP error: {e}")
            return {"status": "error", "message": f"HTTP {e.response.status_code}"}
        except httpx.RequestError as e:
            logger.error(f"OCR health check connection error: {e}")
            return {"status": "error", "message": f"Connection failed: {str(e)}"}

    async def verify_screenshot(
        self,
        image_data: bytes,
        filename: str = "screenshot.jpg",
        invoice_id: Optional[str] = None,
        expected_payment: Optional[Dict[str, Any]] = None,
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify a payment screenshot using OCR service.

        Args:
            image_data: Raw image bytes
            filename: Original filename
            invoice_id: Optional invoice ID to lookup expected payment
            expected_payment: Optional expected payment details
            customer_id: Optional customer reference

        Returns:
            Verification result from OCR service
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "not_configured",
                "message": "OCR service not configured"
            }

        try:
            files = {"image": (filename, image_data, "image/jpeg")}
            data = {}

            if invoice_id:
                data["invoice_id"] = invoice_id

            if expected_payment:
                data["expectedPayment"] = json.dumps(expected_payment)

            if customer_id:
                data["customer_id"] = customer_id

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/verify",
                    headers=self._get_headers(),
                    files=files,
                    data=data if data else None
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"OCR verify HTTP error: {e}")
            try:
                error_detail = e.response.json()
            except Exception:
                error_detail = {"message": str(e)}
            return {
                "success": False,
                "error": "http_error",
                "status_code": e.response.status_code,
                "message": error_detail.get("message", str(e))
            }
        except httpx.RequestError as e:
            logger.error(f"OCR verify connection error: {e}")
            return {
                "success": False,
                "error": "connection_error",
                "message": f"Failed to connect to OCR service: {str(e)}"
            }
        except Exception as e:
            logger.error(f"OCR verify unexpected error: {e}")
            return {
                "success": False,
                "error": "unexpected_error",
                "message": str(e)
            }

    async def get_verification(self, record_id: str) -> Dict[str, Any]:
        """
        Get verification result by record ID.

        Args:
            record_id: The verification record ID

        Returns:
            Verification result
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "not_configured",
                "message": "OCR service not configured"
            }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/verify/{record_id}",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"OCR get verification HTTP error: {e}")
            return {
                "success": False,
                "error": "http_error",
                "status_code": e.response.status_code,
                "message": str(e)
            }
        except httpx.RequestError as e:
            logger.error(f"OCR get verification connection error: {e}")
            return {
                "success": False,
                "error": "connection_error",
                "message": str(e)
            }


# Global service instance
def get_ocr_service() -> OCRService:
    """Get OCR service instance."""
    return OCRService()
