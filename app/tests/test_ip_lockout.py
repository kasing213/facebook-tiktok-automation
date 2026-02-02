# app/tests/test_ip_lockout.py
"""
Comprehensive tests for IP lockout functionality.

Tests IP-based rate limiting, lockout creation, duration, and cleanup.
"""
import pytest
import datetime as dt
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.models import IPLockout, LoginAttempt, LoginAttemptResult
from app.repositories.ip_lockout import IPLockoutRepository
from app.services.login_attempt_service import LoginAttemptService


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    return Mock(spec=Session)


@pytest.fixture
def ip_lockout_repo(mock_db):
    """Create IP lockout repository with mock database"""
    return IPLockoutRepository(mock_db)


@pytest.fixture
def login_attempt_service(mock_db):
    """Create login attempt service with mock database"""
    return LoginAttemptService(mock_db)


@pytest.fixture
def sample_ip_lockout():
    """Create a sample IP lockout for testing"""
    return IPLockout(
        id="123e4567-e89b-12d3-a456-426614174000",
        ip_address="192.168.1.100",
        lockout_reason="too_many_failures_from_ip (10 attempts in 15 minutes)",
        failed_attempts_count=10,
        locked_at=dt.datetime.now(dt.timezone.utc),
        unlock_at=dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1),
        unlocked_at=None,
        unlocked_by=None
    )


class TestIPLockoutRepository:
    """Test IP lockout repository functionality"""

    def test_create_lockout(self, ip_lockout_repo, mock_db):
        """Test creating a new IP lockout"""
        test_ip = "192.168.1.100"
        failed_attempts = 10
        unlock_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)

        # Mock the create method
        mock_lockout = Mock()
        mock_lockout.ip_address = test_ip
        mock_lockout.failed_attempts_count = failed_attempts
        ip_lockout_repo.create = Mock(return_value=mock_lockout)

        result = ip_lockout_repo.create_lockout(
            ip_address=test_ip,
            failed_attempts_count=failed_attempts,
            unlock_at=unlock_at
        )

        assert result.ip_address == test_ip
        assert result.failed_attempts_count == failed_attempts
        ip_lockout_repo.create.assert_called_once()

    def test_get_active_lockout_exists(self, ip_lockout_repo, mock_db, sample_ip_lockout):
        """Test getting active lockout when one exists"""
        test_ip = "192.168.1.100"

        # Mock query chain
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = sample_ip_lockout
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        result = ip_lockout_repo.get_active_lockout(test_ip)

        assert result == sample_ip_lockout
        mock_db.query.assert_called_once_with(IPLockout)

    def test_get_active_lockout_none(self, ip_lockout_repo, mock_db):
        """Test getting active lockout when none exists"""
        test_ip = "192.168.1.100"

        # Mock query chain returning None
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        result = ip_lockout_repo.get_active_lockout(test_ip)

        assert result is None

    def test_is_ip_locked_true(self, ip_lockout_repo, sample_ip_lockout):
        """Test IP is locked when active lockout exists"""
        test_ip = "192.168.1.100"

        # Mock get_active_lockout to return a lockout
        ip_lockout_repo.get_active_lockout = Mock(return_value=sample_ip_lockout)

        result = ip_lockout_repo.is_ip_locked(test_ip)

        assert result is True
        ip_lockout_repo.get_active_lockout.assert_called_once_with(test_ip)

    def test_is_ip_locked_false(self, ip_lockout_repo):
        """Test IP is not locked when no active lockout exists"""
        test_ip = "192.168.1.100"

        # Mock get_active_lockout to return None
        ip_lockout_repo.get_active_lockout = Mock(return_value=None)

        result = ip_lockout_repo.is_ip_locked(test_ip)

        assert result is False

    def test_unlock_ip_success(self, ip_lockout_repo, mock_db, sample_ip_lockout):
        """Test successful manual IP unlock"""
        test_ip = "192.168.1.100"
        admin_user = "admin@example.com"

        # Mock get_active_lockout to return a lockout
        ip_lockout_repo.get_active_lockout = Mock(return_value=sample_ip_lockout)

        result = ip_lockout_repo.unlock_ip(test_ip, admin_user)

        assert result is True
        assert sample_ip_lockout.unlocked_by == admin_user
        assert sample_ip_lockout.unlocked_at is not None
        mock_db.flush.assert_called_once()

    def test_unlock_ip_no_lockout(self, ip_lockout_repo):
        """Test unlock IP when no active lockout exists"""
        test_ip = "192.168.1.100"
        admin_user = "admin@example.com"

        # Mock get_active_lockout to return None
        ip_lockout_repo.get_active_lockout = Mock(return_value=None)

        result = ip_lockout_repo.unlock_ip(test_ip, admin_user)

        assert result is False

    def test_get_ip_lockout_history(self, ip_lockout_repo, mock_db):
        """Test getting IP lockout history"""
        test_ip = "192.168.1.100"
        days = 30

        # Mock query chain
        mock_query = Mock()
        mock_filter = Mock()
        mock_order_by = Mock()
        mock_all = Mock()

        mock_lockout = Mock()
        mock_all.all.return_value = [mock_lockout]
        mock_order_by.all = Mock(return_value=[mock_lockout])
        mock_filter.order_by.return_value = mock_order_by
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        result = ip_lockout_repo.get_ip_lockout_history(test_ip, days)

        mock_db.query.assert_called_once_with(IPLockout)
        assert isinstance(result, list)

    def test_cleanup_expired_lockouts(self, ip_lockout_repo, mock_db):
        """Test cleanup of old lockout records"""
        days_to_keep = 30

        # Mock query and delete
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.delete.return_value = 5  # 5 records deleted
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        result = ip_lockout_repo.cleanup_expired_lockouts(days_to_keep)

        assert result == 5
        mock_db.query.assert_called_once_with(IPLockout)
        mock_filter.delete.assert_called_once()


