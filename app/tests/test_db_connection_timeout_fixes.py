# app/tests/test_db_connection_timeout_fixes.py
"""
Test suite for database connection timeout fixes and retry logic.

This test validates that the new retry mechanisms work correctly
and that background tasks are resilient to database connection issues.
"""
import pytest
import time
import asyncio
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.exc import OperationalError, DisconnectionError
import psycopg.errors

from app.core.db import (
    is_connection_error,
    retry_db_operation,
    get_db_session_with_retry,
    SessionLocal
)
from app.jobs.automation_scheduler import AutomationScheduler
from app.services.automation_service import AutomationService


class TestConnectionErrorDetection:
    """Test connection error detection logic"""

    def test_detects_sqlalchemy_connection_errors(self):
        """Test detection of SQLAlchemy connection errors"""
        operational_error = OperationalError("Connection timeout", None, None)
        disconnection_error = DisconnectionError("Connection lost")

        assert is_connection_error(operational_error)
        assert is_connection_error(disconnection_error)

    def test_detects_psycopg_connection_errors(self):
        """Test detection of psycopg connection errors"""
        timeout_error = psycopg.errors.ConnectionTimeout("Connection timeout expired")
        admin_shutdown = psycopg.errors.AdminShutdown("Server shutting down")

        assert is_connection_error(timeout_error)
        assert is_connection_error(admin_shutdown)

    def test_detects_connection_errors_by_message(self):
        """Test detection of connection errors by message content"""
        timeout_error = Exception("connection timeout expired")
        refused_error = Exception("connection refused by server")
        closed_error = Exception("server closed the connection")

        assert is_connection_error(timeout_error)
        assert is_connection_error(refused_error)
        assert is_connection_error(closed_error)

    def test_does_not_detect_business_logic_errors(self):
        """Test that business logic errors are not treated as connection errors"""
        value_error = ValueError("Invalid input data")
        key_error = KeyError("Missing field")
        custom_error = Exception("Business logic validation failed")

        assert not is_connection_error(value_error)
        assert not is_connection_error(key_error)
        assert not is_connection_error(custom_error)


class TestRetryLogic:
    """Test database operation retry logic"""

    def test_successful_operation_no_retry(self):
        """Test that successful operations don't retry"""
        mock_operation = Mock(return_value="success")

        result = retry_db_operation(
            operation=mock_operation,
            max_retries=3,
            operation_name="Test operation"
        )

        assert result == "success"
        assert mock_operation.call_count == 1

    def test_retries_on_connection_errors(self):
        """Test retry behavior on connection errors"""
        mock_operation = Mock()
        # Fail twice with connection error, then succeed
        mock_operation.side_effect = [
            OperationalError("Connection timeout", None, None),
            psycopg.errors.ConnectionTimeout("timeout expired"),
            "success"
        ]

        result = retry_db_operation(
            operation=mock_operation,
            max_retries=3,
            base_delay=0.1,  # Fast for testing
            operation_name="Test retry operation"
        )

        assert result == "success"
        assert mock_operation.call_count == 3

    def test_gives_up_after_max_retries(self):
        """Test that retry gives up after max attempts"""
        mock_operation = Mock()
        mock_operation.side_effect = OperationalError("Connection timeout", None, None)

        with pytest.raises(OperationalError):
            retry_db_operation(
                operation=mock_operation,
                max_retries=2,
                base_delay=0.1,
                operation_name="Test max retries"
            )

        # Should be called 3 times (initial + 2 retries)
        assert mock_operation.call_count == 3

    def test_no_retry_on_non_connection_errors(self):
        """Test that non-connection errors don't trigger retries"""
        mock_operation = Mock()
        mock_operation.side_effect = ValueError("Invalid data")

        with pytest.raises(ValueError):
            retry_db_operation(
                operation=mock_operation,
                max_retries=3,
                operation_name="Test no retry"
            )

        # Should only be called once
        assert mock_operation.call_count == 1

    def test_exponential_backoff_timing(self):
        """Test that exponential backoff delays work correctly"""
        mock_operation = Mock()
        mock_operation.side_effect = [
            OperationalError("timeout", None, None),
            OperationalError("timeout", None, None),
            "success"
        ]

        start_time = time.time()

        result = retry_db_operation(
            operation=mock_operation,
            max_retries=3,
            base_delay=0.1,
            operation_name="Test backoff timing"
        )

        elapsed = time.time() - start_time

        # Should take at least 0.1 + 0.2 = 0.3 seconds (with some tolerance)
        assert elapsed >= 0.25  # Allow for timing variations
        assert result == "success"


class TestSessionWithRetry:
    """Test database session with retry context manager"""

    @patch('app.core.db.SessionLocal')
    def test_successful_session_creation(self, mock_session_local):
        """Test successful session creation and commit"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session

        with get_db_session_with_retry(max_retries=2, operation_name="Test session") as session:
            # Simulate database operations
            session.query = Mock()

        # Session should be committed and closed
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.rollback.assert_not_called()

    @patch('app.core.db.SessionLocal')
    def test_session_rollback_on_exception(self, mock_session_local):
        """Test session rollback when exception occurs"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session

        with pytest.raises(ValueError):
            with get_db_session_with_retry(max_retries=2) as session:
                raise ValueError("Test error")

        # Session should be rolled back and closed
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.commit.assert_not_called()

    @patch('app.core.db.SessionLocal')
    def test_session_creation_retry(self, mock_session_local):
        """Test retry logic for session creation"""
        # Fail once, then succeed
        mock_session_local.side_effect = [
            OperationalError("Connection failed", None, None),
            Mock()
        ]

        with get_db_session_with_retry(max_retries=2) as session:
            pass

        # Should be called twice
        assert mock_session_local.call_count == 2


