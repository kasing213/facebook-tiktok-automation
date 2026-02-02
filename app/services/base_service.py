# app/services/base_service.py
"""
Base service class providing common patterns for all services.
"""
import logging
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Optional, Type, Dict, Callable, TypeVar, Union
from uuid import UUID
from functools import wraps
import asyncio
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError, OperationalError
from pydantic import BaseModel, ValidationError

from app.core.db import get_db_session_with_retry
from app.core.exceptions import ServiceError, ValidationError as ServiceValidationError
from app.core.validation import (
    BaseRequestModel, BaseResponseModel, RequestValidator, ResponseFormatter,
    ValidationResult
)

logger = logging.getLogger(__name__)

T = TypeVar('T')
ServiceT = TypeVar('ServiceT', bound='BaseService')


class ServiceMetrics:
    """Track service performance metrics"""
    def __init__(self):
        self.call_count: int = 0
        self.total_time: float = 0.0
        self.error_count: int = 0
        self.last_call: Optional[datetime] = None
        self.avg_response_time: float = 0.0

    def record_call(self, duration: float, success: bool = True):
        """Record a service call"""
        self.call_count += 1
        self.total_time += duration
        self.last_call = datetime.utcnow()
        self.avg_response_time = self.total_time / self.call_count

        if not success:
            self.error_count += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        error_rate = (self.error_count / self.call_count) if self.call_count > 0 else 0
        return {
            "call_count": self.call_count,
            "error_count": self.error_count,
            "error_rate": round(error_rate, 4),
            "avg_response_time_ms": round(self.avg_response_time * 1000, 2),
            "total_time_s": round(self.total_time, 2),
            "last_call": self.last_call.isoformat() if self.last_call else None
        }


