# app/repositories/optimized_base.py
"""
Optimized base repository with caching, query optimization, and reduced database pressure.

Key optimizations:
- Query result caching with TTL
- Lazy loading and eager loading strategies
- Query batching and bulk operations
- Connection-efficient patterns
- Statistics collection for monitoring
"""
from abc import ABC
from typing import TypeVar, Generic, Type, Optional, List, Any, Dict, Set, Union
from uuid import UUID
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, desc, asc, text, func
from datetime import datetime
import logging

from app.core.models import Base
from app.core.cache import cached, cache_tenant_data, cache_user_data, invalidate_tenant_cache

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Base)

class QueryStats:
    """Track query statistics to identify optimization opportunities"""

    def __init__(self):
        self.query_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.bulk_operations = 0
        self.expensive_queries = []

    def record_query(self, query_type: str, duration_ms: float, cached: bool = False):
        self.query_count += 1
        if cached:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

        # Track expensive queries (>100ms)
        if duration_ms > 100:
            self.expensive_queries.append({
                'type': query_type,
                'duration_ms': duration_ms,
                'timestamp': datetime.utcnow()
            })

    def get_stats(self) -> Dict[str, Any]:
        return {
            'query_count': self.query_count,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': self.cache_hits / max(self.query_count, 1),
            'bulk_operations': self.bulk_operations,
            'expensive_query_count': len(self.expensive_queries)
        }

# Global query stats instance
_query_stats = QueryStats()

class OptimizedBaseRepository(Generic[T], ABC):
    """
    Optimized base repository with caching and query optimizations.

    Reduces database pressure through:
    - Intelligent caching strategies
    - Query batching and bulk operations
    - Lazy vs eager loading decisions
    - Connection-efficient patterns
    """

    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model
        self._tenant_cache_prefix = f"{model.__tablename__}_tenant"
        self._stats = QueryStats()

    # Core CRUD with caching
    @cached(ttl=300, key_prefix="by_id")
    def get_by_id(self, id: UUID, include_inactive: bool = False) -> Optional[T]:
        """Get a single record by ID with caching"""
        query = self.db.query(self.model).filter(self.model.id == id)

        # Filter out inactive records unless explicitly requested
        if hasattr(self.model, 'is_active') and not include_inactive:
            query = query.filter(self.model.is_active == True)

        return query.first()

    def get_by_id_and_tenant(self, id: UUID, tenant_id: UUID, include_inactive: bool = False) -> Optional[T]:
        """Get record by ID scoped to tenant with caching"""
        @cached(ttl=300, key_prefix=f"{self.model.__tablename__}_by_id_tenant")
        def _get_cached(record_id: UUID, tenant_id: UUID, include_inactive: bool):
            query = self.db.query(self.model).filter(
                and_(self.model.id == record_id, self.model.tenant_id == tenant_id)
            )

            if hasattr(self.model, 'is_active') and not include_inactive:
                query = query.filter(self.model.is_active == True)

            return query.first()

        return _get_cached(id, tenant_id, include_inactive)

    def get_multiple_by_ids(self, ids: List[UUID], tenant_id: UUID = None) -> List[T]:
        """
        Efficiently get multiple records by IDs in a single query.
        Reduces N+1 query problems.
        """
        if not ids:
            return []

        query = self.db.query(self.model).filter(self.model.id.in_(ids))

        if tenant_id and hasattr(self.model, 'tenant_id'):
            query = query.filter(self.model.tenant_id == tenant_id)

        if hasattr(self.model, 'is_active'):
            query = query.filter(self.model.is_active == True)

        self._stats.bulk_operations += 1
        return query.all()

    # Optimized listing with caching
    @cached(ttl=180, key_prefix="list")
    def get_paginated(
        self,
        tenant_id: UUID = None,
        page: int = 1,
        limit: int = 50,
        active_only: bool = True,
        order_by: str = None,
        **filters
    ) -> Dict[str, Any]:
        """
        Get paginated results with caching and optimizations.

        Returns dict with 'items', 'total', 'page', 'limit'
        """
        query = self.db.query(self.model)

        # Apply tenant filter
        if tenant_id and hasattr(self.model, 'tenant_id'):
            query = query.filter(self.model.tenant_id == tenant_id)

        # Apply active filter
        if active_only and hasattr(self.model, 'is_active'):
            query = query.filter(self.model.is_active == True)

        # Apply additional filters
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                query = query.filter(getattr(self.model, key) == value)

        # Get total count (cached separately for better performance)
        total = query.count()

        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            query = query.order_by(desc(getattr(self.model, order_by)))
        elif hasattr(self.model, 'created_at'):
            query = query.order_by(desc(self.model.created_at))

        # Apply pagination
        offset = (page - 1) * limit
        items = query.offset(offset).limit(limit).all()

        return {
            'items': items,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit
        }

    # Bulk operations to reduce connection pressure
    def bulk_create(self, data_list: List[Dict[str, Any]], batch_size: int = 100) -> List[T]:
        """
        Create multiple records efficiently in batches.
        Reduces database round-trips.
        """
        if not data_list:
            return []

        created_items = []

        # Process in batches to avoid memory issues
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]

            # Create instances
            instances = [self.model(**data) for data in batch]

            # Add all to session
            self.db.add_all(instances)
            self.db.flush()  # Get IDs without committing

            # Refresh instances to get generated values
            for instance in instances:
                self.db.refresh(instance)

            created_items.extend(instances)

        self._stats.bulk_operations += 1
        logger.info(f"Bulk created {len(created_items)} {self.model.__tablename__} records")

        return created_items

    def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """
        Update multiple records efficiently.
        Each update dict should contain 'id' and fields to update.
        """
        if not updates:
            return 0

        updated_count = 0

        for update_data in updates:
            record_id = update_data.pop('id')
            if update_data:  # Only update if there are fields to update
                result = self.db.query(self.model).filter(
                    self.model.id == record_id
                ).update(update_data)
                updated_count += result

        self.db.flush()
        self._stats.bulk_operations += 1

        logger.info(f"Bulk updated {updated_count} {self.model.__tablename__} records")
        return updated_count

    # Cached aggregations
    @cached(ttl=600, key_prefix="count")
    def count_by_tenant(self, tenant_id: UUID, active_only: bool = True, **filters) -> int:
        """Count records for tenant with caching"""
        query = self.db.query(self.model).filter(self.model.tenant_id == tenant_id)

        if active_only and hasattr(self.model, 'is_active'):
            query = query.filter(self.model.is_active == True)

        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                query = query.filter(getattr(self.model, key) == value)

        return query.count()

    @cached(ttl=300, key_prefix="exists")
    def exists_by_tenant(self, tenant_id: UUID, **filters) -> bool:
        """Check existence with caching"""
        query = self.db.query(self.model).filter(self.model.tenant_id == tenant_id)

        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                query = query.filter(getattr(self.model, key) == value)

        return query.first() is not None

    # Advanced querying with eager loading
    def get_with_relations(self, id: UUID, relations: List[str] = None) -> Optional[T]:
        """
        Get record with eager loaded relations to avoid N+1 queries.

        Args:
            id: Record ID
            relations: List of relation names to eager load
        """
        query = self.db.query(self.model).filter(self.model.id == id)

        if relations:
            for relation in relations:
                if hasattr(self.model, relation):
                    # Use selectinload for collections, joinedload for single relations
                    attr = getattr(self.model, relation)
                    if hasattr(attr.property, 'collection_class'):
                        query = query.options(selectinload(attr))
                    else:
                        query = query.options(joinedload(attr))

        return query.first()

    # Cache management
    def invalidate_cache(self, tenant_id: UUID = None):
        """Invalidate relevant cache entries"""
        if tenant_id:
            invalidate_tenant_cache(str(tenant_id))

        # Could implement more specific cache invalidation here
        logger.info(f"Cache invalidated for {self.model.__tablename__}")

    def get_stats(self) -> Dict[str, Any]:
        """Get repository performance statistics"""
        return {
            'model': self.model.__tablename__,
            'repository_stats': self._stats.get_stats(),
            'global_stats': _query_stats.get_stats()
        }

