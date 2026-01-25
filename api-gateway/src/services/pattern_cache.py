# api-gateway/src/services/pattern_cache.py
"""
Pattern Cache Service for Auto-Learning OCR

Manages in-memory caching of bank extraction patterns with automatic
invalidation and updates. This ensures fast pattern matching while
keeping patterns fresh with new learning data.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from collections import defaultdict

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)


class PatternCache:
    """
    Manages caching of bank extraction patterns for fast OCR processing.

    Features:
    - In-memory cache for sub-millisecond pattern access
    - TTL-based cache invalidation
    - Automatic pattern updates from learning queue
    - Performance monitoring and statistics
    """

    def __init__(self, ttl_hours: int = 1):
        self.patterns = {}  # {bank_code: pattern_data}
        self.cache_times = {}  # {bank_code: cached_at_timestamp}
        self.access_counts = defaultdict(int)  # {bank_code: access_count}
        self.hit_rates = defaultdict(lambda: defaultdict(int))  # {bank_code: {hits: x, misses: y}}

        self.ttl = timedelta(hours=ttl_hours)
        self.last_cleanup = datetime.now(timezone.utc)
        self.cleanup_interval = timedelta(minutes=30)

        # Statistics
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'patterns_loaded': 0,
            'patterns_updated': 0,
            'last_update': None
        }

    def get_patterns(self, bank_code: str) -> Optional[Dict[str, Any]]:
        """
        Get patterns for a bank from cache.

        Returns:
            Pattern data if found and valid, None if expired or missing
        """
        if bank_code not in self.patterns:
            self.stats['cache_misses'] += 1
            self.hit_rates[bank_code]['misses'] += 1
            return None

        # Check if cache is expired
        cached_at = self.cache_times.get(bank_code)
        if cached_at:
            age = datetime.now(timezone.utc) - cached_at
            if age > self.ttl:
                # Cache expired - remove it
                self._remove_expired_pattern(bank_code)
                self.stats['cache_misses'] += 1
                self.hit_rates[bank_code]['misses'] += 1
                return None

        # Cache hit
        self.access_counts[bank_code] += 1
        self.stats['cache_hits'] += 1
        self.hit_rates[bank_code]['hits'] += 1

        return self.patterns[bank_code]

    def set_patterns(self, bank_code: str, pattern_data: Dict[str, Any]) -> None:
        """
        Store patterns for a bank in cache.

        Args:
            bank_code: Bank identifier (ABA, ACLEDA, etc.)
            pattern_data: Pattern template data from database
        """
        self.patterns[bank_code] = pattern_data.copy()
        self.cache_times[bank_code] = datetime.now(timezone.utc)
        self.stats['patterns_loaded'] += 1
        self.stats['last_update'] = datetime.now(timezone.utc).isoformat()

        logger.debug(f"Cached patterns for {bank_code}")

    def update_patterns(self, bank_code: str, new_patterns: List[Dict[str, Any]]) -> None:
        """
        Update existing patterns with new learned patterns.

        Args:
            bank_code: Bank identifier
            new_patterns: List of new pattern objects to add
        """
        if bank_code not in self.patterns:
            logger.warning(f"Cannot update patterns for {bank_code} - not in cache")
            return

        current_patterns = self.patterns[bank_code]
        existing_pattern_list = current_patterns.get('patterns', [])

        # Add new patterns at the beginning (higher priority)
        for pattern in new_patterns:
            pattern['added_via_update'] = True
            pattern['updated_at'] = datetime.now(timezone.utc).isoformat()
            existing_pattern_list.insert(0, pattern)

        # Limit total patterns per bank to prevent memory bloat
        max_patterns_per_type = 5
        pattern_counts = defaultdict(int)
        filtered_patterns = []

        for pattern in existing_pattern_list:
            pattern_type = pattern.get('type', 'unknown')
            if pattern_counts[pattern_type] < max_patterns_per_type:
                filtered_patterns.append(pattern)
                pattern_counts[pattern_type] += 1

        current_patterns['patterns'] = filtered_patterns
        current_patterns['last_updated'] = datetime.now(timezone.utc).isoformat()
        current_patterns['update_source'] = 'real_time_learning'

        # Update cache timestamp
        self.cache_times[bank_code] = datetime.now(timezone.utc)
        self.stats['patterns_updated'] += 1

        logger.info(f"Updated {len(new_patterns)} patterns for {bank_code}")

    def invalidate_bank(self, bank_code: str) -> None:
        """Invalidate cache for a specific bank."""
        if bank_code in self.patterns:
            del self.patterns[bank_code]
            del self.cache_times[bank_code]
            logger.debug(f"Invalidated cache for {bank_code}")

    def invalidate_all(self) -> None:
        """Clear entire cache."""
        cache_size = len(self.patterns)
        self.patterns.clear()
        self.cache_times.clear()
        self.access_counts.clear()
        logger.info(f"Invalidated entire cache ({cache_size} banks)")

    def cleanup_expired(self) -> int:
        """
        Remove expired patterns from cache.

        Returns:
            Number of patterns removed
        """
        now = datetime.now(timezone.utc)
        expired_banks = []

        for bank_code, cached_at in self.cache_times.items():
            if now - cached_at > self.ttl:
                expired_banks.append(bank_code)

        for bank_code in expired_banks:
            self._remove_expired_pattern(bank_code)

        self.last_cleanup = now

        if expired_banks:
            logger.info(f"Cleaned up {len(expired_banks)} expired patterns")

        return len(expired_banks)

    def _remove_expired_pattern(self, bank_code: str) -> None:
        """Remove a specific expired pattern."""
        if bank_code in self.patterns:
            del self.patterns[bank_code]
        if bank_code in self.cache_times:
            del self.cache_times[bank_code]

    def should_cleanup(self) -> bool:
        """Check if cleanup should be performed."""
        return datetime.now(timezone.utc) - self.last_cleanup > self.cleanup_interval

    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache statistics and information."""
        now = datetime.now(timezone.utc)

        # Calculate hit rates per bank
        bank_hit_rates = {}
        for bank_code, rates in self.hit_rates.items():
            total = rates['hits'] + rates['misses']
            if total > 0:
                bank_hit_rates[bank_code] = {
                    'hit_rate': rates['hits'] / total,
                    'total_requests': total,
                    'hits': rates['hits'],
                    'misses': rates['misses']
                }

        # Overall hit rate
        total_requests = self.stats['cache_hits'] + self.stats['cache_misses']
        overall_hit_rate = self.stats['cache_hits'] / total_requests if total_requests > 0 else 0

        # Cache age info
        cache_ages = {}
        for bank_code, cached_at in self.cache_times.items():
            age_minutes = (now - cached_at).total_seconds() / 60
            cache_ages[bank_code] = age_minutes

        return {
            'cache_size': len(self.patterns),
            'overall_hit_rate': overall_hit_rate,
            'total_requests': total_requests,
            'bank_hit_rates': bank_hit_rates,
            'cache_ages_minutes': cache_ages,
            'most_accessed_banks': dict(sorted(self.access_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
            'ttl_hours': self.ttl.total_seconds() / 3600,
            'last_cleanup': self.last_cleanup.isoformat(),
            'stats': self.stats.copy()
        }

    def get_pattern_summary(self, bank_code: str) -> Optional[Dict[str, Any]]:
        """Get summary of patterns for a specific bank."""
        patterns = self.get_patterns(bank_code)
        if not patterns:
            return None

        pattern_list = patterns.get('patterns', [])

        # Count patterns by type
        pattern_counts = defaultdict(int)
        confidence_sum = defaultdict(float)

        for pattern in pattern_list:
            pattern_type = pattern.get('type', 'unknown')
            pattern_counts[pattern_type] += 1
            confidence_sum[pattern_type] += pattern.get('confidence', 0)

        # Calculate average confidence per type
        avg_confidence = {}
        for pattern_type, count in pattern_counts.items():
            avg_confidence[pattern_type] = confidence_sum[pattern_type] / count

        cached_at = self.cache_times.get(bank_code)
        cache_age_minutes = (datetime.now(timezone.utc) - cached_at).total_seconds() / 60 if cached_at else None

        return {
            'bank_code': bank_code,
            'total_patterns': len(pattern_list),
            'patterns_by_type': dict(pattern_counts),
            'avg_confidence_by_type': avg_confidence,
            'cache_age_minutes': cache_age_minutes,
            'confidence_base': patterns.get('confidence_base', 0),
            'last_updated': patterns.get('last_updated'),
            'source': patterns.get('source', 'unknown')
        }


class MerchantPatternCache:
    """
    Cache for merchant-specific patterns that adapt to individual user behaviors.

    Each merchant gets their own pattern variations based on their customer names,
    account number formats, and amount patterns.
    """

    def __init__(self, ttl_hours: int = 24):
        self.merchant_patterns = {}  # {tenant_id: {bank_code: patterns}}
        self.pattern_performance = {}  # {tenant_id: {pattern_hash: success_rate}}
        self.cache_times = {}  # {tenant_id: cached_at}
        self.ttl = timedelta(hours=ttl_hours)

    def get_merchant_patterns(self, tenant_id: str, bank_code: str) -> Optional[List[Dict[str, Any]]]:
        """Get merchant-specific patterns for a bank."""
        if tenant_id not in self.merchant_patterns:
            return None

        tenant_patterns = self.merchant_patterns[tenant_id]
        return tenant_patterns.get(bank_code)

    def add_merchant_pattern(
        self,
        tenant_id: str,
        bank_code: str,
        pattern: Dict[str, Any],
        success_rate: float = 1.0
    ) -> None:
        """Add a successful pattern for a merchant."""
        if tenant_id not in self.merchant_patterns:
            self.merchant_patterns[tenant_id] = {}

        if bank_code not in self.merchant_patterns[tenant_id]:
            self.merchant_patterns[tenant_id][bank_code] = []

        # Add pattern with metadata
        pattern_with_meta = pattern.copy()
        pattern_with_meta.update({
            'learned_at': datetime.now(timezone.utc).isoformat(),
            'success_rate': success_rate,
            'usage_count': 1,
            'merchant_specific': True
        })

        self.merchant_patterns[tenant_id][bank_code].append(pattern_with_meta)

        # Update cache time
        self.cache_times[tenant_id] = datetime.now(timezone.utc)

        # Limit patterns per merchant-bank combination
        max_merchant_patterns = 10
        if len(self.merchant_patterns[tenant_id][bank_code]) > max_merchant_patterns:
            # Remove oldest patterns
            self.merchant_patterns[tenant_id][bank_code] = \
                self.merchant_patterns[tenant_id][bank_code][-max_merchant_patterns:]

        logger.debug(f"Added merchant pattern for tenant {tenant_id}, bank {bank_code}")

    def update_pattern_performance(
        self,
        tenant_id: str,
        pattern_hash: str,
        success: bool
    ) -> None:
        """Update success rate for a merchant pattern."""
        if tenant_id not in self.pattern_performance:
            self.pattern_performance[tenant_id] = {}

        if pattern_hash not in self.pattern_performance[tenant_id]:
            self.pattern_performance[tenant_id][pattern_hash] = {
                'successes': 0,
                'attempts': 0,
                'success_rate': 0.0
            }

        perf = self.pattern_performance[tenant_id][pattern_hash]
        perf['attempts'] += 1
        if success:
            perf['successes'] += 1

        perf['success_rate'] = perf['successes'] / perf['attempts']

    def cleanup_expired_merchants(self) -> int:
        """Clean up expired merchant patterns."""
        now = datetime.now(timezone.utc)
        expired_tenants = []

        for tenant_id, cached_at in self.cache_times.items():
            if now - cached_at > self.ttl:
                expired_tenants.append(tenant_id)

        for tenant_id in expired_tenants:
            if tenant_id in self.merchant_patterns:
                del self.merchant_patterns[tenant_id]
            if tenant_id in self.pattern_performance:
                del self.pattern_performance[tenant_id]
            del self.cache_times[tenant_id]

        if expired_tenants:
            logger.info(f"Cleaned up patterns for {len(expired_tenants)} expired merchants")

        return len(expired_tenants)

    def get_merchant_stats(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific merchant."""
        if tenant_id not in self.merchant_patterns:
            return None

        patterns = self.merchant_patterns[tenant_id]
        performance = self.pattern_performance.get(tenant_id, {})

        total_patterns = sum(len(bank_patterns) for bank_patterns in patterns.values())
        avg_success_rate = 0.0

        if performance:
            success_rates = [p['success_rate'] for p in performance.values()]
            avg_success_rate = sum(success_rates) / len(success_rates)

        return {
            'tenant_id': tenant_id,
            'banks_with_patterns': len(patterns),
            'total_patterns': total_patterns,
            'avg_success_rate': avg_success_rate,
            'patterns_by_bank': {bank: len(bank_patterns) for bank, bank_patterns in patterns.items()},
            'cached_at': self.cache_times.get(tenant_id, {}).isoformat() if tenant_id in self.cache_times else None
        }


# Global instances
pattern_cache = PatternCache(ttl_hours=1)
merchant_cache = MerchantPatternCache(ttl_hours=24)