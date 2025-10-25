"""
Redis Caching Middleware
P1-2: Performance optimization through intelligent caching
"""

import os
import json
import hashlib
import logging
from typing import Optional, Any, Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import redis
from datetime import timedelta

logger = logging.getLogger(__name__)


class CacheMiddleware:
    """
    Intelligent caching middleware using Redis.
    
    Features:
    - Response caching for GET requests
    - Cache key generation based on URL and query params
    - TTL configuration per endpoint
    - Cache invalidation
    - Cache statistics
    """
    
    def __init__(self):
        """Initialize cache middleware."""
        self.redis_url = os.getenv("REDIS_URL")
        self.enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
        
        if not self.redis_url or not self.enabled:
            logger.warning("Cache middleware disabled (REDIS_URL not set or CACHE_ENABLED=false)")
            self.redis_client = None
            return
        
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Cache middleware initialized with Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
        
        # Cache TTL configuration (in seconds)
        self.cache_ttl = {
            "/health": 10,  # 10 seconds
            "/metrics": 30,  # 30 seconds
            "/test-agent": 300,  # 5 minutes (if identical request)
            "/prompt-injection/detect": 300,
            "/pii-protection/detect": 300,
            "/bias-fairness/audit": 300,
            "/multi-model/detect": 300,
        }
        
        # Default TTL
        self.default_ttl = 60  # 1 minute
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
        }
    
    def _generate_cache_key(self, request: Request) -> str:
        """
        Generate cache key from request.
        
        Args:
            request: FastAPI request
            
        Returns:
            Cache key string
        """
        # Include method, path, and query params
        key_parts = [
            request.method,
            request.url.path,
            str(sorted(request.query_params.items()))
        ]
        
        # For POST requests, include body hash
        if request.method == "POST" and hasattr(request.state, "body"):
            body_hash = hashlib.md5(request.state.body).hexdigest()
            key_parts.append(body_hash)
        
        # Generate key
        key_string = ":".join(key_parts)
        cache_key = f"cache:{hashlib.sha256(key_string.encode()).hexdigest()}"
        
        return cache_key
    
    def _get_ttl_for_path(self, path: str) -> int:
        """
        Get TTL for a specific path.
        
        Args:
            path: Request path
            
        Returns:
            TTL in seconds
        """
        # Check for exact match
        if path in self.cache_ttl:
            return self.cache_ttl[path]
        
        # Check for prefix match
        for cached_path, ttl in self.cache_ttl.items():
            if path.startswith(cached_path):
                return ttl
        
        return self.default_ttl
    
    def _should_cache(self, request: Request) -> bool:
        """
        Determine if request should be cached.
        
        Args:
            request: FastAPI request
            
        Returns:
            True if should cache
        """
        # Don't cache if Redis not available
        if not self.redis_client:
            return False
        
        # Only cache GET requests and specific POST endpoints
        if request.method == "GET":
            return True
        
        # Cache specific POST endpoints (for identical requests)
        cacheable_posts = [
            "/test-agent",
            "/prompt-injection/detect",
            "/pii-protection/detect",
            "/bias-fairness/audit",
            "/multi-model/detect",
        ]
        
        return any(request.url.path.startswith(path) for path in cacheable_posts)
    
    async def get_cached_response(self, request: Request) -> Optional[Response]:
        """
        Get cached response if available.
        
        Args:
            request: FastAPI request
            
        Returns:
            Cached response or None
        """
        if not self._should_cache(request):
            return None
        
        try:
            cache_key = self._generate_cache_key(request)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                self.stats["hits"] += 1
                logger.debug(f"Cache hit: {request.url.path}")
                
                # Parse cached response
                response_data = json.loads(cached_data)
                
                return JSONResponse(
                    content=response_data["content"],
                    status_code=response_data["status_code"],
                    headers={
                        **response_data.get("headers", {}),
                        "X-Cache": "HIT"
                    }
                )
            else:
                self.stats["misses"] += 1
                logger.debug(f"Cache miss: {request.url.path}")
                return None
                
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Cache get error: {e}")
            return None
    
    async def cache_response(
        self,
        request: Request,
        response: Response
    ):
        """
        Cache response.
        
        Args:
            request: FastAPI request
            response: FastAPI response
        """
        if not self._should_cache(request):
            return
        
        # Only cache successful responses
        if response.status_code != 200:
            return
        
        try:
            cache_key = self._generate_cache_key(request)
            ttl = self._get_ttl_for_path(request.url.path)
            
            # Get response body
            if isinstance(response, JSONResponse):
                content = response.body.decode() if isinstance(response.body, bytes) else response.body
                
                # Store response data
                response_data = {
                    "content": json.loads(content) if isinstance(content, str) else content,
                    "status_code": response.status_code,
                    "headers": dict(response.headers)
                }
                
                self.redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(response_data)
                )
                
                logger.debug(f"Cached response: {request.url.path} (TTL: {ttl}s)")
                
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Cache set error: {e}")
    
    def invalidate_cache(self, pattern: str = "*"):
        """
        Invalidate cache entries matching pattern.
        
        Args:
            pattern: Redis key pattern (default: all cache entries)
        """
        if not self.redis_client:
            return
        
        try:
            keys = self.redis_client.keys(f"cache:{pattern}")
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries")
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
    
    def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary of cache stats
        """
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "enabled": self.redis_client is not None
        }


# Global cache middleware instance
_cache_middleware: Optional[CacheMiddleware] = None


def get_cache_middleware() -> CacheMiddleware:
    """Get the global cache middleware instance."""
    global _cache_middleware
    if _cache_middleware is None:
        _cache_middleware = CacheMiddleware()
    return _cache_middleware


async def caching_middleware(request: Request, call_next: Callable):
    """
    Caching middleware for FastAPI.
    
    Usage:
        app.middleware("http")(caching_middleware)
    """
    cache = get_cache_middleware()
    
    # Try to get cached response
    cached_response = await cache.get_cached_response(request)
    if cached_response:
        return cached_response
    
    # Store request body for POST requests (for cache key generation)
    if request.method == "POST":
        body = await request.body()
        request.state.body = body
    
    # Process request
    response = await call_next(request)
    
    # Cache response
    await cache.cache_response(request, response)
    
    # Add cache header
    if not hasattr(response, "headers"):
        return response
    
    response.headers["X-Cache"] = "MISS"
    
    return response