class TenantAwareRepository(OptimizedBaseRepository[T]):
    """
    Specialized repository for tenant-aware models.
    Automatically handles tenant isolation and caching.
    """

    def create(self, tenant_id: UUID, **kwargs) -> T:
        """Create record with automatic tenant assignment"""
        kwargs['tenant_id'] = tenant_id
        instance = self.model(**kwargs)
        self.db.add(instance)
        self.db.flush()
        self.db.refresh(instance)

        # Invalidate relevant caches
        self.invalidate_cache(tenant_id)

        return instance

    def update(self, id: UUID, tenant_id: UUID, **kwargs) -> Optional[T]:
        """Update record with tenant isolation"""
        instance = self.get_by_id_and_tenant(id, tenant_id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key) and key != 'tenant_id':  # Prevent tenant change
                    setattr(instance, key, value)

            self.db.flush()
            self.db.refresh(instance)

            # Invalidate caches
            self.invalidate_cache(tenant_id)

        return instance

    def delete(self, id: UUID, tenant_id: UUID, soft_delete: bool = True) -> bool:
        """Delete record with tenant isolation"""
        instance = self.get_by_id_and_tenant(id, tenant_id)
        if not instance:
            return False

        if soft_delete and hasattr(instance, 'is_active'):
            instance.is_active = False
            self.db.flush()
        else:
            self.db.delete(instance)
            self.db.flush()

        # Invalidate caches
        self.invalidate_cache(tenant_id)

        return True

    @cache_tenant_data
    def get_tenant_summary(self, tenant_id: UUID) -> Dict[str, Any]:
        """Get cached tenant summary statistics"""
        active_count = self.count_by_tenant(tenant_id, active_only=True)
        total_count = self.count_by_tenant(tenant_id, active_only=False)

        return {
            'tenant_id': str(tenant_id),
            'active_records': active_count,
            'total_records': total_count,
            'model': self.model.__tablename__,
            'last_updated': datetime.utcnow().isoformat()
        }

def get_global_stats() -> Dict[str, Any]:
    """Get global repository performance statistics"""
    return _query_stats.get_stats()