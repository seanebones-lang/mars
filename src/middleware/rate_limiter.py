"""
Rate Limiting Middleware
P0-Critical: Prevent abuse and ensure fair usage
"""

import os
import time
import logging
from typing import Dict, Optional, Callable
from fastapi import Request, HTTPException, status
from collections import defaultdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter with support for multiple strategies.
    
    Strategies:
    - IP-based: Rate limit by IP address
    - Customer-based: Rate limit by customer ID
    - Endpoint-based: Different limits per endpoint
    """
    
    def __init__(self):
        """Initialize rate limiter."""
        # Storage for rate limit tracking
        # Format: {key: [(timestamp, count), ...]}
        self._requests: Dict[str, list] = defaultdict(list)
        
        # Default limits (requests per window)
        self.default_limit = int(os.getenv("RATE_LIMIT_DEFAULT", "1000"))
        self.default_window = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds
        
        # Endpoint-specific limits
        self.endpoint_limits = {
            "/test-agent": (100, 60),  # 100 requests per minute
            "/prompt-injection/detect": (200, 60),
            "/multi-model/detect": (50, 60),  # More expensive
            "/pii-protection/detect": (300, 60),
            "/bias-fairness/audit": (100, 60),
            "/multimodal/detect-image": (20, 60),  # Very expensive
            "/multimodal/detect-video": (10, 60),
            "/redteam/simulate": (10, 60),
            "/health": (1000, 60),  # High limit for health checks
            "/metrics": (100, 60),
        }
        
        # Cleanup interval
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes
        
        logger.info(f"Rate limiter initialized: {self.default_limit} req/{self.default_window}s")
    
    def _get_key(self, request: Request, customer_id: Optional[str] = None) -> str:
        """
        Get rate limit key for request.
        
        Args:
            request: FastAPI request
            customer_id: Optional customer ID for customer-based limiting
            
        Returns:
            Rate limit key
        """
        if customer_id:
            return f"customer:{customer_id}:{request.url.path}"
        
        # Use IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}:{request.url.path}"
    
    def _cleanup_old_requests(self):
        """Remove old request records to prevent memory bloat."""
        current_time = time.time()
        
        # Only cleanup every N seconds
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
        
        self._last_cleanup = current_time
        
        # Remove requests older than max window
        max_window = max(
            self.default_window,
            max(window for _, window in self.endpoint_limits.values())
        )
        
        cutoff_time = current_time - max_window
        
        for key in list(self._requests.keys()):
            # Filter out old requests
            self._requests[key] = [
                (timestamp, count)
                for timestamp, count in self._requests[key]
                if timestamp > cutoff_time
            ]
            
            # Remove empty keys
            if not self._requests[key]:
                del self._requests[key]
    
    def _get_limit_for_endpoint(self, path: str) -> tuple:
        """
        Get rate limit for specific endpoint.
        
        Args:
            path: Request path
            
        Returns:
            Tuple of (limit, window)
        """
        # Check for exact match
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]
        
        # Check for prefix match
        for endpoint_path, (limit, window) in self.endpoint_limits.items():
            if path.startswith(endpoint_path):
                return (limit, window)
        
        # Default limit
        return (self.default_limit, self.default_window)
    
    async def check_rate_limit(
        self,
        request: Request,
        customer_id: Optional[str] = None
    ) -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            request: FastAPI request
            customer_id: Optional customer ID
            
        Returns:
            True if within limit, raises HTTPException if exceeded
        """
        # Cleanup old requests periodically
        self._cleanup_old_requests()
        
        # Get rate limit key
        key = self._get_key(request, customer_id)
        
        # Get limit for this endpoint
        limit, window = self._get_limit_for_endpoint(request.url.path)
        
        # Get current time
        current_time = time.time()
        cutoff_time = current_time - window
        
        # Filter requests within window
        recent_requests = [
            (timestamp, count)
            for timestamp, count in self._requests[key]
            if timestamp > cutoff_time
        ]
        
        # Count total requests in window
        total_requests = sum(count for _, count in recent_requests)
        
        # Check if limit exceeded
        if total_requests >= limit:
            # Calculate retry-after
            oldest_request = min(timestamp for timestamp, _ in recent_requests)
            retry_after = int(window - (current_time - oldest_request)) + 1
            
            logger.warning(
                f"Rate limit exceeded for {key}: "
                f"{total_requests}/{limit} in {window}s window"
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )
        
        # Add current request
        recent_requests.append((current_time, 1))
        self._requests[key] = recent_requests
        
        # Add rate limit headers to response (will be set by middleware)
        request.state.rate_limit_limit = limit
        request.state.rate_limit_remaining = limit - total_requests - 1
        request.state.rate_limit_reset = int(current_time + window)
        
        return True
    
    def get_usage_stats(self, customer_id: Optional[str] = None) -> Dict:
        """
        Get rate limit usage statistics.
        
        Args:
            customer_id: Optional customer ID
            
        Returns:
            Dictionary of usage statistics
        """
        if customer_id:
            prefix = f"customer:{customer_id}:"
        else:
            prefix = ""
        
        stats = {}
        current_time = time.time()
        
        for key, requests in self._requests.items():
            if prefix and not key.startswith(prefix):
                continue
            
            # Extract endpoint from key
            endpoint = key.split(":")[-1]
            
            # Get limit for endpoint
            limit, window = self._get_limit_for_endpoint(endpoint)
            
            # Count recent requests
            cutoff_time = current_time - window
            recent_count = sum(
                count for timestamp, count in requests
                if timestamp > cutoff_time
            )
            
            stats[endpoint] = {
                "limit": limit,
                "window": window,
                "used": recent_count,
                "remaining": max(0, limit - recent_count),
                "percentage": (recent_count / limit) * 100 if limit > 0 else 0
            }
        
        return stats


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


async def rate_limit_middleware(request: Request, call_next: Callable):
    """
    Rate limiting middleware for FastAPI.
    
    Usage:
        app.middleware("http")(rate_limit_middleware)
    """
    # Skip rate limiting for health checks in development
    if request.url.path == "/health" and os.getenv("ENVIRONMENT") == "development":
        return await call_next(request)
    
    # Get rate limiter
    limiter = get_rate_limiter()
    
    # Extract customer ID from headers (if available)
    customer_id = request.headers.get("X-Customer-ID")
    
    # Check rate limit
    try:
        await limiter.check_rate_limit(request, customer_id)
    except HTTPException as e:
        # Rate limit exceeded
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail},
            headers=e.headers
        )
    
    # Process request
    response = await call_next(request)
    
    # Add rate limit headers to response
    if hasattr(request.state, "rate_limit_limit"):
        response.headers["X-RateLimit-Limit"] = str(request.state.rate_limit_limit)
        response.headers["X-RateLimit-Remaining"] = str(request.state.rate_limit_remaining)
        response.headers["X-RateLimit-Reset"] = str(request.state.rate_limit_reset)
    
    return response

