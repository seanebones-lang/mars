"""
FastAPI middleware for automatic performance monitoring.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..services.performance_monitor import get_performance_monitor
from ..services.auth_service import get_auth_service

logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically track API performance metrics."""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs", "/redoc", "/openapi.json", "/health", "/favicon.ico"
        ]
        self.performance_monitor = None
        self.auth_service = None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and track performance metrics."""
        
        # Skip monitoring for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Initialize services if needed
        if not self.performance_monitor:
            self.performance_monitor = get_performance_monitor()
            await self.performance_monitor.connect()
            await self.performance_monitor.start_monitoring()
        
        if not self.auth_service:
            self.auth_service = get_auth_service()
        
        # Extract user information
        user_id = await self._extract_user_id(request)
        
        # Record start time
        start_time = time.time()
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Record performance metric
            await self.performance_monitor.record_request_metric(
                request, response, processing_time, user_id
            )
            
            # Add performance headers
            response.headers["X-Response-Time"] = f"{processing_time * 1000:.2f}ms"
            response.headers["X-Timestamp"] = str(int(start_time))
            
            return response
            
        except Exception as e:
            # Record error metric
            processing_time = time.time() - start_time
            
            # Create error response for metrics
            error_response = Response(status_code=500)
            await self.performance_monitor.record_request_metric(
                request, error_response, processing_time, user_id
            )
            
            # Re-raise the exception
            raise e
    
    async def _extract_user_id(self, request: Request) -> str:
        """Extract user ID from request for metrics."""
        try:
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                user = self.auth_service.get_current_user(token)
                if user:
                    return user.user_id
            return None
        except Exception:
            return None


def add_performance_monitoring(app, exclude_paths: list = None):
    """Add performance monitoring middleware to FastAPI app."""
    app.add_middleware(PerformanceMiddleware, exclude_paths=exclude_paths)
    logger.info("Performance monitoring middleware added to application")
