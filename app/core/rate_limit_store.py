# app/core/rate_limit_store.py
"""
Rate limit counter storage with Redis fallback to in-memory
"""
import time
from typing import Optional, Dict, Tuple
from threading import Lock


class RateLimitStore:
    """
    Store for rate limit counters with Redis support and in-memory fallback

    Tracks request counts per key (usually IP address) with automatic expiry.
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize rate limit store

        Args:
            redis_url: Redis connection URL (if None, uses in-memory storage)
        """
        self.redis_url = redis_url
        self.redis_client = None
        self._memory_store: Dict[str, Tuple[int, float]] = {}  # key -> (count, expiry_time)
        self._lock = Lock()

        # Try to connect to Redis if URL provided
        if redis_url:
            try:
                import redis.asyncio as aioredis
                # We'll use sync Redis for simplicity in middleware
                import redis
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self.redis_client.ping()
            except Exception as e:
                print(f"[RateLimitStore] Failed to connect to Redis: {e}, falling back to in-memory")
                self.redis_client = None

    def increment(self, key: str, window: int = 60) -> int:
        """
        Increment counter for key within time window

        Args:
            key: Unique identifier (usually IP address)
            window: Time window in seconds (default: 60)

        Returns:
            Current count after increment
        """
        if self.redis_client:
            return self._increment_redis(key, window)
        else:
            return self._increment_memory(key, window)

    def get_count(self, key: str) -> int:
        """
        Get current count for key

        Args:
            key: Unique identifier

        Returns:
            Current count (0 if not found or expired)
        """
        if self.redis_client:
            return self._get_count_redis(key)
        else:
            return self._get_count_memory(key)

    def reset(self, key: str):
        """
        Reset counter for key

        Args:
            key: Unique identifier to reset
        """
        if self.redis_client:
            self._reset_redis(key)
        else:
            self._reset_memory(key)

    def _increment_redis(self, key: str, window: int) -> int:
        """Increment using Redis"""
        pipeline = self.redis_client.pipeline()
        pipeline.incr(f"rate_limit:{key}")
        pipeline.expire(f"rate_limit:{key}", window)
        results = pipeline.execute()
        return int(results[0])

    def _get_count_redis(self, key: str) -> int:
        """Get count from Redis"""
        count = self.redis_client.get(f"rate_limit:{key}")
        return int(count) if count else 0

    def _reset_redis(self, key: str):
        """Reset counter in Redis"""
        self.redis_client.delete(f"rate_limit:{key}")

    def _increment_memory(self, key: str, window: int) -> int:
        """Increment using in-memory store"""
        with self._lock:
            current_time = time.time()

            # Clean up expired entries periodically (simple approach)
            if len(self._memory_store) > 10000:  # Prevent unbounded growth
                self._cleanup_expired()

            if key in self._memory_store:
                count, expiry = self._memory_store[key]
                if current_time < expiry:
                    # Still valid, increment
                    count += 1
                    self._memory_store[key] = (count, expiry)
                    return count
                else:
                    # Expired, reset
                    self._memory_store[key] = (1, current_time + window)
                    return 1
            else:
                # New key
                self._memory_store[key] = (1, current_time + window)
                return 1

    def _get_count_memory(self, key: str) -> int:
        """Get count from in-memory store"""
        with self._lock:
            if key in self._memory_store:
                count, expiry = self._memory_store[key]
                if time.time() < expiry:
                    return count
                else:
                    # Expired
                    del self._memory_store[key]
                    return 0
            return 0

    def _reset_memory(self, key: str):
        """Reset counter in memory"""
        with self._lock:
            if key in self._memory_store:
                del self._memory_store[key]

    def _cleanup_expired(self):
        """Clean up expired entries from memory store (called with lock held)"""
        current_time = time.time()
        expired_keys = [k for k, (_, expiry) in self._memory_store.items() if current_time >= expiry]
        for k in expired_keys:
            del self._memory_store[k]

    def get_retry_after(self, key: str, window: int = 60) -> int:
        """
        Get seconds until rate limit resets

        Args:
            key: Unique identifier
            window: Time window in seconds

        Returns:
            Seconds until reset (0 if not rate limited)
        """
        if self.redis_client:
            ttl = self.redis_client.ttl(f"rate_limit:{key}")
            return max(0, ttl) if ttl > 0 else 0
        else:
            with self._lock:
                if key in self._memory_store:
                    _, expiry = self._memory_store[key]
                    remaining = expiry - time.time()
                    return max(0, int(remaining))
                return 0
