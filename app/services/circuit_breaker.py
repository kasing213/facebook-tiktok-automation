# app/services/circuit_breaker.py
"""
Circuit breaker pattern implementation for external service calls.
"""
import asyncio
import time
from enum import Enum
from typing import Callable, Any, Optional, Dict, List
from functools import wraps
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from app.core.exceptions import CircuitBreakerOpenError, ExternalServiceError

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Failing, calls blocked
    HALF_OPEN = "half_open" # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5          # Failures before opening
    success_threshold: int = 3          # Successes to close from half-open
    timeout_duration: int = 60          # Seconds before trying half-open
    monitor_window: int = 300           # Seconds to track failures
    exception_types: tuple = (Exception,)  # Exceptions that count as failures


class CircuitBreakerStats:
    """Track circuit breaker statistics"""

    def __init__(self, window_size: int = 300):
        self.window_size = window_size
        self.call_times: List[float] = []
        self.failure_times: List[float] = []
        self.success_count = 0
        self.failure_count = 0
        self.total_calls = 0

    def record_call(self, success: bool, call_time: float = None):
        """Record a call result"""
        now = time.time()
        if call_time is None:
            call_time = now

        self.call_times.append(call_time)
        self.total_calls += 1

        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
            self.failure_times.append(call_time)

        # Clean old data outside window
        self._clean_old_data(now)

    def _clean_old_data(self, current_time: float):
        """Remove data outside the monitoring window"""
        cutoff = current_time - self.window_size

        self.call_times = [t for t in self.call_times if t > cutoff]
        self.failure_times = [t for t in self.failure_times if t > cutoff]

    def get_failure_rate(self) -> float:
        """Get current failure rate"""
        if not self.call_times:
            return 0.0
        return len(self.failure_times) / len(self.call_times)

    def get_recent_failures(self) -> int:
        """Get number of recent failures"""
        return len(self.failure_times)

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        return {
            "total_calls": self.total_calls,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "window_calls": len(self.call_times),
            "window_failures": len(self.failure_times),
            "failure_rate": round(self.get_failure_rate(), 4),
            "window_size": self.window_size
        }


