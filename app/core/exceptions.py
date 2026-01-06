# app/core/exceptions.py
"""
Custom exceptions with plain English error messages for better user experience.

All exceptions in this module provide:
- Clear, user-friendly error messages
- Appropriate HTTP status codes
- Detailed logging information
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class BaseControlError(HTTPException):
    """Base exception for all control-related errors"""

    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.details = details or {}
        super().__init__(
            status_code=status_code,
            detail={
                "error": error_code,
                "message": message,
                "details": self.details
            }
        )


# =============================================================================
# IP Access Control Errors
# =============================================================================

class IPAccessError(BaseControlError):
    """Base class for IP access control errors"""
    pass


class IPAlreadyWhitelisted(IPAccessError):
    """Raised when trying to whitelist an IP that's already whitelisted"""

    def __init__(self, ip_address: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=f"The IP address {ip_address} is already on the whitelist. No changes were made.",
            error_code="IP_ALREADY_WHITELISTED",
            details={"ip_address": ip_address}
        )


class IPAlreadyBlacklisted(IPAccessError):
    """Raised when trying to blacklist an IP that's already blacklisted"""

    def __init__(self, ip_address: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=f"The IP address {ip_address} is already blocked. No changes were made.",
            error_code="IP_ALREADY_BLACKLISTED",
            details={"ip_address": ip_address}
        )


class IPRuleNotFound(IPAccessError):
    """Raised when an IP rule doesn't exist"""

    def __init__(self, ip_address: str, rule_type: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=f"No active {rule_type} rule was found for IP address {ip_address}. The rule may have already been removed or expired.",
            error_code="IP_RULE_NOT_FOUND",
            details={"ip_address": ip_address, "rule_type": rule_type}
        )


class IPNotBanned(IPAccessError):
    """Raised when trying to unban an IP that's not banned"""

    def __init__(self, ip_address: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=f"The IP address {ip_address} is not currently banned. There's nothing to unban.",
            error_code="IP_NOT_BANNED",
            details={"ip_address": ip_address}
        )


class InvalidIPAddress(IPAccessError):
    """Raised when an invalid IP address format is provided"""

    def __init__(self, ip_address: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"The IP address '{ip_address}' is not valid. Please provide a valid IPv4 (e.g., 192.168.1.1) or IPv6 address.",
            error_code="INVALID_IP_ADDRESS",
            details={"ip_address": ip_address}
        )


class IPRuleCreationFailed(IPAccessError):
    """Raised when IP rule creation fails"""

    def __init__(self, ip_address: str, reason: str = "Unknown error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"We couldn't create the IP rule for {ip_address}. Please try again or contact support if the problem persists.",
            error_code="IP_RULE_CREATION_FAILED",
            details={"ip_address": ip_address, "reason": reason}
        )


# =============================================================================
# Rate Limit Control Errors
# =============================================================================

class RateLimitError(BaseControlError):
    """Base class for rate limit errors"""
    pass


class RateLimitExceeded(RateLimitError):
    """Raised when rate limit is exceeded"""

    def __init__(self, ip_address: str, endpoint: str, retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message=f"You've made too many requests. Please wait {retry_after} seconds before trying again.",
            error_code="RATE_LIMIT_EXCEEDED",
            details={
                "ip_address": ip_address,
                "endpoint": endpoint,
                "retry_after_seconds": retry_after
            }
        )


class IPAutoBanned(RateLimitError):
    """Raised when an IP has been automatically banned due to violations"""

    def __init__(self, ip_address: str, violation_count: int, ban_duration_hours: int = 24):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=f"Your IP address has been temporarily blocked due to {violation_count} rate limit violations. The block will be lifted in approximately {ban_duration_hours} hours.",
            error_code="IP_AUTO_BANNED",
            details={
                "ip_address": ip_address,
                "violation_count": violation_count,
                "ban_duration_hours": ban_duration_hours
            }
        )


class ViolationRecordFailed(RateLimitError):
    """Raised when recording a rate limit violation fails"""

    def __init__(self, ip_address: str, endpoint: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="We encountered an issue while processing your request. Please try again.",
            error_code="VIOLATION_RECORD_FAILED",
            details={"ip_address": ip_address, "endpoint": endpoint}
        )


# =============================================================================
# OAuth Token Control Errors
# =============================================================================

class OAuthError(BaseControlError):
    """Base class for OAuth errors"""
    pass