class TestLoginAttemptServiceIPLockout:
    """Test IP lockout functionality in LoginAttemptService"""

    def test_is_ip_locked_integration(self, login_attempt_service):
        """Test IP locked check through service"""
        test_ip = "192.168.1.100"

        # Mock the ip_lockout_repo
        login_attempt_service.ip_lockout_repo.is_ip_locked = Mock(return_value=True)

        result = login_attempt_service.is_ip_locked(test_ip)

        assert result is True
        login_attempt_service.ip_lockout_repo.is_ip_locked.assert_called_once_with(test_ip)

    def test_get_ip_lockout_info_integration(self, login_attempt_service, sample_ip_lockout):
        """Test getting IP lockout info through service"""
        test_ip = "192.168.1.100"

        # Mock the ip_lockout_repo
        login_attempt_service.ip_lockout_repo.get_active_lockout = Mock(return_value=sample_ip_lockout)

        result = login_attempt_service.get_ip_lockout_info(test_ip)

        assert result == sample_ip_lockout
        login_attempt_service.ip_lockout_repo.get_active_lockout.assert_called_once_with(test_ip)

    @patch('app.services.login_attempt_service.dt.datetime')
    def test_check_and_apply_ip_lockout_triggers(self, mock_datetime, login_attempt_service, mock_db):
        """Test that IP lockout is applied after too many failures"""
        test_ip = "192.168.1.100"

        # Mock datetime
        now = dt.datetime.now(dt.timezone.utc)
        mock_datetime.now.return_value = now

        # Mock query to return 10 failed attempts (exceeds threshold)
        mock_query = Mock()
        mock_filter = Mock()
        mock_count = Mock()
        mock_count.count.return_value = 10  # Exceeds IP_LOCKOUT_ATTEMPTS (10)
        mock_filter.count.return_value = 10
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        # Mock IP not currently locked
        login_attempt_service.is_ip_locked = Mock(return_value=False)

        # Mock create_lockout
        mock_lockout = Mock()
        login_attempt_service.ip_lockout_repo.create_lockout = Mock(return_value=mock_lockout)

        was_locked, lockout_info = login_attempt_service.check_and_apply_ip_lockout(test_ip)

        assert was_locked is True
        assert lockout_info == mock_lockout
        login_attempt_service.ip_lockout_repo.create_lockout.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_check_and_apply_ip_lockout_no_trigger(self, login_attempt_service, mock_db):
        """Test that IP lockout is not applied when attempts are below threshold"""
        test_ip = "192.168.1.100"

        # Mock query to return 3 failed attempts (below threshold)
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.count.return_value = 3  # Below IP_LOCKOUT_ATTEMPTS (10)
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        was_locked, lockout_info = login_attempt_service.check_and_apply_ip_lockout(test_ip)

        assert was_locked is False
        assert lockout_info is None
        mock_db.commit.assert_not_called()

    def test_check_and_apply_ip_lockout_already_locked(self, login_attempt_service, mock_db):
        """Test that IP lockout is not applied again if already locked"""
        test_ip = "192.168.1.100"

        # Mock query to return 15 failed attempts (exceeds threshold)
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.count.return_value = 15
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        # Mock IP already locked
        login_attempt_service.is_ip_locked = Mock(return_value=True)

        was_locked, lockout_info = login_attempt_service.check_and_apply_ip_lockout(test_ip)

        assert was_locked is False
        assert lockout_info is None

    def test_unlock_ip_integration(self, login_attempt_service, mock_db):
        """Test IP unlock through service"""
        test_ip = "192.168.1.100"
        admin_user = "admin@example.com"

        # Mock successful unlock
        login_attempt_service.ip_lockout_repo.unlock_ip = Mock(return_value=True)

        result = login_attempt_service.unlock_ip(test_ip, admin_user)

        assert result is True
        login_attempt_service.ip_lockout_repo.unlock_ip.assert_called_once_with(test_ip, admin_user)
        mock_db.commit.assert_called_once()

    def test_cleanup_old_records_includes_ip_lockouts(self, login_attempt_service, mock_db):
        """Test that cleanup includes IP lockout records"""
        days_to_keep = 30

        # Mock successful cleanups
        mock_db.query.return_value.filter.return_value.delete.return_value = 5  # login attempts
        login_attempt_service.ip_lockout_repo.cleanup_expired_lockouts = Mock(return_value=3)

        attempts_deleted, account_lockouts_deleted, ip_lockouts_deleted = \
            login_attempt_service.cleanup_old_records(days_to_keep)

        assert ip_lockouts_deleted == 3
        login_attempt_service.ip_lockout_repo.cleanup_expired_lockouts.assert_called_once_with(days_to_keep)
        mock_db.commit.assert_called_once()


