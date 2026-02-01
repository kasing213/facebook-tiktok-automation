# app/core/cache.py
"""
In-memory caching layer to reduce database pressure.

Uses TTL-based caching to store frequently accessed data and reduce redundant queries.
This is particularly effective for:
- User session data
- Tenant configurations
- Frequently accessed lookups
- Stats and aggregations
"""
import time
import threading
from typing import Any, Dict, Optional, TypeVar, Callable, Union
from functools import wraps
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

@dataclass
class CacheEntry:
    """Cache entry with TTL and metadata"""
    value: Any
    expires_at: float
    created_at: float
    hit_count: int = 0
    key: str = ""

class TTLCache:
    """
    Thread-safe TTL (Time To Live) cache with automatic cleanup.

    Features:
    - Configurable TTL per entry
    - Automatic expired entry cleanup
    - Thread-safe operations
    - Memory usage limits
    - Cache statistics
    """

    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        self.default_ttl = default_ttl  # seconds
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'cleanups': 0
        }

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._stats['misses'] += 1
                return None

            if time.time() > entry.expires_at:
                # Expired, remove it
                del self._cache[key]
                self._stats['misses'] += 1
                return None

            # Cache hit
            entry.hit_count += 1
            self._stats['hits'] += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL"""
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl

        with self._lock:
            # Check if we need to evict entries
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()

            self._cache[key] = CacheEntry(
                value=value,
                expires_at=expires_at,
                created_at=time.time(),
                key=key
            )

    def delete(self, key: str) -> bool:
        """Remove key from cache"""
        with self._lock:
            return self._cache.pop(key, None) is not None

    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items"""
        current_time = time.time()
        removed_count = 0

        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if current_time > entry.expires_at
            ]

            for key in expired_keys:
                del self._cache[key]
                removed_count += 1

            if removed_count > 0:
                self._stats['cleanups'] += 1
                logger.debug(f"Cleaned up {removed_count} expired cache entries")

        return removed_count

    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self._cache:
            return

        # Find entry with lowest hit count and oldest creation time
        lru_key = min(
            self._cache.keys(),
            key=lambda k: (self._cache[k].hit_count, self._cache[k].created_at)
        )

        del self._cache[lru_key]
        self._stats['evictions'] += 1

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0

            return {
                **self._stats,
                'size': len(self._cache),
                'max_size': self.max_size,
                'hit_rate': round(hit_rate * 100, 2),
                'memory_usage_estimate': len(self._cache) * 100  # rough estimate
            }

# Global cache instances
_app_cache = TTLCache(default_ttl=300, max_size=1000)  # 5 minutes, 1000 entries
_user_cache = TTLCache(default_ttl=900, max_size=500)   # 15 minutes, 500 users
_tenant_cache = TTLCache(default_ttl=1800, max_size=200) # 30 minutes, 200 tenants

def cache_key(prefix: str, *args, tenant_id: Optional[str] = None) -> str:
    """Generate consistent cache key with optional tenant isolation"""
    key_parts = [prefix]
    if tenant_id:
        key_parts.append(f"tenant:{tenant_id}")
    key_parts.extend(str(arg) for arg in args)
    return ":".join(key_parts)

def cached(
    ttl: int = 300,
    cache_instance: TTLCache = None,
    key_prefix: str = "",
    include_tenant: bool = True
) -> Callable:
    """
    Decorator for caching function results.

    Args:
        ttl: Time to live in seconds
        cache_instance: Cache instance to use (defaults to app_cache)
        key_prefix: Prefix for cache keys
        include_tenant: Whether to include tenant_id in cache key
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache = cache_instance or _app_cache
        prefix = key_prefix or func.__name__

        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Extract tenant_id if present for key generation
            tenant_id = None
            if include_tenant:
                tenant_id = kwargs.get('tenant_id') or (
                    str(args[0]) if args and hasattr(args[0], 'hex') else None
                )

            # Generate cache key
            key_args = args + tuple(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            key = cache_key(prefix, *key_args, tenant_id=tenant_id)

            # Try cache first
            result = cache.get(key)
            if result is not None:
                return result

            # Cache miss, execute function
            result = func(*args, **kwargs)

            # Cache result if not None
            if result is not None:
                cache.set(key, result, ttl)

            return result

        # Add cache management methods
        wrapper.cache_clear = lambda: cache.clear()
        wrapper.cache_stats = lambda: cache.stats()

        return wrapper

    return decorator

def cache_tenant_data(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for caching tenant-specific data with longer TTL"""
    return cached(ttl=1800, cache_instance=_tenant_cache, include_tenant=True)(func)

def cache_user_data(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for caching user-specific data"""
    return cached(ttl=900, cache_instance=_user_cache, include_tenant=True)(func)

def cache_stats() -> Dict[str, Any]:
    """Get stats for all cache instances"""
    return {
        'app_cache': _app_cache.stats(),
        'user_cache': _user_cache.stats(),
        'tenant_cache': _tenant_cache.stats()
    }

def cleanup_all_caches() -> Dict[str, int]:
    """Cleanup expired entries in all caches"""
    return {
        'app_cache': _app_cache.cleanup_expired(),
        'user_cache': _user_cache.cleanup_expired(),
        'tenant_cache': _tenant_cache.cleanup_expired()
    }

def clear_all_caches() -> None:
    """Clear all cache instances"""
    _app_cache.clear()
    _user_cache.clear()
    _tenant_cache.clear()
    logger.info("All caches cleared")

# Cache invalidation helpers
def invalidate_user_cache(tenant_id: str, user_id: str = None) -> None:
    """Invalidate user-related cache entries"""
    if user_id:
        key = cache_key("user", user_id, tenant_id=tenant_id)
        _user_cache.delete(key)
    else:
        # Clear all user cache for tenant (expensive but thorough)
        keys_to_delete = [
            key for key in _user_cache._cache.keys()
            if f"tenant:{tenant_id}" in key
        ]
        for key in keys_to_delete:
            _user_cache.delete(key)

def invalidate_tenant_cache(tenant_id: str) -> None:
    """Invalidate tenant-related cache entries"""
    keys_to_delete = [
        key for key in _tenant_cache._cache.keys()
        if f"tenant:{tenant_id}" in key or tenant_id in key
    ]
    for key in keys_to_delete:
        _tenant_cache.delete(key)

# Background cleanup task
def start_cache_cleanup_task():
    """Start background task to cleanup expired cache entries"""
    import threading
    import time

    def cleanup_task():
        while True:
            try:
                time.sleep(300)  # Run every 5 minutes
                cleanup_all_caches()
            except Exception as e:
                logger.error(f"Cache cleanup task error: {e}")

    thread = threading.Thread(target=cleanup_task, daemon=True)
    thread.start()
    logger.info("Cache cleanup task started")