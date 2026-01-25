# api-gateway/src/api/auto_learning.py
"""
Auto-Learning OCR Management API

Provides endpoints for monitoring and managing the auto-learning OCR system.
These endpoints help administrators track learning progress, cost savings,
and system performance.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from src.services.init_auto_learning import get_system_status, quick_health_check
from src.services.smart_ocr_service import smart_ocr
from src.jobs.ocr_training_job import training_scheduler

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auto-learning", tags=["auto-learning"])


@router.get("/health")
async def health_check():
    """
    Quick health check of the auto-learning system.

    Returns basic health status for monitoring systems.
    """
    try:
        health = await quick_health_check()
        return health
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_detailed_status():
    """
    Get comprehensive status of the auto-learning system.

    Includes:
    - System requirements check
    - Component health status
    - Learning statistics
    - Cost savings metrics
    - Feature availability
    """
    try:
        status = await get_system_status()
        return status
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_learning_stats():
    """
    Get detailed learning and performance statistics.

    Includes:
    - Cost savings metrics
    - Pattern success rates
    - Training progress
    - Cache performance
    """
    try:
        stats = await smart_ocr.get_service_stats()
        return stats
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/training/stats")
async def get_training_stats():
    """
    Get training job statistics.

    Shows learning queue status, processing progress,
    and training performance metrics.
    """
    try:
        if not training_scheduler.processor.db:
            await training_scheduler.processor.initialize()

        stats = await training_scheduler.processor.get_training_stats()
        return stats
    except Exception as e:
        logger.error(f"Training stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/training/process")
async def trigger_training():
    """
    Manually trigger training queue processing.

    Useful for immediate processing of pending learning data
    instead of waiting for the scheduled background job.
    """
    try:
        result = await training_scheduler.process_now()
        return {
            'triggered': True,
            'processing_result': result,
            'message': f"Processed {result.get('processed_count', 0)} learning records"
        }
    except Exception as e:
        logger.error(f"Manual training trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns/{bank_code}")
async def get_bank_patterns(bank_code: str):
    """
    Get pattern information for a specific bank.

    Args:
        bank_code: Bank identifier (ABA, ACLEDA, Wing, etc.)

    Returns:
        Pattern summary and cache information for the bank
    """
    try:
        from src.services.pattern_cache import pattern_cache

        pattern_summary = pattern_cache.get_pattern_summary(bank_code)

        if not pattern_summary:
            raise HTTPException(
                status_code=404,
                detail=f"No patterns found for bank: {bank_code}"
            )

        return pattern_summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pattern retrieval failed for {bank_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns")
async def get_all_bank_patterns():
    """
    Get pattern information for all banks.

    Returns summary of patterns available for each bank.
    """
    try:
        from src.services.pattern_cache import pattern_cache

        cache_info = pattern_cache.get_cache_info()
        banks_with_patterns = list(pattern_cache.patterns.keys())

        summaries = {}
        for bank_code in banks_with_patterns:
            summary = pattern_cache.get_pattern_summary(bank_code)
            if summary:
                summaries[bank_code] = summary

        return {
            'banks_with_patterns': banks_with_patterns,
            'pattern_summaries': summaries,
            'cache_info': cache_info
        }
    except Exception as e:
        logger.error(f"All patterns retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/merchant/{tenant_id}/stats")
async def get_merchant_learning_stats(tenant_id: str):
    """
    Get learning statistics for a specific merchant/tenant.

    Args:
        tenant_id: Merchant/tenant identifier

    Returns:
        Merchant-specific learning progress and pattern statistics
    """
    try:
        from src.services.pattern_cache import merchant_cache

        merchant_stats = merchant_cache.get_merchant_stats(tenant_id)

        if not merchant_stats:
            return {
                'tenant_id': tenant_id,
                'has_patterns': False,
                'message': 'No merchant-specific patterns found'
            }

        return merchant_stats
    except Exception as e:
        logger.error(f"Merchant stats failed for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache")
async def clear_pattern_cache():
    """
    Clear the pattern cache to force reload from database.

    Use with caution - this will temporarily reduce performance
    until patterns are reloaded.
    """
    try:
        from src.services.pattern_cache import pattern_cache, merchant_cache

        # Get cache size before clearing
        cache_size = len(pattern_cache.patterns)
        merchant_cache_size = len(merchant_cache.merchant_patterns)

        # Clear caches
        pattern_cache.invalidate_all()
        merchant_cache.cleanup_expired_merchants()

        return {
            'cache_cleared': True,
            'bank_patterns_cleared': cache_size,
            'merchant_patterns_cleared': merchant_cache_size,
            'message': 'Pattern caches cleared successfully'
        }
    except Exception as e:
        logger.error(f"Cache clearing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cost-savings")
async def get_cost_savings_report():
    """
    Get detailed cost savings report.

    Shows how much money the auto-learning system is saving
    by reducing GPT-4 Vision API calls.
    """
    try:
        stats = await smart_ocr.get_service_stats()
        cost_savings = stats.get('cost_savings', {})

        total_verifications = cost_savings.get('total_verifications', 0)
        pattern_successes = cost_savings.get('pattern_successes', 0)
        gpt4_calls_avoided = cost_savings.get('gpt4_calls_avoided', 0)
        estimated_savings = cost_savings.get('estimated_savings_usd', 0.0)

        # Calculate additional metrics
        pattern_success_rate = (pattern_successes / total_verifications) if total_verifications > 0 else 0
        estimated_monthly_savings = estimated_savings * 30  # Rough monthly estimate
        estimated_yearly_savings = estimated_savings * 365   # Rough yearly estimate

        return {
            'total_verifications': total_verifications,
            'pattern_based_verifications': pattern_successes,
            'gpt4_vision_calls_avoided': gpt4_calls_avoided,
            'pattern_success_rate': pattern_success_rate,
            'estimated_savings_usd': estimated_savings,
            'estimated_monthly_savings_usd': estimated_monthly_savings,
            'estimated_yearly_savings_usd': estimated_yearly_savings,
            'cost_per_gpt4_call': smart_ocr.gpt4_vision_cost_per_call,
            'report_generated_at': stats.get('timestamp')
        }
    except Exception as e:
        logger.error(f"Cost savings report failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))