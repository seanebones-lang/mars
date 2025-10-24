"""
FastAPI middleware for rate limiting and quota management.
"""

import time
import logging
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..services.rate_limit_service import get_rate_limit_service, RateLimitService
from ..services.auth_service import get_auth_service, AuthService

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits and quotas on API requests."""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs", "/redoc", "/openapi.json", "/health", "/favicon.ico"
        ]
        self.rate_limit_service: Optional[RateLimitService] = None
        self.auth_service: Optional[AuthService] = None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through rate limiting checks."""
        
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Initialize services if needed
        if not self.rate_limit_service:
            self.rate_limit_service = get_rate_limit_service()
            await self.rate_limit_service.connect()
        
        if not self.auth_service:
            self.auth_service = get_auth_service()
        
        # Extract user information from request
        user_id, user_role = await self._extract_user_info(request)
        
        try:
            # Check rate limits
            rate_limit_results = await self.rate_limit_service.check_rate_limit(
                request, user_id, user_role
            )
            
            # Check if any rate limit is violated
            for result in rate_limit_results:
                if not result.allowed:
                    return self._create_rate_limit_response(result)
            
            # Check quotas (only for non-GET requests to avoid quota consumption on reads)
            if request.method != "GET":
                # Determine cost based on endpoint
                cost = self._calculate_request_cost(request.url.path)
                
                quota_results = await self.rate_limit_service.check_quota(
                    request, user_id, user_role, cost
                )
                
                # Check if any quota is exceeded
                for result in quota_results:
                    if not result.allowed:
                        return self._create_quota_response(result)
            
            # Process the request
            start_time = time.time()
            response = await call_next(request)
            processing_time = time.time() - start_time
            
            # Record usage for analytics (async, don't wait)
            if user_id and request.method != "GET":
                cost = self._calculate_request_cost(request.url.path)
                metadata = {
                    "method": request.method,
                    "status_code": response.status_code,
                    "processing_time": processing_time,
                    "user_agent": request.headers.get("user-agent", ""),
                    "ip_address": request.client.host if request.client else ""
                }
                
                # Record usage (fire and forget)
                try:
                    await self.rate_limit_service.record_usage(
                        user_id, request.url.path, cost, metadata
                    )
                except Exception as e:
                    logger.warning(f"Failed to record usage: {e}")
            
            # Add rate limit headers to response
            if rate_limit_results:
                self._add_rate_limit_headers(response, rate_limit_results[0])
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Continue processing if rate limiting fails (fail open)
            return await call_next(request)
    
    async def _extract_user_info(self, request: Request) -> tuple[Optional[str], Optional[str]]:
        """Extract user ID and role from request."""
        try:
            # Try to get user from Authorization header
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                user = self.auth_service.get_current_user(token)
                if user:
                    return user.user_id, user.role.value
            
            return None, None
            
        except Exception as e:
            logger.debug(f"Could not extract user info: {e}")
            return None, None
    
    def _calculate_request_cost(self, endpoint: str) -> float:
        """Calculate the cost of a request based on endpoint."""
        # AI detection endpoints are more expensive
        if any(ai_endpoint in endpoint for ai_endpoint in ["/test-agent", "/analytics"]):
            return 5.0
        
        # Webhook operations
        elif "/webhooks" in endpoint:
            return 2.0
        
        # Batch operations
        elif "/batch" in endpoint:
            return 3.0
        
        # Default cost
        else:
            return 1.0
    
    def _create_rate_limit_response(self, result) -> JSONResponse:
        """Create rate limit exceeded response."""
        headers = {
            "X-RateLimit-Limit": str(result.limit),
            "X-RateLimit-Remaining": str(result.remaining),
            "X-RateLimit-Reset": str(int(result.reset_time.timestamp())),
        }
        
        if result.retry_after:
            headers["Retry-After"] = str(result.retry_after)
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Limit: {result.limit} per window.",
                "limit": result.limit,
                "remaining": result.remaining,
                "reset_time": result.reset_time.isoformat(),
                "retry_after": result.retry_after
            },
            headers=headers
        )
    
    def _create_quota_response(self, result) -> JSONResponse:
        """Create quota exceeded response."""
        return JSONResponse(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            content={
                "error": "Quota exceeded",
                "message": f"Usage quota exceeded. Limit: {result.limit}, Used: {result.used}",
                "limit": result.limit,
                "used": result.used,
                "remaining": result.remaining,
                "reset_time": result.reset_time.isoformat()
            }
        )
    
    def _add_rate_limit_headers(self, response: Response, result):
        """Add rate limit headers to response."""
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(int(result.reset_time.timestamp()))


# Convenience function to add rate limiting to FastAPI app
def add_rate_limiting(app, exclude_paths: list = None):
    """Add rate limiting middleware to FastAPI app."""
    app.add_middleware(RateLimitMiddleware, exclude_paths=exclude_paths)
    logger.info("Rate limiting middleware added to application")