class OAuthInitiationFailed(OAuthError):
    """Raised when OAuth flow initialization fails"""

    def __init__(self, platform: str, reason: str = "Unknown error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"We couldn't start the {platform} authorization process. Please try again or check if your {platform} app settings are correct.",
            error_code="OAUTH_INITIATION_FAILED",
            details={"platform": platform, "reason": reason}
        )


class OAuthStateMismatch(OAuthError):
    """Raised when OAuth state validation fails"""

    def __init__(self, platform: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"The {platform} authorization session has expired or is invalid. Please start the authorization process again.",
            error_code="OAUTH_STATE_MISMATCH",
            details={"platform": platform}
        )


class OAuthCodeExchangeFailed(OAuthError):
    """Raised when exchanging OAuth code for tokens fails"""

    def __init__(self, platform: str, reason: str = "Unknown error"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"We couldn't complete the {platform} authorization. The authorization code may have expired. Please try connecting again.",
            error_code="OAUTH_CODE_EXCHANGE_FAILED",
            details={"platform": platform, "reason": reason}
        )


class TokenNotFound(OAuthError):
    """Raised when a token doesn't exist"""

    def __init__(self, token_id: str, platform: str = "social media"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=f"The {platform} connection token was not found. It may have been removed or you may not have permission to access it.",
            error_code="TOKEN_NOT_FOUND",
            details={"token_id": token_id, "platform": platform}
        )


class TokenExpired(OAuthError):
    """Raised when a token has expired"""

    def __init__(self, platform: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=f"Your {platform} connection has expired. Please reconnect your {platform} account to continue.",
            error_code="TOKEN_EXPIRED",
            details={"platform": platform}
        )


class TokenRefreshFailed(OAuthError):
    """Raised when token refresh fails"""

    def __init__(self, platform: str, reason: str = "Unknown error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"We couldn't refresh your {platform} connection. Please reconnect your {platform} account.",
            error_code="TOKEN_REFRESH_FAILED",
            details={"platform": platform, "reason": reason}
        )


class TokenValidationFailed(OAuthError):
    """Raised when token validation fails"""

    def __init__(self, platform: str, reason: str = "Unknown error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"We couldn't verify your {platform} connection. Please try again or reconnect your account.",
            error_code="TOKEN_VALIDATION_FAILED",
            details={"platform": platform, "reason": reason}
        )


class NoTokenConnected(OAuthError):
    """Raised when no token is connected for a platform"""

    def __init__(self, platform: str, tenant_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=f"No {platform} account is connected. Please connect your {platform} account first.",
            error_code="NO_TOKEN_CONNECTED",
            details={"platform": platform, "tenant_id": tenant_id}
        )


class PageNotFound(OAuthError):
    """Raised when a Facebook page is not found"""

    def __init__(self, page_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=f"The Facebook page was not found or you don't have permission to manage it. Please check your page permissions in Facebook Business Settings.",
            error_code="PAGE_NOT_FOUND",
            details={"page_id": page_id}
        )


class PostToPageFailed(OAuthError):
    """Raised when posting to a page fails"""

    def __init__(self, page_id: str, reason: str = "Unknown error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="We couldn't post to your Facebook page. Please check your page permissions and try again.",
            error_code="POST_TO_PAGE_FAILED",
            details={"page_id": page_id, "reason": reason}
        )


class InsightsRetrievalFailed(OAuthError):
    """Raised when fetching page insights fails"""

    def __init__(self, page_id: str, reason: str = "Unknown error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="We couldn't retrieve the page insights. Please try again later or check your page permissions.",
            error_code="INSIGHTS_RETRIEVAL_FAILED",
            details={"page_id": page_id, "reason": reason}
        )


class VideoUploadFailed(OAuthError):
    """Raised when video upload to TikTok fails"""

    def __init__(self, reason: str = "Unknown error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="We couldn't upload your video to TikTok. Please check your video file and try again.",
            error_code="VIDEO_UPLOAD_FAILED",
            details={"reason": reason}
        )


# =============================================================================
# User Role Control Errors
# =============================================================================

class UserAuthError(BaseControlError):
    """Base class for user authentication errors"""
    pass


class InvalidCredentials(UserAuthError):
    """Raised when login credentials are invalid"""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="The username or password you entered is incorrect. Please check your credentials and try again.",
            error_code="INVALID_CREDENTIALS",
            details={}
        )


class UserNotFound(UserAuthError):
    """Raised when a user is not found"""

    def __init__(self, identifier: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message="We couldn't find an account with those details. Please check your information or create a new account.",
            error_code="USER_NOT_FOUND",
            details={"identifier": identifier}
        )


