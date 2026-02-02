# app/services/external_invoice_client.py
"""
External Invoice Service Client with JWT Authentication.

This client handles communication with external invoice services (like general-invoice)
using JWT tokens for authentication and proper tenant isolation.
"""
import logging
from typing import Optional, List, Dict, Any
import httpx
from app.core.config import get_settings
from app.core.external_jwt import create_invoice_api_headers, create_general_invoice_client_token

logger = logging.getLogger(__name__)


class ExternalInvoiceClient:
    """
    Client for external invoice service with JWT authentication.
    """

    def __init__(self, timeout: float = 30.0):
        """
        Initialize the external invoice client.

        Args:
            timeout: HTTP request timeout in seconds
        """
        self.settings = get_settings()
        self.timeout = timeout
        self.base_url = self.settings.INVOICE_API_URL.rstrip("/") if self.settings.INVOICE_API_URL else None

    def _get_headers(self, tenant_id: str, user_id: Optional[str] = None) -> Dict[str, str]:
        """Get headers with JWT authentication for API requests."""
        headers = create_invoice_api_headers(tenant_id=tenant_id, user_id=user_id)

        # Add API key if configured
        if self.settings.INVOICE_API_KEY.get_secret_value():
            headers["X-API-Key"] = self.settings.INVOICE_API_KEY.get_secret_value()

        return headers

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        tenant_id: str,
        user_id: Optional[str] = None,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Make an authenticated HTTP request to the external service.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            tenant_id: Tenant ID for authentication
            user_id: Optional user ID
            data: Request body data
            params: Query parameters

        Returns:
            Response data or None on failure
        """
        if not self.base_url:
            logger.warning("INVOICE_API_URL not configured, using mock service")
            return None

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers(tenant_id, user_id)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {method} {url}: {e.response.text}")
            return None
        except httpx.TimeoutException:
            logger.error(f"Timeout for {method} {url}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {method} {url}: {e}")
            return None

    # Customer operations
    async def list_customers(
        self,
        tenant_id: str,
        limit: int = 50,
        skip: int = 0,
        search: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Dict]:
        """List customers with JWT authentication."""
        params = {"limit": limit, "skip": skip}
        if search:
            params["search"] = search

        result = await self._make_request(
            method="GET",
            endpoint="/customers",
            tenant_id=tenant_id,
            user_id=user_id,
            params=params
        )
        return result.get("customers", []) if result else []

    async def get_customer(
        self,
        tenant_id: str,
        customer_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Dict]:
        """Get a single customer by ID."""
        result = await self._make_request(
            method="GET",
            endpoint=f"/customers/{customer_id}",
            tenant_id=tenant_id,
            user_id=user_id
        )
        return result

    async def create_customer(
        self,
        tenant_id: str,
        data: Dict,
        user_id: Optional[str] = None
    ) -> Optional[Dict]:
        """Create a new customer."""
        result = await self._make_request(
            method="POST",
            endpoint="/customers",
            tenant_id=tenant_id,
            user_id=user_id,
            data=data
        )
        return result

    async def update_customer(
        self,
        tenant_id: str,
        customer_id: str,
        data: Dict,
        user_id: Optional[str] = None
    ) -> Optional[Dict]:
        """Update an existing customer."""
        result = await self._make_request(
            method="PUT",
            endpoint=f"/customers/{customer_id}",
            tenant_id=tenant_id,
            user_id=user_id,
            data=data
        )
        return result

    async def delete_customer(
        self,
        tenant_id: str,
        customer_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """Delete a customer."""
        result = await self._make_request(
            method="DELETE",
            endpoint=f"/customers/{customer_id}",
            tenant_id=tenant_id,
            user_id=user_id
        )
        return result is not None

    # Invoice operations
    async def list_invoices(
        self,
        tenant_id: str,
        limit: int = 50,
        skip: int = 0,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Dict]:
        """List invoices with JWT authentication."""
        params = {"limit": limit, "skip": skip}
        if customer_id:
            params["customer_id"] = customer_id
        if status:
            params["status"] = status

        result = await self._make_request(
            method="GET",
            endpoint="/invoices",
            tenant_id=tenant_id,
            user_id=user_id,
            params=params
        )
        return result.get("invoices", []) if result else []

    async def get_invoice(
        self,
        tenant_id: str,
        invoice_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Dict]:
        """Get a single invoice by ID."""
        result = await self._make_request(
            method="GET",
            endpoint=f"/invoices/{invoice_id}",
            tenant_id=tenant_id,
            user_id=user_id
        )
        return result

    async def create_invoice(
        self,
        tenant_id: str,
        data: Dict,
        user_id: Optional[str] = None
    ) -> Optional[Dict]:
        """Create a new invoice."""
        result = await self._make_request(
            method="POST",
            endpoint="/invoices",
            tenant_id=tenant_id,
            user_id=user_id,
            data=data
        )
        return result

    async def update_invoice(
        self,
        tenant_id: str,
        invoice_id: str,
        data: Dict,
        user_id: Optional[str] = None
    ) -> Optional[Dict]:
        """Update an existing invoice."""
        result = await self._make_request(
            method="PUT",
            endpoint=f"/invoices/{invoice_id}",
            tenant_id=tenant_id,
            user_id=user_id,
            data=data
        )
        return result

    async def delete_invoice(
        self,
        tenant_id: str,
        invoice_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """Delete an invoice."""
        result = await self._make_request(
            method="DELETE",
            endpoint=f"/invoices/{invoice_id}",
            tenant_id=tenant_id,
            user_id=user_id
        )
        return result is not None

    async def verify_invoice(
        self,
        tenant_id: str,
        invoice_id: str,
        data: Dict,
        user_id: Optional[str] = None
    ) -> Optional[Dict]:
        """Update verification status of an invoice."""
        result = await self._make_request(
            method="POST",
            endpoint=f"/invoices/{invoice_id}/verify",
            tenant_id=tenant_id,
            user_id=user_id,
            data=data
        )
        return result

    # PDF and Export operations
    async def generate_pdf(
        self,
        tenant_id: str,
        invoice_id: str,
        user_id: Optional[str] = None
    ) -> Optional[bytes]:
        """Generate PDF for an invoice."""
        if not self.base_url:
            return None

        url = f"{self.base_url}/invoices/{invoice_id}/pdf"
        headers = self._get_headers(tenant_id, user_id)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.content

        except Exception as e:
            logger.error(f"PDF generation failed for invoice {invoice_id}: {e}")
            return None

    async def export_invoices(
        self,
        tenant_id: str,
        format: str = "csv",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Optional[bytes]:
        """Export invoices to CSV or Excel format."""
        params = {"format": format}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        if not self.base_url:
            return None

        url = f"{self.base_url}/invoices/export"
        headers = self._get_headers(tenant_id, user_id)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                return response.content

        except Exception as e:
            logger.error(f"Export failed for tenant {tenant_id}: {e}")
            return None

    # Statistics
    async def get_stats(
        self,
        tenant_id: str,
        user_id: Optional[str] = None
    ) -> Dict:
        """Get invoice statistics."""
        result = await self._make_request(
            method="GET",
            endpoint="/stats",
            tenant_id=tenant_id,
            user_id=user_id
        )
        return result or {}

    # Health check
    async def health_check(self) -> bool:
        """Check if the external service is healthy."""
        if not self.base_url:
            return False

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False

    def get_client_token(self, tenant_id: str) -> str:
        """
        Get a JWT token for client-side usage (e.g., for JavaScript clients).

        Args:
            tenant_id: Tenant ID

        Returns:
            JWT token string
        """
        return create_general_invoice_client_token(tenant_id)


# Global client instance
external_invoice_client = ExternalInvoiceClient()