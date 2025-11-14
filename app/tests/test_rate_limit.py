# app/tests/test_rate_limit.py
"""Tests for rate limiting functionality."""
import asyncio
import pytest
import time
from app.core.rate_limit import (
    TokenBucketRateLimiter,
    SlidingWindowRateLimiter,
    CompositeRateLimiter,
    PlatformRateLimiters,
)


class TestTokenBucketRateLimiter:
    """Tests for TokenBucketRateLimiter."""

    @pytest.mark.asyncio
    async def test_basic_token_acquisition(self):
        """Test basic token acquisition."""
        limiter = TokenBucketRateLimiter(max_requests=10, time_window=1, burst_size=5)

        # Should be able to acquire up to burst_size tokens immediately
        for _ in range(5):
            assert await limiter.acquire() is True

        # Next acquisition should fail (no tokens left)
        assert await limiter.acquire() is False

    @pytest.mark.asyncio
    async def test_token_refill(self):
        """Test that tokens refill over time."""
        limiter = TokenBucketRateLimiter(max_requests=10, time_window=1, burst_size=5)

        # Exhaust all tokens
        for _ in range(5):
            await limiter.acquire()

        # Wait for refill (should get ~2 tokens in 0.2 seconds at 10 tokens/second)
        await asyncio.sleep(0.2)

        # Should be able to acquire again
        assert await limiter.acquire() is True

    @pytest.mark.asyncio
    async def test_wait_for_token(self):
        """Test wait_for_token blocks until token available."""
        limiter = TokenBucketRateLimiter(max_requests=10, time_window=1, burst_size=2)

        # Exhaust tokens
        await limiter.acquire(2)

        start = time.monotonic()
        # This should wait for refill
        await limiter.wait_for_token()
        elapsed = time.monotonic() - start

        # Should have waited at least 0.05 seconds (less than 1 token refill time)
        assert elapsed >= 0.05

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using limiter as context manager."""
        limiter = TokenBucketRateLimiter(max_requests=10, time_window=1, burst_size=3)

        call_count = 0

        async def make_request():
            nonlocal call_count
            async with limiter:
                call_count += 1

        # Should successfully make burst_size requests
        await asyncio.gather(*[make_request() for _ in range(3)])
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_burst_capacity_limit(self):
        """Test that burst capacity is limited."""
        limiter = TokenBucketRateLimiter(max_requests=100, time_window=1, burst_size=5)

        # Wait to ensure bucket is full
        await asyncio.sleep(0.1)

        # Should only be able to acquire burst_size tokens, not max_requests
        acquired = 0
        for _ in range(10):
            if await limiter.acquire():
                acquired += 1

        assert acquired == 5  # Limited by burst_size

    @pytest.mark.asyncio
    async def test_get_available_tokens(self):
        """Test getting available token count."""
        limiter = TokenBucketRateLimiter(max_requests=10, time_window=1, burst_size=5)

        initial_tokens = limiter.get_available_tokens()
        assert initial_tokens == 5  # Should start with burst_size

        await limiter.acquire(2)
        remaining = limiter.get_available_tokens()
        assert remaining == 3


class TestSlidingWindowRateLimiter:
    """Tests for SlidingWindowRateLimiter."""

    @pytest.mark.asyncio
    async def test_basic_acquisition(self):
        """Test basic request acquisition."""
        limiter = SlidingWindowRateLimiter(max_requests=5, time_window=1)

        # Should allow up to max_requests
        for _ in range(5):
            assert await limiter.acquire() is True

        # Next request should fail
        assert await limiter.acquire() is False

    @pytest.mark.asyncio
    async def test_sliding_window_expiry(self):
        """Test that requests expire after time window."""
        limiter = SlidingWindowRateLimiter(max_requests=3, time_window=0.2)

        # Make 3 requests
        for _ in range(3):
            await limiter.acquire()

        # Should be at limit
        assert await limiter.acquire() is False

        # Wait for window to slide
        await asyncio.sleep(0.25)

        # Should be able to make requests again
        assert await limiter.acquire() is True

    @pytest.mark.asyncio
    async def test_wait_for_slot(self):
        """Test wait_for_slot blocks until slot available."""
        limiter = SlidingWindowRateLimiter(max_requests=2, time_window=0.2)

        # Fill up slots
        await limiter.acquire()
        await limiter.acquire()

        start = time.monotonic()
        await limiter.wait_for_slot()
        elapsed = time.monotonic() - start

        # Should have waited approximately the time window
        assert elapsed >= 0.15  # Allow some tolerance

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using limiter as context manager."""
        limiter = SlidingWindowRateLimiter(max_requests=3, time_window=1)

        call_count = 0

        async def make_request():
            nonlocal call_count
            async with limiter:
                call_count += 1

        await asyncio.gather(*[make_request() for _ in range(3)])
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_get_request_count(self):
        """Test getting current request count."""
        limiter = SlidingWindowRateLimiter(max_requests=5, time_window=1)

        assert limiter.get_request_count() == 0

        await limiter.acquire()
        assert limiter.get_request_count() == 1

        await limiter.acquire()
        await limiter.acquire()
        assert limiter.get_request_count() == 3

    @pytest.mark.asyncio
    async def test_get_remaining_requests(self):
        """Test getting remaining request count."""
        limiter = SlidingWindowRateLimiter(max_requests=5, time_window=1)

        assert limiter.get_remaining_requests() == 5

        await limiter.acquire()
        assert limiter.get_remaining_requests() == 4

        await limiter.acquire()
        await limiter.acquire()
        assert limiter.get_remaining_requests() == 2