def service_method(retry_count: int = 3, track_metrics: bool = True):
    """
    Decorator for service methods with retry logic and metrics tracking.

    Args:
        retry_count: Number of retries for database operations
        track_metrics: Whether to track performance metrics
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(self: 'BaseService', *args, **kwargs):
            start_time = time.time()
            method_name = f"{self.__class__.__name__}.{func.__name__}"
            success = True

            try:
                if asyncio.iscoroutinefunction(func):
                    result = await self._retry_async_operation(
                        lambda: func(self, *args, **kwargs),
                        retry_count,
                        method_name
                    )
                else:
                    result = self._retry_operation(
                        lambda: func(self, *args, **kwargs),
                        retry_count,
                        method_name
                    )
                return result
            except Exception as e:
                success = False
                logger.error(f"Service method {method_name} failed: {e}")
                raise
            finally:
                if track_metrics:
                    duration = time.time() - start_time
                    self.metrics.record_call(duration, success)

        @wraps(func)
        def sync_wrapper(self: 'BaseService', *args, **kwargs):
            start_time = time.time()
            method_name = f"{self.__class__.__name__}.{func.__name__}"
            success = True

            try:
                result = self._retry_operation(
                    lambda: func(self, *args, **kwargs),
                    retry_count,
                    method_name
                )
                return result
            except Exception as e:
                success = False
                logger.error(f"Service method {method_name} failed: {e}")
                raise
            finally:
                if track_metrics:
                    duration = time.time() - start_time
                    self.metrics.record_call(duration, success)

        # Return appropriate wrapper based on function type
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


class BaseService(ABC):
    """
    Base class for all services providing common patterns.

    Features:
    - Standardized error handling
    - Database session management with retry logic
    - Performance metrics tracking
    - Logging patterns
    - Transaction management
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)
        self.metrics = ServiceMetrics()
        self._service_name = self.__class__.__name__

        # Initialize service-specific setup
        self._initialize()

    def _initialize(self) -> None:
        """Override this method for service-specific initialization"""
        pass

    @contextmanager
    def get_db_session(self, use_existing: bool = True):
        """
        Get database session with proper error handling and cleanup.

        Args:
            use_existing: If True, use existing session if available
        """
        if use_existing and self.db:
            # Use existing session
            yield self.db
        else:
            # Create new session with retry logic
            with get_db_session_with_retry() as session:
                yield session

    def _retry_operation(self, operation: Callable[[], T], max_retries: int, operation_name: str) -> T:
        """
        Retry database operations with exponential backoff.

        Args:
            operation: Function to execute
            max_retries: Maximum number of retries
            operation_name: Name for logging

        Returns:
            Result of the operation

        Raises:
            ServiceError: If all retries are exhausted
        """
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return operation()
            except (DisconnectionError, OperationalError) as e:
                last_exception = e

                if attempt < max_retries:
                    delay = min(2 ** attempt, 30)  # Exponential backoff, max 30s
                    self.logger.warning(
                        f"Database operation {operation_name} failed (attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {delay}s: {e}"
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(
                        f"Database operation {operation_name} failed after {max_retries + 1} attempts: {e}"
                    )
            except Exception as e:
                # Non-retryable error
                self.logger.error(f"Non-retryable error in {operation_name}: {e}")
                raise ServiceError(f"Service operation failed: {str(e)}") from e

        # If we get here, all retries were exhausted
        raise ServiceError(f"Database operation failed after {max_retries + 1} attempts") from last_exception

    async def _retry_async_operation(self, operation: Callable, max_retries: int, operation_name: str) -> Any:
        """Async version of retry operation"""
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return await operation()
            except (DisconnectionError, OperationalError) as e:
                last_exception = e

                if attempt < max_retries:
                    delay = min(2 ** attempt, 30)
                    self.logger.warning(
                        f"Async operation {operation_name} failed (attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(
                        f"Async operation {operation_name} failed after {max_retries + 1} attempts: {e}"
                    )
            except Exception as e:
                self.logger.error(f"Non-retryable async error in {operation_name}: {e}")
                raise ServiceError(f"Async service operation failed: {str(e)}") from e

        raise ServiceError(f"Async operation failed after {max_retries + 1} attempts") from last_exception

    def validate_input(self, data: Any, model_class: Type[BaseModel]) -> BaseModel:
        """
        Validate input data using Pydantic models.

        Args:
            data: Data to validate
            model_class: Pydantic model class

        Returns:
            Validated data

        Raises:
            ServiceValidationError: If validation fails
        """
        try:
            if isinstance(data, dict):
                return model_class(**data)
            elif isinstance(data, model_class):
                return data
            else:
                return model_class.parse_obj(data)
        except ValidationError as e:
            self.logger.error(f"Input validation failed for {model_class.__name__}: {e}")
            raise ServiceValidationError(f"Invalid input data: {e}") from e

    def validate_request(
        self,
        data: Dict[str, Any],
        model_class: Type[BaseRequestModel]
    ) -> ValidationResult:
        """Validate request data against standardized request model"""
        return RequestValidator.validate_model(data, model_class)

    def validate_tenant_resource_access(self, tenant_id: UUID, resource_tenant_id: UUID) -> ValidationResult:
        """Validate tenant access using standardized validation"""
        return RequestValidator.validate_tenant_access(tenant_id, resource_tenant_id)

    def format_success_response(
        self,
        data: Any = None,
        message: str = "Operation completed successfully"
    ) -> Dict[str, Any]:
        """Format standardized success response"""
        return ResponseFormatter.success_response(data, message)

    def format_error_response(
        self,
        message: str,
        error_code: str = None,
        details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Format standardized error response"""
        return ResponseFormatter.error_response(message, error_code, details)

    def format_validation_error_response(self, validation_result: ValidationResult) -> Dict[str, Any]:
        """Format standardized validation error response"""
        return ResponseFormatter.validation_error_response(validation_result)

    def validate_tenant_access(self, tenant_id: UUID, resource_tenant_id: UUID) -> None:
        """
        Validate that the requesting tenant has access to the resource.

        Args:
            tenant_id: Requesting tenant ID
            resource_tenant_id: Resource owner tenant ID

        Raises:
            ServiceError: If tenant doesn't have access
        """
        if tenant_id != resource_tenant_id:
            self.logger.warning(
                f"Tenant isolation violation: {tenant_id} attempted to access resource owned by {resource_tenant_id}"
            )
            raise ServiceError("Access denied: insufficient permissions")

    def log_service_action(self, action: str, details: Dict[str, Any] = None, level: str = "info") -> None:
        """
        Log service actions with consistent format.

        Args:
            action: Action being performed
            details: Additional details to log
            level: Log level (debug, info, warning, error)
        """
        log_data = {
            "service": self._service_name,
            "action": action,
            "timestamp": datetime.utcnow().isoformat()
        }

        if details:
            log_data.update(details)

        log_message = f"Service action: {action}"
        if details:
            log_message += f" | Details: {details}"

        getattr(self.logger, level)(log_message, extra=log_data)

    @contextmanager
    def transaction(self, session: Optional[Session] = None):
        """
        Database transaction context manager with automatic rollback on error.

        Args:
            session: Optional session to use, otherwise uses default
        """
        session_to_use = session or self.db
        if not session_to_use:
            raise ServiceError("No database session available for transaction")

        try:
            # Start transaction (implicit with SQLAlchemy)
            self.log_service_action("transaction_start")
            yield session_to_use
            session_to_use.commit()
            self.log_service_action("transaction_commit")
        except Exception as e:
            session_to_use.rollback()
            self.log_service_action("transaction_rollback", {"error": str(e)}, level="error")
            raise ServiceError(f"Transaction failed: {str(e)}") from e

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of the service.

        Returns:
            Health status information
        """
        try:
            # Test database connectivity if available
            db_healthy = False
            if self.db:
                try:
                    # Simple query to test connection
                    self.db.execute("SELECT 1")
                    db_healthy = True
                except Exception as e:
                    self.logger.warning(f"Database health check failed: {e}")

            return {
                "service": self._service_name,
                "status": "healthy" if db_healthy else "degraded",
                "database": "connected" if db_healthy else "disconnected",
                "metrics": self.metrics.get_metrics(),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Health check failed for {self._service_name}: {e}")
            return {
                "service": self._service_name,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    @abstractmethod
    def _service_specific_health_checks(self) -> Dict[str, Any]:
        """
        Override this method to add service-specific health checks.

        Returns:
            Service-specific health information
        """
        pass


class ServiceRegistry:
    """Registry for managing service instances"""

    _instances: Dict[str, BaseService] = {}

    @classmethod
    def register(cls, service_name: str, service_instance: BaseService) -> None:
        """Register a service instance"""
        cls._instances[service_name] = service_instance

    @classmethod
    def get(cls, service_name: str) -> Optional[BaseService]:
        """Get a registered service instance"""
        return cls._instances.get(service_name)

    @classmethod
    def get_all_health_status(cls) -> Dict[str, Any]:
        """Get health status for all registered services"""
        return {
            name: service.get_health_status()
            for name, service in cls._instances.items()
        }