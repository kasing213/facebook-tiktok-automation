# api-gateway/src/services/ocr_service.py
"""OCR Verification service for payment screenshot verification."""

import logging
import uuid
import re
import random
from typing import Dict, Any, Optional
from datetime import datetime

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


class MockOCRExtractor:
    """
    Mock OCR extractor for testing purposes.

    In production, this would be replaced with actual OCR like:
    - Google Cloud Vision
    - AWS Textract
    - Azure Computer Vision
    - Tesseract + preprocessing
    - PaddleOCR
    """

    # Common Cambodian bank patterns
    BANK_PATTERNS = {
        "aba": ["ABA", "ABA Bank", "ABA BANK"],
        "acleda": ["ACLEDA", "Acleda Bank", "ACLEDA BANK"],
        "wing": ["WING", "Wing Bank", "Wing Cambodia"],
        "true_money": ["TrueMoney", "True Money", "TRUE MONEY"],
        "bakong": ["Bakong", "BAKONG", "NBC Bakong"],
        "may_bank": ["Maybank", "MAY BANK", "MAYBANK"],
        "canadia": ["Canadia", "CANADIA", "Canadia Bank"],
        "phillip": ["Phillip Bank", "PHILLIP", "Phillip"],
    }

    # Currency patterns
    CURRENCY_PATTERNS = {
        "KHR": [r"KHR", r"៛", r"រៀល", r"Riel"],
        "USD": [r"USD", r"\$", r"US\$", r"Dollar"],
    }

    def extract_amount_from_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Extract payment information from image.

        For mock mode, we simulate realistic extraction based on image size
        and return mock data. In production, this would use real OCR.
        """
        # Get image size as a "seed" for consistent mock results
        image_size = len(image_data)

        # Simulate processing time characteristics based on image
        # In reality, larger images might have more text/data

        # Generate mock extracted data
        # In a real implementation, you would:
        # 1. Preprocess the image (deskew, enhance, etc.)
        # 2. Run OCR to extract text
        # 3. Parse the text for amounts, dates, references

        return {
            "raw_text": "[Mock OCR - Image processed]",
            "confidence": 0.0,  # Will be set based on expected payment match
            "extracted_fields": {}
        }

    def verify_payment(
        self,
        image_data: bytes,
        expected_payment: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Verify payment screenshot against expected payment.

        In mock mode, this simulates verification by assuming the payment is valid
        if expected_payment is provided, since we can't actually read the image.

        Verification checks:
        1. Amount - must match within tolerance (default 5%)
        2. Date - transaction date must be on or before due date
        3. Recipient Name - if provided, assumes match in mock mode
        4. Account Number - if provided, assumes match in mock mode

        For testing purposes:
        - If expected_payment is provided, assume high match rate
        - Generate realistic-looking extracted data based on expected values
        """
        record_id = str(uuid.uuid4())[:8]
        timestamp = datetime.utcnow().isoformat()
        today = datetime.utcnow().date()

        if not expected_payment:
            # No expected payment - just return mock extraction
            return {
                "success": True,
                "record_id": f"mock-{record_id}",
                "extracted_data": {
                    "amount": "N/A",
                    "currency": "",
                    "date": timestamp[:10],
                    "reference": f"REF-{record_id.upper()}",
                    "account": "N/A",
                    "recipient_name": "N/A"
                },
                "confidence": 0.5,
                "verification": {
                    "status": "pending",
                    "message": "No expected payment provided for comparison"
                },
                "mock_mode": True
            }

        # With expected payment, simulate verification
        expected_amount = expected_payment.get("amount", 0)
        expected_currency = expected_payment.get("currency", "KHR")
        expected_account = expected_payment.get("toAccount", "")
        expected_bank = expected_payment.get("bank", "")
        expected_recipient_name = expected_payment.get("recipientName", "")
        expected_due_date = expected_payment.get("dueDate", "")

        # Simulate OCR extraction matching the expected values
        # In reality, OCR would extract actual values from the image
        # For testing, we assume the screenshot shows the expected payment

        # Add slight variation to simulate OCR imperfection
        confidence = random.uniform(0.75, 0.95)

        # Simulate extracted amount (may have slight variation)
        extracted_amount = expected_amount

        # Format amount for display
        if expected_currency == "KHR":
            amount_str = f"{extracted_amount:,.0f}"
        else:
            amount_str = f"{extracted_amount:.2f}"

        # Simulated transaction date (in mock, we use today's date)
        transaction_date = today.isoformat()

        extracted_data = {
            "amount": amount_str,
            "currency": expected_currency,
            "date": transaction_date,
            "reference": f"TXN-{record_id.upper()}",
            "account": expected_account if expected_account else "N/A",
            "bank": expected_bank if expected_bank else "Unknown Bank",
            "recipient_name": expected_recipient_name if expected_recipient_name else "N/A"
        }

        # Determine verification status
        # In mock mode, we assume high match rate for testing
        tolerance = expected_payment.get("tolerancePercent", 5) / 100
        amount_diff = abs(extracted_amount - expected_amount) / expected_amount if expected_amount else 0

        # Initialize verification flags
        amount_match = amount_diff <= tolerance
        date_match = True
        date_warning = None
        rejection_reasons = []

        # Check due date - if payment date is after due date, flag as late
        if expected_due_date:
            try:
                # Parse due date (handles both ISO format and simple date)
                due_date_str = expected_due_date.split('T')[0] if 'T' in expected_due_date else expected_due_date
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()

                if today > due_date:
                    date_match = False
                    date_warning = f"Payment received after due date ({due_date_str})"
                    rejection_reasons.append("late_payment")
            except ValueError as e:
                logger.warning(f"Could not parse due date: {expected_due_date}, error: {e}")

        # Amount check
        if not amount_match:
            rejection_reasons.append("amount_mismatch")

        # Determine final verification status
        if rejection_reasons:
            verification_status = "rejected"
            if "late_payment" in rejection_reasons and "amount_mismatch" not in rejection_reasons:
                verification_message = f"Payment is late: {date_warning}"
            elif "amount_mismatch" in rejection_reasons:
                verification_message = f"Amount mismatch: expected {expected_amount}, found {extracted_amount}"
                if date_warning:
                    verification_message += f". Also: {date_warning}"
            else:
                verification_message = ", ".join(rejection_reasons)
        else:
            verification_status = "verified"
            verification_message = "Payment verified successfully"

        return {
            "success": True,
            "record_id": f"mock-{record_id}",
            "extracted_data": extracted_data,
            "confidence": confidence,
            "verification": {
                "status": verification_status,
                "message": verification_message,
                "rejectionReason": ", ".join(rejection_reasons) if rejection_reasons else None,
                "expected": {
                    "amount": expected_amount,
                    "currency": expected_currency,
                    "account": expected_account,
                    "recipient_name": expected_recipient_name,
                    "due_date": expected_due_date
                },
                "matched": {
                    "amount": amount_match,
                    "currency": True,
                    "account": bool(expected_account),
                    "recipient_name": bool(expected_recipient_name),
                    "date": date_match
                },
                "date_warning": date_warning
            },
            "mock_mode": True,
            "timestamp": timestamp
        }