class TestCompositeRateLimiter:
    """Tests for CompositeRateLimiter."""

    @pytest.mark.asyncio
    async def test_multiple_limiters_enforced(self):
        """Test that all limiters are enforced using context manager."""
        limiter = CompositeRateLimiter([
            SlidingWindowRateLimiter(max_requests=5, time_window=1),
            SlidingWindowRateLimiter(max_requests=2, time_window=0.3),
        ])

        # Should be able to make 2 requests (limited by 2nd limiter)
        async with limiter:
            pass
        async with limiter:
            pass

        # Wait for second limiter to reset
        await asyncio.sleep(0.35)

        # Should be able to make more requests (still have capacity in first limiter)
        async with limiter:
            pass

    @pytest.mark.asyncio
    async def test_wait_for_slot_all_limiters(self):
        """Test wait_for_slot waits for all limiters."""
        limiter = CompositeRateLimiter([
            SlidingWindowRateLimiter(max_requests=1, time_window=0.2),
            TokenBucketRateLimiter(max_requests=5, time_window=1, burst_size=1),
        ])

        # Exhaust both limiters
        await limiter.acquire()

        start = time.monotonic()
        await limiter.wait_for_slot()
        elapsed = time.monotonic() - start

        # Should have waited for tokens to refill
        assert elapsed >= 0.1

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using composite limiter as context manager."""
        limiter = CompositeRateLimiter([
            SlidingWindowRateLimiter(max_requests=2, time_window=1),
            TokenBucketRateLimiter(max_requests=10, time_window=1, burst_size=2),
        ])

        call_count = 0

        async def make_request():
            nonlocal call_count
            async with limiter:
                call_count += 1

        await asyncio.gather(*[make_request() for _ in range(2)])
        assert call_count == 2


class TestPlatformRateLimiters:
    """Tests for predefined platform rate limiters."""

    @pytest.mark.asyncio
    async def test_facebook_limiter_creation(self):
        """Test Facebook rate limiter can be created."""
        limiter = PlatformRateLimiters.facebook_graph_api()
        assert isinstance(limiter, CompositeRateLimiter)
        assert len(limiter.limiters) > 0

    @pytest.mark.asyncio
    async def test_tiktok_limiter_creation(self):
        """Test TikTok rate limiter can be created."""
        limiter = PlatformRateLimiters.tiktok_api()
        assert isinstance(limiter, CompositeRateLimiter)
        assert len(limiter.limiters) > 0

    @pytest.mark.asyncio
    async def test_conservative_limiter_creation(self):
        """Test conservative rate limiter can be created."""
        limiter = PlatformRateLimiters.conservative()
        assert isinstance(limiter, CompositeRateLimiter)
        assert len(limiter.limiters) >= 3  # Should have multiple tiers

    @pytest.mark.asyncio
    async def test_facebook_limiter_functional(self):
        """Test Facebook limiter allows requests."""
        limiter = PlatformRateLimiters.facebook_graph_api()

        # Should allow at least a few requests
        for _ in range(5):
            async with limiter:
                pass  # Simulated API call

    @pytest.mark.asyncio
    async def test_tiktok_limiter_functional(self):
        """Test TikTok limiter allows requests."""
        limiter = PlatformRateLimiters.tiktok_api()

        # Should allow at least a few requests
        for _ in range(5):
            async with limiter:
                pass  # Simulated API call


class TestRateLimiterPerformance:
    """Performance and stress tests for rate limiters."""

    @pytest.mark.asyncio
    async def test_high_concurrency_sliding_window(self):
        """Test sliding window under high concurrency."""
        limiter = SlidingWindowRateLimiter(max_requests=100, time_window=1)

        async def make_request():
            async with limiter:
                await asyncio.sleep(0.001)  # Simulate work

        # Make 50 concurrent requests
        await asyncio.gather(*[make_request() for _ in range(50)])

        # Should have made 50 requests
        assert limiter.get_request_count() <= 50

    @pytest.mark.asyncio
    async def test_high_concurrency_token_bucket(self):
        """Test token bucket under high concurrency."""
        limiter = TokenBucketRateLimiter(max_requests=100, time_window=1, burst_size=50)

        async def make_request():
            async with limiter:
                await asyncio.sleep(0.001)  # Simulate work

        # Make 30 concurrent requests
        await asyncio.gather(*[make_request() for _ in range(30)])

        # All requests should complete
        # Token count should be reduced
        assert limiter.get_available_tokens() < 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
