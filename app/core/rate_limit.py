# app/core/rate_limit.py
"""
Rate limiting utilities for API calls to external services.

Provides both token bucket and sliding window rate limiters to prevent
exceeding API rate limits for Facebook, TikTok, and other third-party services.
"""
from __future__ import annotations
import asyncio
import time
from typing import Optional
from collections import deque
from dataclasses import dataclass, field


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    max_requests: int  # Maximum number of requests allowed
    time_window: float  # Time window in seconds
    burst_size: Optional[int] = None  # Maximum burst size (defaults to max_requests)

    def __post_init__(self):
        if self.burst_size is None:
            self.burst_size = self.max_requests


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter implementation.

    Allows bursts up to burst_size, refilling at a steady rate.
    Suitable for APIs that allow temporary bursts but enforce average rate limits.

    Example:
        # Allow 100 requests per minute, burst up to 20
        limiter = TokenBucketRateLimiter(max_requests=100, time_window=60, burst_size=20)

        async with limiter:
            # Make API call here
            response = await api_client.get("/data")
    """

    def __init__(self, max_requests: int, time_window: float, burst_size: Optional[int] = None):
        """
        Initialize token bucket rate limiter.

        Args:
            max_requests: Maximum requests allowed per time window
            time_window: Time window in seconds
            burst_size: Maximum burst capacity (defaults to max_requests)
        """
        self.config = RateLimitConfig(max_requests, time_window, burst_size)
        self.tokens = float(self.config.burst_size)
        self.last_refill = time.monotonic()
        self.lock = asyncio.Lock()
        self.refill_rate = self.config.max_requests / self.config.time_window

    async def acquire(self, tokens: int = 1) -> bool:
        """
        Acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire (default: 1)

        Returns:
            True if tokens were acquired, False otherwise
        """
        async with self.lock:
            await self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def wait_for_token(self, tokens: int = 1):
        """
        Wait until tokens are available, then acquire them.

        Args:
            tokens: Number of tokens to acquire (default: 1)
        """
        while True:
            acquired = await self.acquire(tokens)
            if acquired:
                return

            # Calculate wait time until we have enough tokens
            async with self.lock:
                await self._refill()
                tokens_needed = tokens - self.tokens
                if tokens_needed > 0:
                    wait_time = tokens_needed / self.refill_rate
                    await asyncio.sleep(min(wait_time, 0.1))  # Check at least every 100ms
                else:
                    await asyncio.sleep(0.01)  # Brief pause before retry

    async def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_refill

        # Add tokens based on refill rate and elapsed time
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.tokens + new_tokens, self.config.burst_size)
        self.last_refill = now

    async def __aenter__(self):
        """Context manager entry - acquire a token."""
        await self.wait_for_token()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        return False

    def get_available_tokens(self) -> float:
        """Get current number of available tokens."""
        return self.tokens


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter implementation.

    Tracks timestamps of recent requests and enforces strict rate limits
    based on a sliding time window.

    Example:
        # Allow 10 requests per 60 seconds
        limiter = SlidingWindowRateLimiter(max_requests=10, time_window=60)

        async with limiter:
            # Make API call here
            response = await api_client.get("/data")
    """

    def __init__(self, max_requests: int, time_window: float):
        """
        Initialize sliding window rate limiter.

        Args:
            max_requests: Maximum requests allowed per time window
            time_window: Time window in seconds
        """
        self.config = RateLimitConfig(max_requests, time_window)
        self.requests: deque[float] = deque()
        self.lock = asyncio.Lock()

    async def acquire(self) -> bool:
        """
        Try to acquire permission to make a request.

        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        async with self.lock:
            now = time.monotonic()
            cutoff = now - self.config.time_window

            # Remove expired timestamps
            while self.requests and self.requests[0] < cutoff:
                self.requests.popleft()

            # Check if we can make a request
            if len(self.requests) < self.config.max_requests:
                self.requests.append(now)
                return True

            return False

    async def wait_for_slot(self):
        """Wait until a request slot is available."""
        while True:
            acquired = await self.acquire()
            if acquired:
                return

            # Calculate wait time until oldest request expires
            async with self.lock:
                if self.requests:
                    oldest = self.requests[0]
                    now = time.monotonic()
                    wait_time = (oldest + self.config.time_window) - now
                    if wait_time > 0:
                        await asyncio.sleep(min(wait_time + 0.01, 0.1))
                    else:
                        await asyncio.sleep(0.01)
                else:
                    await asyncio.sleep(0.01)

    async def __aenter__(self):
        """Context manager entry - wait for a slot."""
        await self.wait_for_slot()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        return False

    def get_request_count(self) -> int:
        """Get current number of requests in the window."""
        return len(self.requests)

    def get_remaining_requests(self) -> int:
        """Get number of remaining requests allowed."""
        return max(0, self.config.max_requests - len(self.requests))


class CompositeRateLimiter:
    """
    Composite rate limiter that enforces multiple rate limits.

    Useful for APIs with multiple rate limit tiers (e.g., per-second, per-minute, per-hour).

    Example:
        limiter = CompositeRateLimiter([
            SlidingWindowRateLimiter(max_requests=5, time_window=1),    # 5/second
            SlidingWindowRateLimiter(max_requests=100, time_window=60),  # 100/minute
            SlidingWindowRateLimiter(max_requests=1000, time_window=3600) # 1000/hour
        ])

        async with limiter:
            response = await api_client.get("/data")
    """

    def __init__(self, limiters: list[TokenBucketRateLimiter | SlidingWindowRateLimiter]):
        """
        Initialize composite rate limiter.

        Args:
            limiters: List of rate limiters to enforce
        """
        self.limiters = limiters

    async def acquire(self) -> bool:
        """
        Try to acquire permission from all limiters.

        Returns:
            True if all limiters allow the request, False otherwise
        """
        for limiter in self.limiters:
            if not await limiter.acquire():
                return False
        return True

    async def wait_for_slot(self):
        """Wait until all limiters allow a request."""
        # Wait for each limiter in sequence
        for limiter in self.limiters:
            if isinstance(limiter, TokenBucketRateLimiter):
                await limiter.wait_for_token()
            else:
                await limiter.wait_for_slot()

    async def __aenter__(self):
        """Context manager entry - wait for all limiters."""
        await self.wait_for_slot()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        return False


# Predefined rate limiters for common platforms
class PlatformRateLimiters:
    """Predefined rate limiters for common platforms."""

    @staticmethod
    def facebook_graph_api() -> CompositeRateLimiter:
        """
        Rate limiter for Facebook Graph API.

        Facebook Graph API limits:
        - 200 calls per hour per user
        - Burst handling with token bucket
        """
        return CompositeRateLimiter([
            TokenBucketRateLimiter(max_requests=200, time_window=3600, burst_size=10),
        ])

    @staticmethod
    def tiktok_api() -> CompositeRateLimiter:
        """
        Rate limiter for TikTok API.

        TikTok API limits vary by endpoint, but common limits:
        - 100 requests per minute per app
        """
        return CompositeRateLimiter([
            SlidingWindowRateLimiter(max_requests=100, time_window=60),
            TokenBucketRateLimiter(max_requests=100, time_window=60, burst_size=10),
        ])

    @staticmethod
    def conservative() -> CompositeRateLimiter:
        """
        Conservative rate limiter for unknown APIs.

        - 10 requests per second
        - 300 requests per minute
        - 5000 requests per hour
        """
        return CompositeRateLimiter([
            SlidingWindowRateLimiter(max_requests=10, time_window=1),
            SlidingWindowRateLimiter(max_requests=300, time_window=60),
            SlidingWindowRateLimiter(max_requests=5000, time_window=3600),
        ])
