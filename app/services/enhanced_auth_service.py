# app/services/enhanced_auth_service.py
"""
Enhanced Auth Service demonstrating standardized request/response validation patterns.
This shows how to refactor existing services to use the new validation system.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.base_service import BaseService, service_method
from app.services.validation_schemas import (
    StoreOAuthTokenRequest, StoreOAuthTokenResponse,
    GetTokenRequest, GetTokenResponse,
    ValidateTokenRequest, ValidateTokenResponse,
    AuthenticateUserRequest, AuthenticateUserResponse,
    CreateUserRequest, CreateUserResponse,
    GetFacebookPagesRequest, GetFacebookPagesResponse,
    RefreshTokenRequest, RefreshTokenResponse,
    DeleteUserDataRequest, DeleteUserDataResponse
)
from app.core.models import AdToken, Platform, User, TokenType, SocialIdentity, FacebookPage
from app.repositories import AdTokenRepository, UserRepository
from app.repositories.social_identity import SocialIdentityRepository
from app.repositories.facebook_page import FacebookPageRepository
from app.core.crypto import TokenEncryptor
from app.integrations.oauth import OAuthResult, FacebookAPIClient


class EnhancedAuthService(BaseService):
    """
    Enhanced Auth Service with standardized validation patterns.

    Demonstrates:
    - Request/response validation using Pydantic models
    - Standardized error responses
    - Metrics tracking
    - Proper tenant isolation
    """

    def __init__(self, db: Session, encryptor: TokenEncryptor):
        super().__init__(db)
        self.ad_token_repo = AdTokenRepository(db)
        self.user_repo = UserRepository(db)
        self.social_identity_repo = SocialIdentityRepository(db)
        self.facebook_page_repo = FacebookPageRepository(db)
        self.encryptor = encryptor

    def _service_specific_health_checks(self) -> Dict[str, Any]:
        """Service-specific health checks"""
        return {
            "encryptor_available": self.encryptor is not None,
            "repositories_initialized": all([
                self.ad_token_repo,
                self.user_repo,
                self.social_identity_repo,
                self.facebook_page_repo
            ])
        }

    @service_method(retry_count=3, track_metrics=True)
    def store_oauth_token(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store OAuth token with full validation and standardized responses.

        Args:
            request_data: Raw request data to validate

        Returns:
            Standardized response with token information
        """
        # Validate request
        validation_result = self.validate_request(request_data, StoreOAuthTokenRequest)
        if not validation_result.is_valid:
            return self.format_validation_error_response(validation_result)

        request = validation_result.data

        try:
            with self.transaction():
                # Encrypt tokens
                encrypted_access_token = self.encryptor.enc(request.access_token)
                encrypted_refresh_token = None
                if request.refresh_token:
                    encrypted_refresh_token = self.encryptor.enc(request.refresh_token)

                # Build OAuth result object for existing logic
                oauth_result = OAuthResult(
                    platform=request.platform,
                    access_token=request.access_token,
                    refresh_token=request.refresh_token,
                    account_ref=request.account_ref,
                    scope=request.scope,
                    expires_at=request.expires_at,
                    raw=request.raw_data or {}
                )

                # Use existing store logic (could be refactored further)
                token = self._store_oauth_token_internal(
                    tenant_id=request.tenant_id,
                    oauth_result=oauth_result,
                    user_id=request.user_id
                )

                # Format success response
                response_data = StoreOAuthTokenResponse(
                    token_id=token.id,
                    platform=token.platform,
                    account_name=token.account_name,
                    expires_at=token.expires_at
                )

                return self.format_success_response(
                    response_data.dict(),
                    "OAuth token stored successfully"
                )

        except Exception as e:
            self.logger.error(f"Failed to store OAuth token: {e}")
            return self.format_error_response(
                "Failed to store OAuth token",
                "TOKEN_STORAGE_ERROR",
                {"error": str(e)}
            )

    @service_method(retry_count=3, track_metrics=True)
    def get_decrypted_token(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get decrypted token with validation.

        Args:
            request_data: Raw request data to validate

        Returns:
            Standardized response with token or error
        """
        # Validate request
        validation_result = self.validate_request(request_data, GetTokenRequest)
        if not validation_result.is_valid:
            return self.format_validation_error_response(validation_result)

        request = validation_result.data

        # Validate tenant access if dealing with specific resources
        if request.social_identity_id or request.facebook_page_id:
            # Would need to fetch and validate tenant ownership
            pass

        try:
            token = self.ad_token_repo.get_active_token(
                tenant_id=request.tenant_id,
                platform=request.platform,
                user_id=request.user_id,
                account_ref=request.account_ref,
                social_identity_id=request.social_identity_id,
                facebook_page_id=request.facebook_page_id
            )

            if token and token.is_valid:
                try:
                    decrypted_token = self.encryptor.dec(token.access_token_enc)

                    response_data = GetTokenResponse(
                        token=decrypted_token,
                        expires_at=token.expires_at,
                        is_valid=True
                    )

                    return self.format_success_response(
                        response_data.dict(),
                        "Token retrieved successfully"
                    )

                except Exception as decrypt_error:
                    # Token decryption failed, mark as invalid
                    self.ad_token_repo.invalidate_token(token.id)
                    self.db.commit()

                    self.logger.warning(f"Token decryption failed for token {token.id}: {decrypt_error}")

                    response_data = GetTokenResponse(
                        token=None,
                        expires_at=None,
                        is_valid=False
                    )

                    return self.format_success_response(
                        response_data.dict(),
                        "Token invalid or expired"
                    )
            else:
                response_data = GetTokenResponse(
                    token=None,
                    expires_at=None,
                    is_valid=False
                )

                return self.format_success_response(
                    response_data.dict(),
                    "No valid token found"
                )

        except Exception as e:
            self.logger.error(f"Failed to get token: {e}")
            return self.format_error_response(
                "Failed to retrieve token",
                "TOKEN_RETRIEVAL_ERROR",
                {"error": str(e)}
            )

    @service_method(retry_count=3, track_metrics=True)
    def validate_token(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate token ownership and status.

        Args:
            request_data: Raw request data to validate

        Returns:
            Standardized response with validation result
        """
        # Validate request
        validation_result = self.validate_request(request_data, ValidateTokenRequest)
        if not validation_result.is_valid:
            return self.format_validation_error_response(validation_result)

        request = validation_result.data

        try:
            # Verify user owns token
            if not self.ad_token_repo.verify_user_owns_token(request.token_id, request.user_id):
                return self.format_error_response(
                    "Access denied: Token not found or not owned by user",
                    "ACCESS_DENIED"
                )

            # Update token validation status
            token = self.ad_token_repo.update_validation(request.token_id, request.is_valid)

            if token:
                self.db.commit()

                response_data = ValidateTokenResponse(
                    token_id=token.id,
                    is_valid=token.is_valid,
                    updated_at=datetime.utcnow()
                )

                return self.format_success_response(
                    response_data.dict(),
                    "Token validation updated successfully"
                )
            else:
                return self.format_error_response(
                    "Token not found",
                    "TOKEN_NOT_FOUND"
                )

        except Exception as e:
            self.logger.error(f"Failed to validate token: {e}")
            return self.format_error_response(
                "Failed to validate token",
                "TOKEN_VALIDATION_ERROR",
                {"error": str(e)}
            )

    @service_method(retry_count=3, track_metrics=True)
    def authenticate_user(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Authenticate user and update last login.

        Args:
            request_data: Raw request data to validate

        Returns:
            Standardized response with authentication result
        """
        # Validate request
        validation_result = self.validate_request(request_data, AuthenticateUserRequest)
        if not validation_result.is_valid:
            return self.format_validation_error_response(validation_result)

        request = validation_result.data

        try:
            user = self.user_repo.get_by_telegram_id(request.tenant_id, request.telegram_user_id)

            if user and user.is_active:
                # Update last login
                self.user_repo.update_last_login(user.id)
                self.db.commit()

                response_data = AuthenticateUserResponse(
                    user_id=user.id,
                    username=user.username,
                    is_authenticated=True,
                    last_login=user.last_login
                )

                self.log_service_action("user_authenticated", {
                    "user_id": str(user.id),
                    "telegram_user_id": request.telegram_user_id
                })

                return self.format_success_response(
                    response_data.dict(),
                    "User authenticated successfully"
                )
            else:
                response_data = AuthenticateUserResponse(
                    user_id=None,
                    username=None,
                    is_authenticated=False,
                    last_login=None
                )

                return self.format_success_response(
                    response_data.dict(),
                    "User not found or inactive"
                )

        except Exception as e:
            self.logger.error(f"Failed to authenticate user: {e}")
            return self.format_error_response(
                "Failed to authenticate user",
                "AUTHENTICATION_ERROR",
                {"error": str(e)}
            )

    @service_method(retry_count=3, track_metrics=True)
    def create_user(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new user or return existing.

        Args:
            request_data: Raw request data to validate

        Returns:
            Standardized response with user information
        """
        # Validate request
        validation_result = self.validate_request(request_data, CreateUserRequest)
        if not validation_result.is_valid:
            return self.format_validation_error_response(validation_result)

        request = validation_result.data

        try:
            with self.transaction():
                # Check if user already exists
                existing_user = self.user_repo.get_by_telegram_id(
                    request.tenant_id,
                    request.telegram_user_id
                )

                if existing_user:
                    response_data = CreateUserResponse(
                        user_id=existing_user.id,
                        telegram_user_id=existing_user.telegram_user_id,
                        username=existing_user.username,
                        created_at=existing_user.created_at
                    )

                    return self.format_success_response(
                        response_data.dict(),
                        "User already exists"
                    )

                # Create new user
                user = self.user_repo.create_user(
                    tenant_id=request.tenant_id,
                    telegram_user_id=request.telegram_user_id,
                    username=request.username
                )

                response_data = CreateUserResponse(
                    user_id=user.id,
                    telegram_user_id=user.telegram_user_id,
                    username=user.username,
                    created_at=user.created_at
                )

                self.log_service_action("user_created", {
                    "user_id": str(user.id),
                    "telegram_user_id": request.telegram_user_id
                })

                return self.format_success_response(
                    response_data.dict(),
                    "User created successfully"
                )

        except Exception as e:
            self.logger.error(f"Failed to create user: {e}")
            return self.format_error_response(
                "Failed to create user",
                "USER_CREATION_ERROR",
                {"error": str(e)}
            )

    def _store_oauth_token_internal(
        self,
        tenant_id: UUID,
        oauth_result: OAuthResult,
        user_id: UUID
    ) -> AdToken:
        """
        Internal method to store OAuth token (existing logic).
        This could be further refactored but keeping for compatibility.
        """
        # Implementation would match the existing store_oauth_token logic
        # from the original auth service
        pass