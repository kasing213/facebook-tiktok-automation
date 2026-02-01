# app/routes/db_health.py
"""
Database health and performance monitoring endpoints.

Provides insights into database performance, query optimization,
and connection management for production monitoring.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.core.auth import get_current_owner
from app.core.models import User
from app.core.db import get_db
from app.core.db_monitor import db_monitor, run_health_check
from app.core.cache import cache_stats, cleanup_all_caches, clear_all_caches
from app.repositories.optimized_base import get_global_stats

router = APIRouter(prefix="/db", tags=["Database Health"])

@router.get("/health", response_model=Dict[str, Any])
async def database_health_check():
    """
    Comprehensive database health check.

    Returns:
        - Connection status
        - Performance metrics
        - Optimization recommendations
    """
    try:
        health_data = run_health_check()
        return health_data
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database health check failed: {str(e)}")

@router.get("/performance", response_model=Dict[str, Any])
async def get_performance_metrics(
    current_user: User = Depends(get_current_owner)
):
    """
    Get detailed database performance metrics.
    Only accessible to tenant owners.
    """
    try:
        # Get monitoring stats
        performance_stats = db_monitor.get_performance_stats()

        # Get cache stats
        cache_statistics = cache_stats()

        # Get repository stats
        repository_stats = get_global_stats()

        # Get slow queries
        slow_queries = db_monitor.get_slow_queries(limit=5)

        # Get optimization recommendations
        recommendations = db_monitor.get_optimization_recommendations()

        return {
            "performance": performance_stats,
            "cache": cache_statistics,
            "repositories": repository_stats,
            "slow_queries": slow_queries,
            "recommendations": recommendations,
            "tenant_id": str(current_user.tenant_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")

@router.get("/slow-queries", response_model=List[Dict[str, Any]])
async def get_slow_queries(
    limit: int = 20,
    current_user: User = Depends(get_current_owner)
):
    """
    Get recent slow queries for analysis.
    Helps identify optimization opportunities.
    """
    try:
        slow_queries = db_monitor.get_slow_queries(limit=limit)
        return slow_queries
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get slow queries: {str(e)}")

@router.post("/cache/cleanup", response_model=Dict[str, Any])
async def cleanup_caches(
    current_user: User = Depends(get_current_owner)
):
    """
    Cleanup expired cache entries.
    Returns count of cleaned up entries.
    """
    try:
        cleanup_results = cleanup_all_caches()
        total_cleaned = sum(cleanup_results.values())

        return {
            "message": "Cache cleanup completed",
            "cleaned_entries": cleanup_results,
            "total_cleaned": total_cleaned
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache cleanup failed: {str(e)}")

@router.post("/cache/clear", response_model=Dict[str, str])
async def clear_all_cache(
    current_user: User = Depends(get_current_owner)
):
    """
    Clear all cache entries.
    Use with caution - may temporarily impact performance.
    """
    try:
        clear_all_caches()
        return {"message": "All caches cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache clear failed: {str(e)}")

@router.get("/cache/stats", response_model=Dict[str, Any])
async def get_cache_statistics(
    current_user: User = Depends(get_current_owner)
):
    """
    Get detailed cache performance statistics.
    """
    try:
        return cache_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

@router.get("/optimization-tips", response_model=List[Dict[str, str]])
async def get_optimization_tips(
    current_user: User = Depends(get_current_owner)
):
    """
    Get personalized database optimization recommendations.
    """
    try:
        recommendations = db_monitor.get_optimization_recommendations()

        # Add general tips based on performance
        stats = db_monitor.get_performance_stats()
        performance_score = stats['performance_score']

        general_tips = []

        if performance_score < 70:
            general_tips.append({
                'type': 'general',
                'priority': 'high',
                'issue': 'Low performance score',
                'recommendation': 'Consider implementing caching, reviewing slow queries, and optimizing database indexes'
            })

        if stats['connection_stats']['active_connections'] > 10:
            general_tips.append({
                'type': 'connections',
                'priority': 'medium',
                'issue': 'High connection usage',
                'recommendation': 'Consider using bulk operations and closing database sessions promptly'
            })

        return recommendations + general_tips
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get optimization tips: {str(e)}")

@router.post("/monitoring/reset", response_model=Dict[str, str])
async def reset_monitoring_stats(
    current_user: User = Depends(get_current_owner)
):
    """
    Reset database monitoring statistics.
    Useful for starting fresh performance measurements.
    """
    try:
        db_monitor.reset_stats()
        return {"message": "Monitoring statistics reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset monitoring stats: {str(e)}")

@router.get("/connection-info", response_model=Dict[str, Any])
async def get_connection_info(
    current_user: User = Depends(get_current_owner),
    db: Session = Depends(get_db)
):
    """
    Get current database connection information.
    """
    try:
        from sqlalchemy import text

        # Get connection details
        result = db.execute(text("""
            SELECT
                current_database() as database,
                current_user as user,
                inet_server_addr() as server_ip,
                inet_server_port() as server_port,
                version() as version,
                current_setting('server_version_num') as version_num
        """)).fetchone()

        # Get pool status
        from app.core.db import get_pool_status
        pool_status = get_pool_status()

        # Get active connections count
        active_connections = db.execute(text("""
            SELECT count(*) as active_connections
            FROM pg_stat_activity
            WHERE state = 'active'
        """)).fetchone()

        return {
            "database": result.database,
            "user": result.user,
            "server": f"{result.server_ip}:{result.server_port}",
            "version": result.version.split()[0:2],
            "version_number": result.version_num,
            "pool_status": pool_status,
            "active_server_connections": active_connections.active_connections
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get connection info: {str(e)}")

# Include monitoring endpoints in development only
from app.core.config import get_settings
settings = get_settings()

if settings.ENV == "dev":
    @router.post("/monitoring/enable")
    async def enable_monitoring(current_user: User = Depends(get_current_owner)):
        """Enable database monitoring (dev only)"""
        db_monitor.enable_monitoring()
        return {"message": "Database monitoring enabled"}

    @router.post("/monitoring/disable")
    async def disable_monitoring(current_user: User = Depends(get_current_owner)):
        """Disable database monitoring (dev only)"""
        db_monitor.disable_monitoring()
        return {"message": "Database monitoring disabled"}