class OCRService:
    """Service for interacting with external OCR verification API."""

    def __init__(self):
        self.base_url = settings.OCR_API_URL.rstrip("/") if settings.OCR_API_URL else ""
        self.api_key = settings.OCR_API_KEY
        self.mock_mode = settings.OCR_MOCK_MODE
        self.timeout = 60.0  # OCR can take time
        self.mock_extractor = MockOCRExtractor()

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for OCR API requests."""
        return {"X-API-Key": self.api_key}

    def is_configured(self) -> bool:
        """Check if OCR service is configured (external API or mock mode)."""
        return self.mock_mode or bool(self.base_url and self.api_key)

    def is_mock_mode(self) -> bool:
        """Check if running in mock mode."""
        return self.mock_mode or not (self.base_url and self.api_key)

    async def health_check(self) -> Dict[str, Any]:
        """Check OCR service health."""
        if self.is_mock_mode():
            return {
                "status": "healthy",
                "mode": "mock",
                "message": "Mock OCR service active (for testing)"
            }

        if not self.base_url or not self.api_key:
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
                    "mode": "external",
                    "ocr_service": response.json()
                }
        except httpx.HTTPStatusError as e:
            logger.error(f"OCR health check HTTP error: {e}")
            return {"status": "error", "message": f"HTTP {e.response.status_code}"}
        except httpx.RequestError as e:
            logger.error(f"OCR health check connection error: {e}")
            return {"status": "error", "message": f"Connection failed: {str(e)}"}

    async def get_status(self) -> Dict[str, Any]:
        """Get detailed OCR service status."""
        if self.is_mock_mode():
            return {
                "status": "active",
                "mode": "mock",
                "message": "Mock OCR service for testing",
                "capabilities": [
                    "payment_verification",
                    "amount_extraction",
                    "currency_detection"
                ]
            }

        if not self.base_url or not self.api_key:
            return {
                "status": "not_configured",
                "message": "OCR_API_URL or OCR_API_KEY not set"
            }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/status",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"OCR status check error: {e}")
            return {"status": "error", "message": str(e)}

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
        # Use mock mode if enabled or external API not configured
        if self.is_mock_mode():
            logger.info(f"Using mock OCR for verification (invoice: {invoice_id})")
            result = self.mock_extractor.verify_payment(
                image_data=image_data,
                expected_payment=expected_payment
            )
            # Add additional context
            result["invoice_id"] = invoice_id
            result["customer_id"] = customer_id
            return result

        # External API mode
        if not self.base_url or not self.api_key:
            return {
                "success": False,
                "error": "not_configured",
                "message": "OCR service not configured"
            }

        try:
            files = {"image": (filename, image_data)}
            data = {}

            if invoice_id:
                data["invoice_id"] = invoice_id

            if expected_payment:
                import json
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
            error_detail = e.response.json() if e.response.content else {}
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
        if self.is_mock_mode():
            # Mock mode - return mock result
            if record_id.startswith("mock-"):
                return {
                    "success": True,
                    "record_id": record_id,
                    "status": "completed",
                    "mode": "mock"
                }
            return {
                "success": False,
                "error": "not_found",
                "message": f"Record {record_id} not found in mock mode"
            }

        if not self.base_url or not self.api_key:
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
ocr_service = OCRService()
