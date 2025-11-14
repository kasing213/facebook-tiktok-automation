# app/tests/test_facebook_oauth.py
"""
Tests for Facebook OAuth integration and multi-tenant isolation.
"""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from app.core.models import Platform
from app.integrations.oauth import FacebookOAuth, OAuthResult, FacebookAPIClient
from app.services.auth_service import AuthService
from app.core.crypto import TokenEncryptor


class TestFacebookOAuth:
    """Test Facebook OAuth functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.tenant_id_1 = uuid4()
        self.tenant_id_2 = uuid4()

        # Mock settings
        self.mock_settings = MagicMock()
        self.mock_settings.FB_APP_ID = "test_app_id"
        self.mock_settings.FB_APP_SECRET.get_secret_value.return_value = "test_secret"
        self.mock_settings.FB_SCOPES = "pages_manage_posts,pages_read_engagement"
        self.mock_settings.BASE_URL = "http://localhost:8000"

    def test_auth_url_generation(self):
        """Test Facebook auth URL generation"""
        oauth = FacebookOAuth(self.mock_settings)

        # Mock state creation
        with patch.object(oauth, 'create_state', return_value='test_state'):
            auth_url = oauth.auth_url(str(self.tenant_id_1))

        assert "https://www.facebook.com/v23.0/dialog/oauth" in auth_url
        assert "client_id=test_app_id" in auth_url
        assert "state=test_state" in auth_url
        assert "pages_manage_posts" in auth_url

    @pytest.mark.asyncio
    async def test_token_exchange(self):
        """Test OAuth token exchange"""
        oauth = FacebookOAuth(self.mock_settings)

        # Mock HTTP responses
        mock_token_response = {
            "access_token": "short_token_123"
        }
        mock_long_token_response = {
            "access_token": "long_token_456",
            "expires_in": 5184000  # 60 days
        }
        mock_user_response = {
            "id": "user_123",
            "name": "Test User",
            "email": "test@example.com"
        }
        mock_pages_response = {
            "data": [
                {
                    "id": "page_123",
                    "name": "Test Page",
                    "access_token": "page_token_123",
                    "category": "Business"
                }
            ]
        }

        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock responses
            mock_context = mock_client.return_value.__aenter__.return_value

            # First call: short token exchange
            mock_response_1 = AsyncMock()
            mock_response_1.json.return_value = mock_token_response
            mock_response_1.raise_for_status.return_value = None

            # Second call: long-lived token exchange
            mock_response_2 = AsyncMock()
            mock_response_2.json.return_value = mock_long_token_response
            mock_response_2.raise_for_status.return_value = None

            # Third call: user info
            mock_response_3 = AsyncMock()
            mock_response_3.json.return_value = mock_user_response
            mock_response_3.raise_for_status.return_value = None

            # Fourth call: pages
            mock_response_4 = AsyncMock()
            mock_response_4.json.return_value = mock_pages_response
            mock_response_4.raise_for_status.return_value = None

            mock_context.get.side_effect = [
                mock_response_1, mock_response_2, mock_response_3, mock_response_4
            ]

            result = await oauth.exchange("test_code")

        assert result.platform == Platform.facebook
        assert result.account_ref == "user_123"
        assert result.access_token == "long_token_456"
        assert result.raw["user"]["name"] == "Test User"
        assert len(result.raw["pages"]) == 1
        assert result.raw["pages"][0]["id"] == "page_123"


class TestMultiTenantIsolation:
    """Test multi-tenant isolation for Facebook tokens"""

    def setup_method(self):
        """Setup test fixtures"""
        self.tenant_id_1 = uuid4()
        self.tenant_id_2 = uuid4()

        # Mock database and repositories
        self.mock_db = MagicMock()
        self.mock_encryptor = MagicMock(spec=TokenEncryptor)
        self.mock_encryptor.enc.side_effect = lambda x: f"encrypted_{x}"
        self.mock_encryptor.dec.side_effect = lambda x: x.replace("encrypted_", "")

    def test_token_isolation_between_tenants(self):
        """Test that tokens are isolated between tenants"""
        # Create mock OAuth results for two different tenants
        oauth_result_1 = OAuthResult(
            platform=Platform.facebook,
            account_ref="user_123",
            access_token="token_tenant_1",
            refresh_token=None,
            scope="pages_manage_posts",
            expires_at=datetime.utcnow() + timedelta(days=60),
            raw={
                "user": {"id": "user_123", "name": "Tenant 1 User"},
                "pages": [{"id": "page_1", "name": "Tenant 1 Page", "access_token": "page_token_1"}]
            }
        )

        oauth_result_2 = OAuthResult(
            platform=Platform.facebook,
            account_ref="user_456",
            access_token="token_tenant_2",
            refresh_token=None,
            scope="pages_manage_posts",
            expires_at=datetime.utcnow() + timedelta(days=60),
            raw={
                "user": {"id": "user_456", "name": "Tenant 2 User"},
                "pages": [{"id": "page_2", "name": "Tenant 2 Page", "access_token": "page_token_2"}]
            }
        )

        # Mock repository methods
        mock_ad_token_repo = MagicMock()
        mock_user_repo = MagicMock()

        # Mock that no existing tokens exist
        mock_ad_token_repo.get_active_token.return_value = None

        # Mock token creation - need tokens for user + page tokens
        mock_tokens = []
        for i in range(4):  # 2 user tokens + 2 page tokens
            mock_token = MagicMock()
            mock_token.id = uuid4()
            mock_tokens.append(mock_token)

        mock_ad_token_repo.create_token.side_effect = mock_tokens

        # Create auth service
        auth_service = AuthService(self.mock_db, self.mock_encryptor)
        auth_service.ad_token_repo = mock_ad_token_repo
        auth_service.user_repo = mock_user_repo

        # Store tokens for both tenants
        token_1 = auth_service.store_oauth_token(self.tenant_id_1, oauth_result_1)
        token_2 = auth_service.store_oauth_token(self.tenant_id_2, oauth_result_2)

        # Verify tokens were created with correct tenant isolation
        assert mock_ad_token_repo.create_token.call_count >= 2  # User tokens + page tokens

        # Check that tenant IDs are correctly passed
        call_args_list = mock_ad_token_repo.create_token.call_args_list
        tenant_ids_used = [call[1]['tenant_id'] for call in call_args_list]

        assert self.tenant_id_1 in tenant_ids_used
        assert self.tenant_id_2 in tenant_ids_used

    def test_page_token_isolation(self):
        """Test that Facebook page tokens are isolated between tenants"""
        oauth_result = OAuthResult(
            platform=Platform.facebook,
            account_ref="user_123",
            access_token="user_token",
            refresh_token=None,
            scope="pages_manage_posts",
            expires_at=datetime.utcnow() + timedelta(days=60),
            raw={
                "user": {"id": "user_123", "name": "Test User"},
                "pages": [
                    {"id": "page_1", "name": "Page 1", "access_token": "page_token_1"},
                    {"id": "page_2", "name": "Page 2", "access_token": "page_token_2"}
                ]
            }
        )

        # Mock repository
        mock_ad_token_repo = MagicMock()
        mock_user_repo = MagicMock()
        mock_ad_token_repo.get_active_token.return_value = None

        # Mock token creation
        mock_tokens = [MagicMock() for _ in range(3)]  # User + 2 pages
        for i, token in enumerate(mock_tokens):
            token.id = uuid4()
        mock_ad_token_repo.create_token.side_effect = mock_tokens

        # Create auth service
        auth_service = AuthService(self.mock_db, self.mock_encryptor)
        auth_service.ad_token_repo = mock_ad_token_repo
        auth_service.user_repo = mock_user_repo

        # Store OAuth result
        auth_service.store_oauth_token(self.tenant_id_1, oauth_result)

        # Verify page tokens were created with correct prefixes
        call_args_list = mock_ad_token_repo.create_token.call_args_list
        account_refs = [call[1].get('account_ref') for call in call_args_list]

        assert 'user_123' in account_refs  # User token
        assert 'page_page_1' in account_refs  # Page 1 token
        assert 'page_page_2' in account_refs  # Page 2 token

    def test_get_facebook_page_tokens_tenant_isolation(self):
        """Test that getting page tokens respects tenant isolation"""
        # Mock tokens for different tenants
        mock_token_tenant_1 = MagicMock()
        mock_token_tenant_1.account_ref = "page_123"
        mock_token_tenant_1.account_name = "Tenant 1 Page"
        mock_token_tenant_1.is_valid = True
        mock_token_tenant_1.access_token_enc = "encrypted_page_token_1"
        mock_token_tenant_1.id = uuid4()
        mock_token_tenant_1.meta = {"id": "123", "name": "Tenant 1 Page"}

        mock_token_tenant_2 = MagicMock()
        mock_token_tenant_2.account_ref = "page_456"
        mock_token_tenant_2.account_name = "Tenant 2 Page"
        mock_token_tenant_2.is_valid = True
        mock_token_tenant_2.access_token_enc = "encrypted_page_token_2"
        mock_token_tenant_2.id = uuid4()
        mock_token_tenant_2.meta = {"id": "456", "name": "Tenant 2 Page"}

        # Mock repository
        mock_ad_token_repo = MagicMock()
        mock_user_repo = MagicMock()

        # Return different tokens for different tenants
        def get_by_platform_side_effect(tenant_id, platform):
            if tenant_id == self.tenant_id_1:
                return [mock_token_tenant_1]
            elif tenant_id == self.tenant_id_2:
                return [mock_token_tenant_2]
            return []

        mock_ad_token_repo.get_by_platform.side_effect = get_by_platform_side_effect

        # Create auth service
        auth_service = AuthService(self.mock_db, self.mock_encryptor)
        auth_service.ad_token_repo = mock_ad_token_repo
        auth_service.user_repo = mock_user_repo

        # Get page tokens for tenant 1
        page_tokens_1 = auth_service.get_facebook_page_tokens(self.tenant_id_1)

        # Get page tokens for tenant 2
        page_tokens_2 = auth_service.get_facebook_page_tokens(self.tenant_id_2)

        # Verify isolation
        assert len(page_tokens_1) == 1
        assert len(page_tokens_2) == 1
        assert page_tokens_1[0]["page_id"] == "123"
        assert page_tokens_2[0]["page_id"] == "456"
        assert page_tokens_1[0]["page_name"] == "Tenant 1 Page"
        assert page_tokens_2[0]["page_name"] == "Tenant 2 Page"


class TestFacebookAPIClient:
    """Test Facebook API client functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.access_token = "test_access_token"
        self.client = FacebookAPIClient(self.access_token)

    @pytest.mark.asyncio
    async def test_post_to_page(self):
        """Test posting to Facebook page"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = {"id": "post_123"}
            mock_response.raise_for_status.return_value = None

            mock_context = mock_client.return_value.__aenter__.return_value
            mock_context.post.return_value = mock_response

            result = await self.client.post_to_page("page_123", "Test message", "page_token")

            assert result["id"] == "post_123"
            mock_context.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_page_insights(self):
        """Test getting page insights"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "data": [
                    {"name": "page_impressions", "values": [{"value": 1000}]}
                ]
            }
            mock_response.raise_for_status.return_value = None

            mock_context = mock_client.return_value.__aenter__.return_value
            mock_context.get.return_value = mock_response

            result = await self.client.get_page_insights("page_123", "page_token")

            assert "data" in result
            assert len(result["data"]) == 1
            mock_context.get.assert_called_once()