"""
Monitoring API Endpoints
P1-1: Advanced monitoring endpoints for cost tracking, drift detection, and cache stats
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime

from ..utils.cost_tracker import get_cost_tracker
from ..utils.model_drift_detector import get_drift_detector
from ..middleware.caching_middleware import get_cache_middleware

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/cost/daily")
async def get_daily_cost(date: Optional[str] = None):
    """
    Get daily cost summary.
    
    Args:
        date: Date in YYYY-MM-DD format (default: today)
        
    Returns:
        Daily cost summary
    """
    tracker = get_cost_tracker()
    summary = tracker.get_daily_summary(date)
    
    return {
        "status": "success",
        "data": summary
    }


@router.get("/cost/monthly")
async def get_monthly_cost(year: Optional[int] = None, month: Optional[int] = None):
    """
    Get monthly cost summary.
    
    Args:
        year: Year (default: current year)
        month: Month (default: current month)
        
    Returns:
        Monthly cost summary
    """
    tracker = get_cost_tracker()
    summary = tracker.get_monthly_summary(year, month)
    
    return {
        "status": "success",
        "data": summary
    }


@router.get("/cost/customer/{customer_id}")
async def get_customer_cost(customer_id: str, days: int = 30):
    """
    Get cost summary for a specific customer.
    
    Args:
        customer_id: Customer ID
        days: Number of days to look back
        
    Returns:
        Customer cost summary
    """
    tracker = get_cost_tracker()
    summary = tracker.get_customer_usage(customer_id, days)
    
    return {
        "status": "success",
        "data": summary
    }


@router.get("/cost/breakdown")
async def get_cost_breakdown(days: int = 7):
    """
    Get cost breakdown by service.
    
    Args:
        days: Number of days to look back
        
    Returns:
        Service cost breakdown
    """
    tracker = get_cost_tracker()
    breakdown = tracker.get_service_breakdown(days)
    
    return {
        "status": "success",
        "data": breakdown
    }


@router.get("/drift/check")
async def check_model_drift():
    """
    Check for AI model drift.
    
    Returns:
        Drift detection report
    """
    detector = get_drift_detector()
    drift_detected, report = detector.detect_drift()
    
    return {
        "status": "success",
        "drift_detected": drift_detected,
        "report": report
    }


@router.get("/drift/baseline")
async def get_drift_baseline():
    """
    Get baseline metrics for drift detection.
    
    Returns:
        Baseline metrics
    """
    detector = get_drift_detector()
    baseline = detector.calculate_baseline_metrics()
    
    return {
        "status": "success",
        "baseline": baseline
    }


@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics.
    
    Returns:
        Cache hit/miss statistics
    """
    cache = get_cache_middleware()
    stats = cache.get_stats()
    
    return {
        "status": "success",
        "stats": stats
    }


@router.post("/cache/invalidate")
async def invalidate_cache(pattern: str = "*"):
    """
    Invalidate cache entries.
    
    Args:
        pattern: Redis key pattern (default: all)
        
    Returns:
        Success message
    """
    cache = get_cache_middleware()
    cache.invalidate_cache(pattern)
    
    return {
        "status": "success",
        "message": f"Cache invalidated for pattern: {pattern}"
    }


@router.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check with all monitoring metrics.
    
    Returns:
        Comprehensive health status
    """
    from ..utils.health_monitor import get_health_status
    
    # Get base health status
    health = get_health_status()
    
    # Add monitoring metrics
    tracker = get_cost_tracker()
    detector = get_drift_detector()
    cache = get_cache_middleware()
    
    health["monitoring"] = {
        "cost_tracking": {
            "enabled": True,
            "daily_summary": tracker.get_daily_summary()
        },
        "drift_detection": {
            "enabled": True,
            "baseline": detector.baseline_metrics
        },
        "caching": {
            "enabled": cache.redis_client is not None,
            "stats": cache.get_stats()
        }
    }
    
    return health

