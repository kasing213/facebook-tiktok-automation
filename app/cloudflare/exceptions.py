"""Cloudflare integration exceptions."""

from typing import Optional, Dict, Any


class CloudflareError(Exception):
    """Base exception for Cloudflare integration errors."""

    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class CloudflareAPIError(CloudflareError):
    """Exception for Cloudflare API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response or {}


class CloudflareAuthError(CloudflareError):
    """Exception for Cloudflare authentication errors."""
    pass


class CloudflareNotFoundError(CloudflareError):
    """Exception for Cloudflare resource not found errors."""
    pass


class CloudflareRateLimitError(CloudflareError):
    """Exception for Cloudflare rate limit errors."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class CloudflareConfigError(CloudflareError):
    """Exception for Cloudflare configuration errors."""
    pass


class CloudflareValidationError(CloudflareError):
    """Exception for Cloudflare data validation errors."""
    pass