class CircuitBreaker:
    """
    Circuit breaker implementation for protecting external service calls.
    """

    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats(self.config.monitor_window)
        self.last_failure_time: Optional[float] = None
        self.consecutive_successes = 0
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: When circuit is open
            ExternalServiceError: When function fails
        """
        async with self._lock:
            # Check if circuit should transition states
            await self._check_state_transition()

            # If open, reject immediately
            if self.state == CircuitState.OPEN:
                logger.warning(f"Circuit breaker {self.name} is OPEN, rejecting call")
                raise CircuitBreakerOpenError(
                    self.name,
                    retry_after=self.config.timeout_duration
                )

        # Execute the function
        start_time = time.time()
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Record success
            await self._record_success(start_time)
            return result

        except Exception as e:
            # Record failure
            await self._record_failure(start_time, e)
            raise ExternalServiceError(
                self.name,
                f"call to {func.__name__}",
                getattr(e, 'status_code', None)
            ) from e

    async def _record_success(self, call_time: float):
        """Record successful call"""
        async with self._lock:
            self.stats.record_call(True, call_time)
            self.consecutive_successes += 1

            # If half-open and enough successes, close the circuit
            if (self.state == CircuitState.HALF_OPEN and
                    self.consecutive_successes >= self.config.success_threshold):
                await self._transition_to_closed()

            logger.debug(f"Circuit breaker {self.name} recorded success")

    async def _record_failure(self, call_time: float, exception: Exception):
        """Record failed call"""
        async with self._lock:
            self.stats.record_call(False, call_time)
            self.consecutive_successes = 0
            self.last_failure_time = call_time

            # Check if we should open the circuit
            if (self.state == CircuitState.CLOSED and
                    self.stats.get_recent_failures() >= self.config.failure_threshold):
                await self._transition_to_open()
            elif self.state == CircuitState.HALF_OPEN:
                # Failed while testing, go back to open
                await self._transition_to_open()

            logger.warning(
                f"Circuit breaker {self.name} recorded failure: {exception}",
                extra={"exception": str(exception)}
            )

    async def _check_state_transition(self):
        """Check if circuit should transition states"""
        now = time.time()

        if (self.state == CircuitState.OPEN and
                self.last_failure_time and
                now - self.last_failure_time > self.config.timeout_duration):
            await self._transition_to_half_open()

    async def _transition_to_open(self):
        """Transition circuit to OPEN state"""
        self.state = CircuitState.OPEN
        logger.warning(
            f"Circuit breaker {self.name} transitioned to OPEN "
            f"(failures: {self.stats.get_recent_failures()}, "
            f"threshold: {self.config.failure_threshold})"
        )

    async def _transition_to_half_open(self):
        """Transition circuit to HALF_OPEN state"""
        self.state = CircuitState.HALF_OPEN
        self.consecutive_successes = 0
        logger.info(f"Circuit breaker {self.name} transitioned to HALF_OPEN")

    async def _transition_to_closed(self):
        """Transition circuit to CLOSED state"""
        self.state = CircuitState.CLOSED
        logger.info(
            f"Circuit breaker {self.name} transitioned to CLOSED "
            f"(successes: {self.consecutive_successes})"
        )

    def get_state_info(self) -> Dict[str, Any]:
        """Get current state information"""
        return {
            "name": self.name,
            "state": self.state.value,
            "consecutive_successes": self.consecutive_successes,
            "last_failure_time": self.last_failure_time,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout_duration": self.config.timeout_duration,
                "monitor_window": self.config.monitor_window
            },
            "stats": self.stats.get_stats(),
            "is_available": self.state != CircuitState.OPEN
        }


class CircuitBreakerRegistry:
    """Registry for managing circuit breakers"""

    _breakers: Dict[str, CircuitBreaker] = {}

    @classmethod
    def get_breaker(cls, name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Get or create circuit breaker"""
        if name not in cls._breakers:
            cls._breakers[name] = CircuitBreaker(name, config)
        return cls._breakers[name]

    @classmethod
    def get_all_states(cls) -> Dict[str, Dict[str, Any]]:
        """Get state info for all circuit breakers"""
        return {
            name: breaker.get_state_info()
            for name, breaker in cls._breakers.items()
        }

    @classmethod
    async def reset_breaker(cls, name: str) -> bool:
        """Reset circuit breaker to closed state"""
        if name in cls._breakers:
            breaker = cls._breakers[name]
            async with breaker._lock:
                breaker.state = CircuitState.CLOSED
                breaker.consecutive_successes = 0
                breaker.last_failure_time = None
                logger.info(f"Circuit breaker {name} manually reset to CLOSED")
            return True
        return False


def circuit_breaker(
    name: str = None,
    failure_threshold: int = 5,
    success_threshold: int = 3,
    timeout_duration: int = 60,
    monitor_window: int = 300,
    exception_types: tuple = (Exception,)
):
    """
    Decorator for adding circuit breaker protection to functions.

    Args:
        name: Circuit breaker name (defaults to function name)
        failure_threshold: Failures before opening circuit
        success_threshold: Successes needed to close from half-open
        timeout_duration: Seconds before trying half-open
        monitor_window: Seconds to track failures
        exception_types: Exception types that count as failures
    """
    def decorator(func: Callable) -> Callable:
        breaker_name = name or f"{func.__module__}.{func.__qualname__}"
        config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            timeout_duration=timeout_duration,
            monitor_window=monitor_window,
            exception_types=exception_types
        )

        breaker = CircuitBreakerRegistry.get_breaker(breaker_name, config)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, use asyncio.run for the circuit breaker logic
            async def async_call():
                return await breaker.call(func, *args, **kwargs)

            try:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(async_call())
            except RuntimeError:
                # No event loop running, create new one
                return asyncio.run(async_call())

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


# Predefined circuit breaker configurations for common services
SERVICE_CIRCUIT_CONFIGS = {
    'ocr_service': CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout_duration=120,  # OCR might need more time
        monitor_window=600
    ),
    'email_service': CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=3,
        timeout_duration=60,
        monitor_window=300
    ),
    'telegram_api': CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout_duration=30,
        monitor_window=180
    ),
    'webhook_service': CircuitBreakerConfig(
        failure_threshold=4,
        success_threshold=2,
        timeout_duration=45,
        monitor_window=240
    )
}


def get_service_circuit_breaker(service_name: str) -> CircuitBreaker:
    """Get circuit breaker for a specific service with predefined config"""
    config = SERVICE_CIRCUIT_CONFIGS.get(service_name, CircuitBreakerConfig())
    return CircuitBreakerRegistry.get_breaker(service_name, config)