class TestAutomationSchedulerResilience:
    """Test automation scheduler resilience with new retry logic"""

    @pytest.fixture
    def scheduler(self):
        """Create scheduler instance for testing"""
        return AutomationScheduler(check_interval=1)

    @patch('app.jobs.automation_scheduler.get_db_session_with_retry')
    @patch('app.services.automation_service.AutomationService')
    async def test_scheduler_handles_connection_errors(self, mock_service_class, mock_db_session, scheduler):
        """Test that scheduler handles database connection errors gracefully"""
        mock_service = Mock()
        mock_service.get_due_automations.return_value = []
        mock_service_class.return_value = mock_service

        # Mock the session context manager
        mock_session_context = Mock()
        mock_session_context.__enter__.return_value = Mock()
        mock_session_context.__exit__.return_value = False
        mock_db_session.return_value = mock_session_context

        # This should not raise an exception
        await scheduler.check_and_execute_automations()

        # Verify retry logic was used
        mock_db_session.assert_called_with(
            max_retries=5,
            operation_name="Automation scheduler - get due automations"
        )

    @patch('app.jobs.automation_scheduler.get_db_session_with_retry')
    async def test_scheduler_continues_after_individual_failures(self, mock_db_session, scheduler):
        """Test that scheduler continues processing after individual automation failures"""
        # Mock automations
        mock_automation1 = Mock()
        mock_automation1.name = "Test Automation 1"
        mock_automation1.id = "1"

        mock_automation2 = Mock()
        mock_automation2.name = "Test Automation 2"
        mock_automation2.id = "2"

        # Mock service that returns automations
        mock_service = Mock()
        mock_service.get_due_automations.return_value = [mock_automation1, mock_automation2]

        # Mock session contexts
        def mock_session_context(*args, **kwargs):
            context = Mock()
            context.__enter__.return_value = Mock()
            context.__exit__.return_value = False
            return context

        mock_db_session.side_effect = [
            # First call for getting due automations
            mock_session_context(),
            # Second call for first automation - will fail
            mock_session_context(),
            # Third call for second automation - will succeed
            mock_session_context()
        ]

        # Mock the service creation
        with patch('app.jobs.automation_scheduler.AutomationService') as mock_service_class:
            mock_service_class.return_value = mock_service

            # Mock execute_automation_safe to fail for first automation
            original_execute = scheduler.execute_automation_safe
            async def mock_execute(automation, db):
                if automation.name == "Test Automation 1":
                    raise OperationalError("Connection failed", None, None)
                return Mock()

            scheduler.execute_automation_safe = mock_execute

            # This should not raise an exception and should process both automations
            await scheduler.check_and_execute_automations()

            # Should call session creation 3 times (1 for get + 2 for execute)
            assert mock_db_session.call_count == 3


class TestBackgroundTaskIntegration:
    """Integration tests for background task database connectivity"""

    async def test_automation_scheduler_start_stop(self):
        """Test that automation scheduler can start and stop gracefully"""
        scheduler = AutomationScheduler(check_interval=0.1)

        # Start the scheduler
        task = asyncio.create_task(scheduler.run_scheduler())

        # Let it run briefly
        await asyncio.sleep(0.2)

        # Stop the scheduler
        scheduler.stop()

        # Wait for task to complete
        try:
            await asyncio.wait_for(task, timeout=1.0)
        except asyncio.TimeoutError:
            task.cancel()
            pytest.fail("Scheduler did not stop gracefully")

    @patch('app.jobs.automation_scheduler.get_db_session_with_retry')
    async def test_scheduler_backoff_on_consecutive_failures(self, mock_db_session):
        """Test scheduler exponential backoff on consecutive failures"""
        # Make session creation always fail
        mock_db_session.side_effect = OperationalError("Always fails", None, None)

        scheduler = AutomationScheduler(check_interval=0.1)

        # Track call times to verify backoff
        start_time = time.time()
        call_times = []

        original_check = scheduler.check_and_execute_automations
        async def mock_check():
            call_times.append(time.time() - start_time)
            return await original_check()

        scheduler.check_and_execute_automations = mock_check

        # Start scheduler
        task = asyncio.create_task(scheduler.run_scheduler())

        # Let it fail a few times
        await asyncio.sleep(1.0)

        # Stop scheduler
        scheduler.stop()
        task.cancel()

        # Should have made multiple attempts with increasing delays
        assert len(call_times) >= 2

        # Verify delays are increasing (with some tolerance for timing)
        if len(call_times) >= 3:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]
            assert delay2 > delay1 * 0.8  # Allow for timing variations


if __name__ == "__main__":
    # Run with: python -m pytest app/tests/test_db_connection_timeout_fixes.py -v
    pytest.main([__file__, "-v", "--tb=short"])