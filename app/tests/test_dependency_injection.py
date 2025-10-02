# app/tests/test_dependency_injection.py
"""
Test suite for dependency injection setup and validation.

This test suite validates that all dependencies can be properly resolved,
that services work correctly with repositories, and that the DI container
is properly configured for both FastAPI routes and background tasks.
"""
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.main import app
from app.deps import (
    get_db, get_settings_dep, get_logger,
    get_tenant_service, get_auth_service, get_automation_service,
    get_facebook_oauth, get_tiktok_oauth, get_token_encryptor
)
from app.core.config import Settings
from app.services import TenantService, AuthService, AutomationService
from app.repositories import TenantRepository, UserRepository, AdTokenRepository
from app.integrations.oauth import FacebookOAuth, TikTokOAuth
from app.core.crypto import TokenEncryptor


class TestDependencyInjection:
    """Test dependency injection setup and resolution"""

    def test_database_dependency_resolution(self):
        """Test that database sessions are properly created and cleaned up"""
        db_gen = get_db()
        db_session = next(db_gen)

        assert isinstance(db_session, Session)
        assert db_session.is_active

        # Clean up
        try:
            next(db_gen)
        except StopIteration:
            pass  # Expected when generator is exhausted

    def test_settings_dependency_resolution(self):
        """Test that settings are properly resolved"""
        settings = get_settings_dep()
        assert isinstance(settings, Settings)
        assert hasattr(settings, 'ENV')
        assert hasattr(settings, 'DATABASE_URL')

    def test_logger_dependency_resolution(self):
        """Test that logger is properly configured"""
        import logging
        logger = get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "app"
        assert len(logger.handlers) > 0

    @patch('app.core.db.get_db')
    def test_service_dependency_resolution(self, mock_get_db):
        """Test that services are properly instantiated with dependencies"""
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = iter([mock_db])

        # Test tenant service
        tenant_service = get_tenant_service(mock_db)
        assert isinstance(tenant_service, TenantService)
        assert tenant_service.db == mock_db
        assert isinstance(tenant_service.tenant_repo, TenantRepository)

        # Test auth service
        auth_service = get_auth_service(mock_db)
        assert isinstance(auth_service, AuthService)
        assert auth_service.db == mock_db

        # Test automation service
        automation_service = get_automation_service(mock_db)
        assert isinstance(automation_service, AutomationService)
        assert automation_service.db == mock_db

    def test_integration_dependency_resolution(self):
        """Test that integration services are properly resolved"""
        # Test token encryptor (cached)
        encryptor = get_token_encryptor()
        assert isinstance(encryptor, TokenEncryptor)

        # Test OAuth providers
        settings = get_settings_dep()

        fb_oauth = get_facebook_oauth(settings)
        assert isinstance(fb_oauth, FacebookOAuth)
        assert fb_oauth.s == settings

        tiktok_oauth = get_tiktok_oauth(settings)
        assert isinstance(tiktok_oauth, TikTokOAuth)
        assert tiktok_oauth.s == settings

    def test_fastapi_route_dependency_injection(self):
        """Test that FastAPI routes can resolve dependencies"""
        client = TestClient(app)

        # Test health endpoint which uses settings dependency
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "environment" in data
        assert "services" in data

    @patch('app.services.TenantService.get_active_tenants')
    def test_api_endpoints_use_proper_di(self, mock_get_tenants):
        """Test that API endpoints properly use dependency injection"""
        mock_get_tenants.return_value = []

        client = TestClient(app)
        response = client.get("/api/tenants")

        # Should return 200 even if empty, proving DI worked
        assert response.status_code == 200
        assert response.json() == []
        mock_get_tenants.assert_called_once()

    def test_repository_dependency_chain(self):
        """Test that repository dependencies are properly chained"""
        from app.deps import get_tenant_repository, get_user_repository

        mock_db = Mock(spec=Session)

        tenant_repo = get_tenant_repository(mock_db)
        assert isinstance(tenant_repo, TenantRepository)
        assert tenant_repo.db == mock_db

        user_repo = get_user_repository(mock_db)
        assert isinstance(user_repo, UserRepository)
        assert user_repo.db == mock_db

    @patch('app.core.crypto.load_encryptor')
    def test_cached_dependencies(self, mock_load_encryptor):
        """Test that cached dependencies are properly reused"""
        mock_encryptor = Mock(spec=TokenEncryptor)
        mock_load_encryptor.return_value = mock_encryptor

        # First call should load
        enc1 = get_token_encryptor()
        assert enc1 == mock_encryptor
        assert mock_load_encryptor.call_count == 1

        # Second call should use cache
        enc2 = get_token_encryptor()
        assert enc2 == mock_encryptor
        assert enc2 is enc1  # Same instance
        assert mock_load_encryptor.call_count == 1  # Not called again

    def test_type_annotations_work_with_di(self):
        """Test that type annotations work correctly with DI"""
        from app.deps import DatabaseSession, SettingsDep, TenantSvc
        from typing import get_args, get_origin

        # Verify annotated types are properly configured
        assert get_origin(DatabaseSession) is not None
        assert get_origin(SettingsDep) is not None
        assert get_origin(TenantSvc) is not None

    @patch.dict('os.environ', {
        'DATABASE_URL': 'postgresql://test:test@localhost/test',
        'OAUTH_STATE_SECRET': 'test-secret',
        'MASTER_SECRET_KEY': 'test-master-key',
        'FB_APP_ID': 'test-fb-id',
        'FB_APP_SECRET': 'test-fb-secret',
        'TIKTOK_CLIENT_KEY': 'test-tiktok-key',
        'TIKTOK_CLIENT_SECRET': 'test-tiktok-secret',
        'TELEGRAM_BOT_TOKEN': 'test-bot-token'
    })
    def test_settings_validation(self):
        """Test that settings validation works correctly"""
        # Clear cache to force reload with new env vars
        get_settings_dep.cache_clear() if hasattr(get_settings_dep, 'cache_clear') else None

        from app.core.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()
        assert settings.DATABASE_URL == 'postgresql://test:test@localhost/test'
        assert settings.FB_APP_ID == 'test-fb-id'
        assert settings.TIKTOK_CLIENT_KEY == 'test-tiktok-key'

    def test_di_works_in_background_tasks(self):
        """Test that DI can be used in background tasks (non-FastAPI context)"""
        from app.core.db import get_db_session
        from app.services import TenantService

        # Simulate background task usage
        with get_db_session() as db:
            tenant_service = TenantService(db)
            assert isinstance(tenant_service, TenantService)
            assert tenant_service.db == db


class TestDependencyOverrides:
    """Test dependency override functionality for testing"""

    def test_dependency_override_mechanism(self):
        """Test that FastAPI dependency overrides work correctly"""
        test_app = FastAPI()

        # Mock dependency
        def mock_get_db():
            yield Mock(spec=Session)

        # Override dependency
        test_app.dependency_overrides[get_db] = mock_get_db

        @test_app.get("/test")
        def test_endpoint(db: Session = get_db()):
            return {"db_type": type(db).__name__}

        client = TestClient(test_app)
        response = client.get("/test")

        assert response.status_code == 200
        # Should use mock instead of real database
        assert "Mock" in response.json()["db_type"]

    def test_service_mocking_for_tests(self):
        """Test that services can be mocked for unit testing"""
        mock_db = Mock(spec=Session)
        mock_tenant_service = Mock(spec=TenantService)

        # This pattern can be used in actual tests
        def mock_get_tenant_service(db: Session = mock_db):
            return mock_tenant_service

        service = mock_get_tenant_service()
        assert service == mock_tenant_service


if __name__ == "__main__":
    pytest.main([__file__, "-v"])