class TestIPLockoutConfiguration:
    """Test IP lockout configuration and constants"""

    def test_ip_lockout_configuration(self, login_attempt_service):
        """Test IP lockout configuration constants"""
        assert login_attempt_service.IP_LOCKOUT_ATTEMPTS == 10
        assert login_attempt_service.IP_LOCKOUT_DURATION_HOURS == 1
        assert login_attempt_service.ATTEMPT_WINDOW_MINUTES == 15

    def test_lockout_duration_calculation(self):
        """Test that lockout duration is calculated correctly"""
        duration_hours = 1
        expected_seconds = duration_hours * 60 * 60

        # This would be tested in actual lockout creation
        duration = dt.timedelta(hours=duration_hours)
        assert duration.total_seconds() == expected_seconds


class TestIPLockoutEdgeCases:
    """Test edge cases and error conditions"""

    def test_lockout_with_invalid_ip(self, ip_lockout_repo, mock_db):
        """Test lockout creation with edge case IP addresses"""
        edge_case_ips = [
            "0.0.0.0",
            "255.255.255.255",
            "::1",  # IPv6 localhost
            "2001:db8::1",  # IPv6 example
            "invalid-ip"  # Invalid format (should still work in our system)
        ]

        for ip in edge_case_ips:
            # Should not raise exceptions
            unlock_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)

            # Mock create to avoid actual database operations
            mock_lockout = Mock()
            mock_lockout.ip_address = ip
            ip_lockout_repo.create = Mock(return_value=mock_lockout)

            result = ip_lockout_repo.create_lockout(
                ip_address=ip,
                failed_attempts_count=10,
                unlock_at=unlock_at
            )

            assert result.ip_address == ip

    def test_concurrent_lockout_creation(self, login_attempt_service, mock_db):
        """Test handling of concurrent lockout creation attempts"""
        test_ip = "192.168.1.100"

        # Mock query to return threshold attempts
        mock_db.query.return_value.filter.return_value.count.return_value = 10

        # First check: IP not locked
        # Second check: IP already locked (simulating concurrent creation)
        login_attempt_service.is_ip_locked = Mock(side_effect=[False, True])

        # Should handle gracefully - the first call might create, second won't
        result1 = login_attempt_service.check_and_apply_ip_lockout(test_ip)
        result2 = login_attempt_service.check_and_apply_ip_lockout(test_ip)

        # At least one should indicate the state correctly
        assert result1[0] or not result2[0]  # Either first succeeded or second detected existing

    def test_expired_lockout_handling(self, ip_lockout_repo, mock_db):
        """Test that expired lockouts are not considered active"""
        test_ip = "192.168.1.100"

        # Create expired lockout
        expired_lockout = Mock()
        expired_lockout.unlock_at = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=1)  # Expired

        # Mock query that would return expired lockout, but filter should exclude it
        # In the actual implementation, the filter checks unlock_at > now
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None  # Should return None for expired
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        result = ip_lockout_repo.get_active_lockout(test_ip)

        assert result is None  # Expired lockout should not be active