class UserInactive(UserAuthError):
    """Raised when a user account is inactive"""

    def __init__(self, username: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Your account has been deactivated. Please contact support if you believe this is a mistake.",
            error_code="USER_INACTIVE",
            details={"username": username}
        )


class UsernameAlreadyExists(UserAuthError):
    """Raised when username is already taken"""

    def __init__(self, username: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"The username '{username}' is already taken. Please choose a different username.",
            error_code="USERNAME_ALREADY_EXISTS",
            details={"username": username}
        )


class EmailAlreadyExists(UserAuthError):
    """Raised when email is already registered"""

    def __init__(self, email: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="This email address is already registered. Please use a different email or try logging in.",
            error_code="EMAIL_ALREADY_EXISTS",
            details={"email": email}
        )


class PasswordTooWeak(UserAuthError):
    """Raised when password doesn't meet requirements"""

    def __init__(self, requirements: str = "at least 8 characters"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Your password doesn't meet the security requirements. Please use a password with {requirements}.",
            error_code="PASSWORD_TOO_WEAK",
            details={"requirements": requirements}
        )


class IncorrectPassword(UserAuthError):
    """Raised when current password is incorrect during password change"""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="The current password you entered is incorrect. Please try again.",
            error_code="INCORRECT_PASSWORD",
            details={}
        )


class TokenInvalid(UserAuthError):
    """Raised when JWT token is invalid"""

    def __init__(self, reason: str = "Token is invalid or malformed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Your session is invalid. Please log in again.",
            error_code="TOKEN_INVALID",
            details={"reason": reason}
        )


class TokenExpiredAuth(UserAuthError):
    """Raised when JWT token has expired"""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Your session has expired. Please log in again to continue.",
            error_code="TOKEN_EXPIRED",
            details={}
        )


class AdminAccessRequired(UserAuthError):
    """Raised when admin access is required"""

    def __init__(self, action: str = "perform this action"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=f"You need administrator privileges to {action}. Please contact your organization's admin.",
            error_code="ADMIN_ACCESS_REQUIRED",
            details={"required_role": "admin", "action": action}
        )


class TenantMismatch(UserAuthError):
    """Raised when user tries to access resources from another tenant"""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message="You don't have permission to access this organization's resources.",
            error_code="TENANT_MISMATCH",
            details={}
        )


class TokenOwnershipError(UserAuthError):
    """Raised when user tries to access a token they don't own"""

    def __init__(self, token_id: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message="You don't have permission to manage this connection. It belongs to another user.",
            error_code="TOKEN_OWNERSHIP_ERROR",
            details={"token_id": token_id}
        )


# =============================================================================
# Data Deletion Errors
# =============================================================================

class DataDeletionError(BaseControlError):
    """Base class for data deletion errors"""
    pass


class InvalidSignedRequest(DataDeletionError):
    """Raised when Facebook signed request is invalid"""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="The data deletion request could not be verified. Please try again from Facebook.",
            error_code="INVALID_SIGNED_REQUEST",
            details={}
        )


class DataDeletionFailed(DataDeletionError):
    """Raised when data deletion fails"""

    def __init__(self, user_id: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="We encountered an issue while deleting your data. Please try again or contact support.",
            error_code="DATA_DELETION_FAILED",
            details={"user_id": user_id}
        )


class InvalidConfirmationCode(DataDeletionError):
    """Raised when confirmation code is invalid"""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="The confirmation code is invalid or has expired.",
            error_code="INVALID_CONFIRMATION_CODE",
            details={}
        )


# =============================================================================
# Generic Control Errors
# =============================================================================

class DatabaseError(BaseControlError):
    """Raised when a database operation fails"""

    def __init__(self, operation: str = "complete the operation"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"We couldn't {operation} due to a database issue. Please try again later.",
            error_code="DATABASE_ERROR",
            details={"operation": operation}
        )


class ServiceUnavailable(BaseControlError):
    """Raised when an external service is unavailable"""

    def __init__(self, service: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=f"The {service} service is temporarily unavailable. Please try again in a few minutes.",
            error_code="SERVICE_UNAVAILABLE",
            details={"service": service}
        )


class InvalidUUIDFormat(BaseControlError):
    """Raised when a UUID format is invalid"""

    def __init__(self, field_name: str, value: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"The {field_name} format is invalid. Please provide a valid identifier.",
            error_code="INVALID_UUID_FORMAT",
            details={"field": field_name, "value": value}
        )
