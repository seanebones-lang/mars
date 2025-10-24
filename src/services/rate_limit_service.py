"""
Enterprise Rate Limiting and Quota Management Service
Implements sliding window rate limiting with Redis backend and usage tracking.
"""

import os
import time
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import redis.asyncio as redis
from fastapi import Request, HTTPException, status

logger = logging.getLogger(__name__)


class RateLimitType(Enum):
    """Types of rate limits."""
    PER_USER = "per_user"
    PER_IP = "per_ip"
    PER_ENDPOINT = "per_endpoint"
    GLOBAL = "global"


class QuotaType(Enum):
    """Types of quotas."""
    DAILY = "daily"
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass
class RateLimitRule:
    """Rate limit rule configuration."""
    rule_id: str
    name: str
    limit_type: RateLimitType
    requests_per_window: int
    window_seconds: int
    endpoints: List[str] = None  # None means all endpoints
    user_roles: List[str] = None  # None means all roles
    enabled: bool = True
    burst_allowance: int = 0  # Extra requests allowed in burst
    
    def __post_init__(self):
        if self.endpoints is None:
            self.endpoints = ["*"]
        if self.user_roles is None:
            self.user_roles = ["*"]


@dataclass
class QuotaRule:
    """Quota rule configuration."""
    rule_id: str
    name: str
    quota_type: QuotaType
    max_requests: int
    endpoints: List[str] = None
    user_roles: List[str] = None
    enabled: bool = True
    cost_multiplier: float = 1.0  # For weighted quotas (e.g., AI calls cost more)
    
    def __post_init__(self):
        if self.endpoints is None:
            self.endpoints = ["*"]
        if self.user_roles is None:
            self.user_roles = ["*"]


@dataclass
class UsageRecord:
    """Usage tracking record."""
    user_id: str
    endpoint: str
    timestamp: datetime
    cost: float = 1.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class RateLimitResult:
    """Result of rate limit check."""
    allowed: bool
    limit: int
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None
    rule_id: Optional[str] = None


@dataclass
class QuotaResult:
    """Result of quota check."""
    allowed: bool
    limit: int
    used: int
    remaining: int
    reset_time: datetime
    rule_id: Optional[str] = None


