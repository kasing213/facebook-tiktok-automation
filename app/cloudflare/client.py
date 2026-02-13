"""Cloudflare API client service."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import httpx
from pydantic import BaseModel

from .exceptions import (
    CloudflareAPIError,
    CloudflareAuthError,
    CloudflareNotFoundError,
    CloudflareRateLimitError,
    CloudflareConfigError,
)
from .models import CloudflareConfig, CloudflareHealthStatus

logger = logging.getLogger(__name__)


class CloudflareService:
    """Core Cloudflare API service."""

    def __init__(self, config: CloudflareConfig):
        """Initialize Cloudflare service with configuration."""
        self.config = config
        self.base_url = "https://api.cloudflare.com/client/v4"
        self._client: Optional[httpx.AsyncClient] = None
        self._rate_limit_semaphore = asyncio.Semaphore(config.max_requests_per_minute)

    async def __aenter__(self):
        """Async context manager entry."""
        await self._initialize_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _initialize_client(self):
        """Initialize HTTP client with authentication headers."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Facebook-Automation/1.0",
        }

        # Set authentication headers
        if self.config.api_token:
            headers["Authorization"] = f"Bearer {self.config.api_token}"
        elif self.config.email and self.config.api_key:
            headers["X-Auth-Email"] = self.config.email
            headers["X-Auth-Key"] = self.config.api_key
        else:
            raise CloudflareConfigError("No valid authentication method provided")

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=httpx.Timeout(self.config.request_timeout),
        )

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """Make authenticated request to Cloudflare API."""
        if not self._client:
            await self._initialize_client()

        # Rate limiting
        async with self._rate_limit_semaphore:
            try:
                url = f"{endpoint}"

                if self.config.test_mode and method in ["POST", "PUT", "PATCH", "DELETE"]:
                    logger.info(f"TEST MODE: Would {method} to {url} with data: {data}")
                    return {"success": True, "result": {"test_mode": True}, "messages": []}

                response = await self._client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                )

                return await self._handle_response(response, endpoint, retry_count)

            except httpx.TimeoutException:
                raise CloudflareAPIError(f"Request timeout for {endpoint}")
            except httpx.RequestError as e:
                raise CloudflareAPIError(f"Request failed for {endpoint}: {str(e)}")

    async def _handle_response(
        self, response: httpx.Response, endpoint: str, retry_count: int
    ) -> Dict[str, Any]:
        """Handle API response and errors."""
        try:
            data = response.json()
        except Exception:
            raise CloudflareAPIError(f"Invalid JSON response from {endpoint}")

        # Handle rate limiting
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            if retry_count < 3:
                logger.warning(f"Rate limited, retrying after {retry_after} seconds")
                await asyncio.sleep(retry_after)
                return await self._make_request("GET", endpoint, retry_count=retry_count + 1)
            else:
                raise CloudflareRateLimitError(
                    "Rate limit exceeded", retry_after=retry_after
                )

        # Handle authentication errors
        if response.status_code == 401:
            raise CloudflareAuthError("Authentication failed - check API credentials")

        # Handle not found
        if response.status_code == 404:
            raise CloudflareNotFoundError(f"Resource not found: {endpoint}")

        # Handle other client/server errors
        if response.status_code >= 400:
            error_msg = data.get("errors", [{"message": "Unknown error"}])[0].get("message")
            raise CloudflareAPIError(
                f"API error ({response.status_code}): {error_msg}",
                status_code=response.status_code,
                response=data,
            )

        # Check if API response indicates failure
        if not data.get("success", False):
            errors = data.get("errors", [])
            if errors:
                error_msg = errors[0].get("message", "Unknown API error")
                raise CloudflareAPIError(f"API returned error: {error_msg}", response=data)

        return data

    async def get_zone_info(self) -> Dict[str, Any]:
        """Get zone information."""
        endpoint = f"/zones/{self.config.zone_id}"
        response = await self._make_request("GET", endpoint)
        return response.get("result", {})

    async def list_dns_records(
        self,
        record_type: Optional[str] = None,
        name: Optional[str] = None,
        content: Optional[str] = None,
        page: int = 1,
        per_page: int = 100,
    ) -> List[Dict[str, Any]]:
        """List DNS records with optional filters."""
        endpoint = f"/zones/{self.config.zone_id}/dns_records"

        params = {"page": page, "per_page": per_page}
        if record_type:
            params["type"] = record_type
        if name:
            params["name"] = name
        if content:
            params["content"] = content

        response = await self._make_request("GET", endpoint, params=params)
        return response.get("result", [])

    async def get_dns_record(self, record_id: str) -> Dict[str, Any]:
        """Get a specific DNS record."""
        endpoint = f"/zones/{self.config.zone_id}/dns_records/{record_id}"
        response = await self._make_request("GET", endpoint)
        return response.get("result", {})

    async def create_dns_record(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new DNS record."""
        endpoint = f"/zones/{self.config.zone_id}/dns_records"
        response = await self._make_request("POST", endpoint, data=record_data)
        return response.get("result", {})

    async def update_dns_record(
        self, record_id: str, record_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing DNS record."""
        endpoint = f"/zones/{self.config.zone_id}/dns_records/{record_id}"
        response = await self._make_request("PUT", endpoint, data=record_data)
        return response.get("result", {})

    async def delete_dns_record(self, record_id: str) -> Dict[str, Any]:
        """Delete a DNS record."""
        endpoint = f"/zones/{self.config.zone_id}/dns_records/{record_id}"
        response = await self._make_request("DELETE", endpoint)
        return response.get("result", {})

    async def health_check(self) -> CloudflareHealthStatus:
        """Perform health check of Cloudflare service."""
        start_time = datetime.utcnow()
        errors = []
        zone_accessible = False
        api_accessible = False

        try:
            # Test API accessibility
            await self.get_zone_info()
            api_accessible = True
            zone_accessible = True
        except CloudflareAuthError:
            errors.append("Authentication failed")
            api_accessible = False
        except CloudflareNotFoundError:
            errors.append("Zone not found")
            api_accessible = True
            zone_accessible = False
        except Exception as e:
            errors.append(f"API error: {str(e)}")
            api_accessible = False

        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds() * 1000

        if api_accessible and zone_accessible:
            status = "healthy"
        elif api_accessible:
            status = "degraded"
        else:
            status = "unhealthy"

        return CloudflareHealthStatus(
            status=status,
            zone_accessible=zone_accessible,
            api_accessible=api_accessible,
            last_check=end_time,
            response_time_ms=response_time,
            errors=errors,
        )