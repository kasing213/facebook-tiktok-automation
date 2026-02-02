# app/services/cache_service.py
"""
Service caching layer with Redis backend and in-memory fallback.
"""
import json
import hashlib
import pickle
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List, Callable, Union
from functools import wraps
import logging

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """Abstract cache backend interface"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value with TTL"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key"""
        pass

    @abstractmethod
    async def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern"""
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        """Check if backend is healthy"""
        pass


class RedisBackend(CacheBackend):
    """Redis cache backend"""

    def __init__(self):
        self.redis_client = None
        self._initialize_redis()

    def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            settings = get_settings()
            if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=False,  # We handle encoding ourselves
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache backend initialized successfully")
            else:
                logger.warning("Redis URL not configured, Redis backend unavailable")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis backend: {e}")
            self.redis_client = None

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        if not self.redis_client:
            return None

        try:
            data = self.redis_client.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Redis get failed for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in Redis with TTL"""
        if not self.redis_client:
            return False

        try:
            serialized = pickle.dumps(value)
            return self.redis_client.setex(key, ttl, serialized)
        except Exception as e:
            logger.warning(f"Redis set failed for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not self.redis_client:
            return False

        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.warning(f"Redis delete failed for key {key}: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern"""
        if not self.redis_client:
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Redis clear pattern failed for {pattern}: {e}")
            return 0

    def is_healthy(self) -> bool:
        """Check Redis health"""
        try:
            return bool(self.redis_client and self.redis_client.ping())
        except Exception:
            return False


class MemoryBackend(CacheBackend):
    """In-memory cache backend with TTL support"""

    def __init__(self, max_size: int = 10000):
        self._cache: Dict[str, Dict] = {}
        self._max_size = max_size

    def _cleanup_expired(self):
        """Remove expired entries"""
        now = datetime.utcnow()
        expired_keys = [
            key for key, data in self._cache.items()
            if data['expires_at'] and data['expires_at'] < now
        ]
        for key in expired_keys:
            del self._cache[key]

    def _evict_if_needed(self):
        """Evict oldest entries if cache is full"""
        if len(self._cache) >= self._max_size:
            # Remove oldest 20% of entries
            to_remove = int(self._max_size * 0.2)
            sorted_items = sorted(
                self._cache.items(),
                key=lambda x: x[1]['created_at']
            )
            for key, _ in sorted_items[:to_remove]:
                del self._cache[key]

    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache"""
        self._cleanup_expired()

        if key not in self._cache:
            return None

        data = self._cache[key]
        if data['expires_at'] and data['expires_at'] < datetime.utcnow():
            del self._cache[key]
            return None

        return data['value']

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in memory cache"""
        self._evict_if_needed()

        expires_at = datetime.utcnow() + timedelta(seconds=ttl) if ttl > 0 else None

        self._cache[key] = {
            'value': value,
            'created_at': datetime.utcnow(),
            'expires_at': expires_at
        }
        return True

    async def delete(self, key: str) -> bool:
        """Delete key from memory cache"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    async def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern (basic wildcard support)"""
        pattern = pattern.replace('*', '')  # Simple pattern matching
        keys_to_delete = [key for key in self._cache.keys() if pattern in key]
        count = len(keys_to_delete)

        for key in keys_to_delete:
            del self._cache[key]

        return count

    def is_healthy(self) -> bool:
        """Memory cache is always healthy"""
        return True


class ServiceCache:
    """
    Service-level cache with automatic fallback and cache invalidation.
    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.primary_backend: CacheBackend = RedisBackend() if REDIS_AVAILABLE else MemoryBackend()
        self.fallback_backend: CacheBackend = MemoryBackend(max_size=1000)

        # Cache configuration per service
        self.cache_config = {
            'OCRService': {'default_ttl': 3600, 'max_size': 5000},  # 1 hour
            'TenantService': {'default_ttl': 1800, 'max_size': 1000},  # 30 minutes
            'ProductImageService': {'default_ttl': 7200, 'max_size': 2000},  # 2 hours
            'ContentModerationService': {'default_ttl': 3600, 'max_size': 1000},  # 1 hour
            'AuthService': {'default_ttl': 900, 'max_size': 5000},  # 15 minutes
        }

        self.default_ttl = self.cache_config.get(service_name, {}).get('default_ttl', 300)

    def _make_key(self, method_name: str, *args, **kwargs) -> str:
        """Generate cache key from method name and arguments"""
        # Create deterministic key from arguments
        key_parts = [self.service_name, method_name]

        # Add args
        if args:
            args_str = str(hash(str(args)))
            key_parts.append(args_str)

        # Add kwargs (sorted for consistency)
        if kwargs:
            # Remove non-cacheable kwargs
            cacheable_kwargs = {
                k: v for k, v in kwargs.items()
                if not k.startswith('_') and k not in ['db', 'session']
            }
            if cacheable_kwargs:
                kwargs_str = str(hash(str(sorted(cacheable_kwargs.items()))))
                key_parts.append(kwargs_str)

        return ':'.join(key_parts)

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with fallback"""
        # Try primary backend first
        if self.primary_backend.is_healthy():
            value = await self.primary_backend.get(key)
            if value is not None:
                return value

        # Fallback to secondary backend
        return await self.fallback_backend.get(key)

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache"""
        if ttl is None:
            ttl = self.default_ttl

        success = False

        # Set in primary backend
        if self.primary_backend.is_healthy():
            success = await self.primary_backend.set(key, value, ttl)

        # Always set in fallback
        fallback_success = await self.fallback_backend.set(key, value, ttl)

        return success or fallback_success

    async def delete(self, key: str) -> bool:
        """Delete from all backends"""
        results = []

        if self.primary_backend.is_healthy():
            results.append(await self.primary_backend.delete(key))

        results.append(await self.fallback_backend.delete(key))

        return any(results)

    async def clear_service_cache(self) -> int:
        """Clear all cache entries for this service"""
        pattern = f"{self.service_name}:*"
        count = 0

        if self.primary_backend.is_healthy():
            count += await self.primary_backend.clear_pattern(pattern)

        count += await self.fallback_backend.clear_pattern(pattern)

        logger.info(f"Cleared {count} cache entries for {self.service_name}")
        return count

    async def cached_call(
        self,
        method: Callable,
        method_name: str,
        ttl: int = None,
        force_refresh: bool = False,
        *args,
        **kwargs
    ) -> Any:
        """Execute method with caching"""
        cache_key = self._make_key(method_name, *args, **kwargs)

        # Try to get from cache first (unless force refresh)
        if not force_refresh:
            cached_value = await self.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {self.service_name}.{method_name}")
                return cached_value

        # Execute method
        logger.debug(f"Cache miss for {self.service_name}.{method_name}, executing method")
        result = await method(*args, **kwargs) if hasattr(method, '__call__') else method

        # Cache the result
        await self.set(cache_key, result, ttl)

        return result

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "service": self.service_name,
            "primary_backend": type(self.primary_backend).__name__,
            "primary_healthy": self.primary_backend.is_healthy(),
            "fallback_backend": type(self.fallback_backend).__name__,
            "fallback_healthy": self.fallback_backend.is_healthy(),
            "default_ttl": self.default_ttl
        }


def cached_method(ttl: int = None, skip_args: List[str] = None):
    """
    Decorator for caching service method results.

    Args:
        ttl: Time to live in seconds (uses service default if None)
        skip_args: List of argument names to skip in cache key generation
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            # Initialize cache if not present
            if not hasattr(self, '_service_cache'):
                self._service_cache = ServiceCache(self.__class__.__name__)

            # Remove skip_args from kwargs for cache key
            if skip_args:
                cache_kwargs = {k: v for k, v in kwargs.items() if k not in skip_args}
            else:
                cache_kwargs = kwargs

            return await self._service_cache.cached_call(
                func,
                func.__name__,
                ttl,
                False,  # force_refresh
                self,
                *args,
                **cache_kwargs
            )

        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            # For sync methods, execute directly (no caching for sync methods)
            return func(self, *args, **kwargs)

        # Return appropriate wrapper
        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


class CacheManager:
    """Global cache manager for all services"""

    _service_caches: Dict[str, ServiceCache] = {}

    @classmethod
    def get_service_cache(cls, service_name: str) -> ServiceCache:
        """Get or create cache for service"""
        if service_name not in cls._service_caches:
            cls._service_caches[service_name] = ServiceCache(service_name)
        return cls._service_caches[service_name]

    @classmethod
    async def clear_all_caches(cls) -> Dict[str, int]:
        """Clear all service caches"""
        results = {}
        for service_name, cache in cls._service_caches.items():
            results[service_name] = await cache.clear_service_cache()
        return results

    @classmethod
    def get_global_cache_stats(cls) -> Dict[str, Any]:
        """Get statistics for all service caches"""
        return {
            service_name: cache.get_cache_stats()
            for service_name, cache in cls._service_caches.items()
        }