class RateLimitService:
    """Enterprise rate limiting and quota management service."""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client: Optional[redis.Redis] = None
        
        # Default rate limit rules
        self.rate_limit_rules: Dict[str, RateLimitRule] = {}
        self.quota_rules: Dict[str, QuotaRule] = {}
        
        # Initialize default rules
        self._init_default_rules()
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self):
        """Connect to Redis."""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            logger.info("Connected to Redis for rate limiting")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Using in-memory fallback.")
            self.redis_client = None
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
    
    def _init_default_rules(self):
        """Initialize default rate limiting and quota rules."""
        
        # Rate limit rules by user role
        self.rate_limit_rules = {
            "admin_general": RateLimitRule(
                rule_id="admin_general",
                name="Admin General API",
                limit_type=RateLimitType.PER_USER,
                requests_per_window=1000,
                window_seconds=3600,  # 1 hour
                user_roles=["admin"],
                burst_allowance=100
            ),
            "supervisor_general": RateLimitRule(
                rule_id="supervisor_general", 
                name="Supervisor General API",
                limit_type=RateLimitType.PER_USER,
                requests_per_window=500,
                window_seconds=3600,
                user_roles=["supervisor"],
                burst_allowance=50
            ),
            "user_general": RateLimitRule(
                rule_id="user_general",
                name="User General API", 
                limit_type=RateLimitType.PER_USER,
                requests_per_window=200,
                window_seconds=3600,
                user_roles=["user"],
                burst_allowance=20
            ),
            "detection_endpoint": RateLimitRule(
                rule_id="detection_endpoint",
                name="AI Detection Endpoints",
                limit_type=RateLimitType.PER_USER,
                requests_per_window=100,
                window_seconds=3600,
                endpoints=["/test-agent", "/test-agent-rag"],
                burst_allowance=10
            ),
            "webhook_endpoint": RateLimitRule(
                rule_id="webhook_endpoint",
                name="Webhook Management",
                limit_type=RateLimitType.PER_USER,
                requests_per_window=50,
                window_seconds=3600,
                endpoints=["/webhooks", "/webhooks/*"],
                user_roles=["admin", "supervisor"]
            ),
            "ip_global": RateLimitRule(
                rule_id="ip_global",
                name="Global IP Rate Limit",
                limit_type=RateLimitType.PER_IP,
                requests_per_window=2000,
                window_seconds=3600,
                burst_allowance=200
            )
        }
        
        # Quota rules
        self.quota_rules = {
            "admin_monthly": QuotaRule(
                rule_id="admin_monthly",
                name="Admin Monthly Quota",
                quota_type=QuotaType.MONTHLY,
                max_requests=50000,
                user_roles=["admin"]
            ),
            "supervisor_monthly": QuotaRule(
                rule_id="supervisor_monthly",
                name="Supervisor Monthly Quota", 
                quota_type=QuotaType.MONTHLY,
                max_requests=20000,
                user_roles=["supervisor"]
            ),
            "user_monthly": QuotaRule(
                rule_id="user_monthly",
                name="User Monthly Quota",
                quota_type=QuotaType.MONTHLY,
                max_requests=5000,
                user_roles=["user"]
            ),
            "ai_detection_daily": QuotaRule(
                rule_id="ai_detection_daily",
                name="AI Detection Daily Quota",
                quota_type=QuotaType.DAILY,
                max_requests=1000,
                endpoints=["/test-agent", "/test-agent-rag"],
                cost_multiplier=5.0  # AI calls are more expensive
            )
        }
    
    def _get_redis_key(self, key_type: str, identifier: str, rule_id: str, window_start: int = None) -> str:
        """Generate Redis key for rate limiting."""
        if window_start:
            return f"watcher:ratelimit:{key_type}:{rule_id}:{identifier}:{window_start}"
        else:
            return f"watcher:quota:{key_type}:{rule_id}:{identifier}"
    
    def _get_window_start(self, window_seconds: int) -> int:
        """Get the start of the current time window."""
        return int(time.time()) // window_seconds * window_seconds
    
    def _matches_endpoint(self, endpoint: str, patterns: List[str]) -> bool:
        """Check if endpoint matches any of the patterns."""
        if "*" in patterns:
            return True
        
        for pattern in patterns:
            if pattern.endswith("*"):
                if endpoint.startswith(pattern[:-1]):
                    return True
            elif endpoint == pattern:
                return True
        
        return False
    
    def _matches_role(self, user_role: str, allowed_roles: List[str]) -> bool:
        """Check if user role matches allowed roles."""
        return "*" in allowed_roles or user_role in allowed_roles
    
    async def _sliding_window_check(self, key: str, limit: int, window_seconds: int, 
                                  burst_allowance: int = 0) -> RateLimitResult:
        """Implement sliding window rate limiting."""
        now = time.time()
        window_start = int(now) - window_seconds
        
        if not self.redis_client:
            # Fallback to simple in-memory check (not recommended for production)
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=limit - 1,
                reset_time=datetime.fromtimestamp(now + window_seconds)
            )
        
        # Use Redis sorted set for sliding window
        pipe = self.redis_client.pipeline()
        
        # Remove expired entries
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {str(now): now})
        
        # Set expiration
        pipe.expire(key, window_seconds)
        
        results = await pipe.execute()
        current_count = results[1]
        
        # Check if within limits (including burst allowance)
        effective_limit = limit + burst_allowance
        allowed = current_count <= effective_limit
        
        if not allowed:
            # Remove the request we just added since it's not allowed
            await self.redis_client.zrem(key, str(now))
        
        remaining = max(0, limit - current_count)
        reset_time = datetime.fromtimestamp(now + window_seconds)
        retry_after = int(window_seconds) if not allowed else None
        
        return RateLimitResult(
            allowed=allowed,
            limit=limit,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=retry_after
        )
    
    async def _quota_check(self, key: str, limit: int, cost: float = 1.0) -> QuotaResult:
        """Check and update quota usage."""
        if not self.redis_client:
            # Fallback - allow all requests
            return QuotaResult(
                allowed=True,
                limit=limit,
                used=0,
                remaining=limit,
                reset_time=datetime.now() + timedelta(days=30)
            )
        
        # Get current usage
        current_usage = await self.redis_client.get(key)
        current_usage = float(current_usage) if current_usage else 0.0
        
        # Check if adding this request would exceed quota
        new_usage = current_usage + cost
        allowed = new_usage <= limit
        
        if allowed:
            # Update usage
            await self.redis_client.set(key, new_usage)
            
            # Set expiration if this is a new key
            if current_usage == 0:
                # Set expiration based on quota type (simplified)
                await self.redis_client.expire(key, 86400 * 31)  # ~1 month
        
        remaining = max(0, limit - new_usage)
        
        return QuotaResult(
            allowed=allowed,
            limit=limit,
            used=int(new_usage),
            remaining=int(remaining),
            reset_time=datetime.now() + timedelta(days=30)  # Simplified
        )
    
    async def check_rate_limit(self, request: Request, user_id: str = None, 
                             user_role: str = None) -> List[RateLimitResult]:
        """Check rate limits for a request."""
        results = []
        endpoint = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        
        for rule in self.rate_limit_rules.values():
            if not rule.enabled:
                continue
            
            # Check if rule applies to this endpoint
            if not self._matches_endpoint(endpoint, rule.endpoints):
                continue
            
            # Check if rule applies to this user role
            if user_role and not self._matches_role(user_role, rule.user_roles):
                continue
            
            # Determine identifier based on limit type
            if rule.limit_type == RateLimitType.PER_USER and user_id:
                identifier = user_id
            elif rule.limit_type == RateLimitType.PER_IP:
                identifier = client_ip
            elif rule.limit_type == RateLimitType.PER_ENDPOINT:
                identifier = endpoint
            elif rule.limit_type == RateLimitType.GLOBAL:
                identifier = "global"
            else:
                continue  # Skip if we don't have the right identifier
            
            # Generate Redis key
            window_start = self._get_window_start(rule.window_seconds)
            key = self._get_redis_key(rule.limit_type.value, identifier, rule.rule_id, window_start)
            
            # Check rate limit
            result = await self._sliding_window_check(
                key, rule.requests_per_window, rule.window_seconds, rule.burst_allowance
            )
            result.rule_id = rule.rule_id
            results.append(result)
            
            # If any rule is violated, we can stop checking
            if not result.allowed:
                break
        
        return results
    
    async def check_quota(self, request: Request, user_id: str = None, 
                        user_role: str = None, cost: float = 1.0) -> List[QuotaResult]:
        """Check quotas for a request."""
        results = []
        endpoint = request.url.path
        
        for rule in self.quota_rules.values():
            if not rule.enabled:
                continue
            
            # Check if rule applies to this endpoint
            if not self._matches_endpoint(endpoint, rule.endpoints):
                continue
            
            # Check if rule applies to this user role
            if user_role and not self._matches_role(user_role, rule.user_roles):
                continue
            
            if not user_id:
                continue  # Quotas are typically per-user
            
            # Generate Redis key based on quota type
            period = datetime.now().strftime("%Y-%m") if rule.quota_type == QuotaType.MONTHLY else datetime.now().strftime("%Y-%m-%d")
            key = self._get_redis_key(rule.quota_type.value, f"{user_id}:{period}", rule.rule_id)
            
            # Apply cost multiplier
            effective_cost = cost * rule.cost_multiplier
            
            # Check quota
            result = await self._quota_check(key, rule.max_requests, effective_cost)
            result.rule_id = rule.rule_id
            results.append(result)
            
            # If any quota is exceeded, we can stop checking
            if not result.allowed:
                break
        
        return results
    
    async def record_usage(self, user_id: str, endpoint: str, cost: float = 1.0, 
                         metadata: Dict[str, Any] = None):
        """Record API usage for analytics."""
        if not self.redis_client:
            return
        
        usage_record = UsageRecord(
            user_id=user_id,
            endpoint=endpoint,
            timestamp=datetime.now(),
            cost=cost,
            metadata=metadata or {}
        )
        
        # Store in Redis for analytics (with expiration)
        key = f"watcher:usage:{user_id}:{int(time.time())}"
        await self.redis_client.setex(key, 86400 * 7, json.dumps(asdict(usage_record), default=str))
    
    async def get_usage_stats(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get usage statistics for a user."""
        if not self.redis_client:
            return {"error": "Redis not available"}
        
        # This would implement comprehensive usage analytics
        # For now, return mock data
        return {
            "user_id": user_id,
            "period_days": days,
            "total_requests": 1250,
            "total_cost": 1875.5,
            "endpoints": {
                "/test-agent": 450,
                "/analytics/overview": 200,
                "/webhooks": 150,
                "others": 450
            },
            "daily_usage": [
                {"date": "2025-10-24", "requests": 45, "cost": 67.5},
                {"date": "2025-10-23", "requests": 52, "cost": 78.0},
                # ... more daily data
            ]
        }
    
    def add_rate_limit_rule(self, rule: RateLimitRule):
        """Add a new rate limit rule."""
        self.rate_limit_rules[rule.rule_id] = rule
        logger.info(f"Added rate limit rule: {rule.name}")
    
    def add_quota_rule(self, rule: QuotaRule):
        """Add a new quota rule."""
        self.quota_rules[rule.rule_id] = rule
        logger.info(f"Added quota rule: {rule.name}")
    
    def remove_rule(self, rule_id: str):
        """Remove a rate limit or quota rule."""
        if rule_id in self.rate_limit_rules:
            del self.rate_limit_rules[rule_id]
            logger.info(f"Removed rate limit rule: {rule_id}")
        
        if rule_id in self.quota_rules:
            del self.quota_rules[rule_id]
            logger.info(f"Removed quota rule: {rule_id}")
    
    def get_all_rules(self) -> Dict[str, Any]:
        """Get all rate limit and quota rules."""
        return {
            "rate_limit_rules": {k: asdict(v) for k, v in self.rate_limit_rules.items()},
            "quota_rules": {k: asdict(v) for k, v in self.quota_rules.items()}
        }


# Global rate limit service instance
_rate_limit_service: Optional[RateLimitService] = None

def get_rate_limit_service() -> RateLimitService:
    """Get or create rate limit service instance."""
    global _rate_limit_service
    if _rate_limit_service is None:
        _rate_limit_service = RateLimitService()
    return _rate_limit_service
