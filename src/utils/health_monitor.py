"""
System Health Monitor
Comprehensive health checking for all system components.
Part of P0-Critical production readiness requirements.
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status of a system component."""
    name: str
    status: HealthStatus
    message: str
    response_time_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    last_check: Optional[str] = None


class HealthMonitor:
    """Monitors health of all system components."""
    
    def __init__(self):
        """Initialize health monitor."""
        self.checks: List[ComponentHealth] = []
        
    def check_claude_api(self) -> ComponentHealth:
        """Check Claude API configuration and connectivity."""
        start_time = time.time()
        api_key = os.getenv("CLAUDE_API_KEY")
        
        if not api_key:
            return ComponentHealth(
                name="Claude API",
                status=HealthStatus.UNHEALTHY,
                message="CLAUDE_API_KEY not configured",
                response_time_ms=0,
                last_check=datetime.utcnow().isoformat()
            )
        
        if not api_key.startswith("sk-ant-api03-"):
            return ComponentHealth(
                name="Claude API",
                status=HealthStatus.DEGRADED,
                message="CLAUDE_API_KEY format invalid",
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.utcnow().isoformat()
            )
        
        # TODO: Add actual API connectivity check
        return ComponentHealth(
            name="Claude API",
            status=HealthStatus.HEALTHY,
            message="API key configured",
            response_time_ms=(time.time() - start_time) * 1000,
            details={"key_prefix": api_key[:20] + "..."},
            last_check=datetime.utcnow().isoformat()
        )
    
    def check_database(self) -> ComponentHealth:
        """Check database connectivity."""
        start_time = time.time()
        db_url = os.getenv("DATABASE_URL")
        
        if not db_url:
            return ComponentHealth(
                name="Database",
                status=HealthStatus.DEGRADED,
                message="Using SQLite fallback (not recommended for production)",
                response_time_ms=(time.time() - start_time) * 1000,
                details={"type": "sqlite", "production_ready": False},
                last_check=datetime.utcnow().isoformat()
            )
        
        if db_url.startswith("postgresql://") or db_url.startswith("postgres://"):
            # TODO: Add actual database connectivity check
            return ComponentHealth(
                name="Database",
                status=HealthStatus.HEALTHY,
                message="PostgreSQL configured",
                response_time_ms=(time.time() - start_time) * 1000,
                details={"type": "postgresql", "production_ready": True},
                last_check=datetime.utcnow().isoformat()
            )
        
        return ComponentHealth(
            name="Database",
            status=HealthStatus.DEGRADED,
            message="Unknown database type",
            response_time_ms=(time.time() - start_time) * 1000,
            last_check=datetime.utcnow().isoformat()
        )
    
    def check_redis(self) -> ComponentHealth:
        """Check Redis connectivity."""
        start_time = time.time()
        redis_url = os.getenv("REDIS_URL")
        
        if not redis_url:
            return ComponentHealth(
                name="Redis Cache",
                status=HealthStatus.DEGRADED,
                message="Using in-memory cache (not recommended for production)",
                response_time_ms=(time.time() - start_time) * 1000,
                details={"type": "memory", "production_ready": False},
                last_check=datetime.utcnow().isoformat()
            )
        
        # TODO: Add actual Redis connectivity check
        return ComponentHealth(
            name="Redis Cache",
            status=HealthStatus.HEALTHY,
            message="Redis configured",
            response_time_ms=(time.time() - start_time) * 1000,
            details={"type": "redis", "production_ready": True},
            last_check=datetime.utcnow().isoformat()
        )
    
    def check_stripe(self) -> ComponentHealth:
        """Check Stripe configuration."""
        start_time = time.time()
        stripe_key = os.getenv("STRIPE_SECRET_KEY")
        
        if not stripe_key:
            return ComponentHealth(
                name="Stripe Payments",
                status=HealthStatus.DEGRADED,
                message="STRIPE_SECRET_KEY not configured (payments disabled)",
                response_time_ms=(time.time() - start_time) * 1000,
                details={"enabled": False},
                last_check=datetime.utcnow().isoformat()
            )
        
        if not stripe_key.startswith("sk_"):
            return ComponentHealth(
                name="Stripe Payments",
                status=HealthStatus.UNHEALTHY,
                message="STRIPE_SECRET_KEY format invalid",
                response_time_ms=(time.time() - start_time) * 1000,
                details={"enabled": False},
                last_check=datetime.utcnow().isoformat()
            )
        
        is_live = stripe_key.startswith("sk_live_")
        return ComponentHealth(
            name="Stripe Payments",
            status=HealthStatus.HEALTHY,
            message=f"Stripe configured ({'live' if is_live else 'test'} mode)",
            response_time_ms=(time.time() - start_time) * 1000,
            details={"enabled": True, "mode": "live" if is_live else "test"},
            last_check=datetime.utcnow().isoformat()
        )
    
    def check_optional_apis(self) -> List[ComponentHealth]:
        """Check optional API configurations."""
        checks = []
        
        # OpenAI API
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            checks.append(ComponentHealth(
                name="OpenAI API",
                status=HealthStatus.HEALTHY if openai_key.startswith("sk-") else HealthStatus.DEGRADED,
                message="Configured for multi-model consensus",
                details={"enabled": True},
                last_check=datetime.utcnow().isoformat()
            ))
        
        # Google Gemini API
        google_key = os.getenv("GOOGLE_API_KEY")
        if google_key:
            checks.append(ComponentHealth(
                name="Google Gemini API",
                status=HealthStatus.HEALTHY,
                message="Configured for multimodal detection",
                details={"enabled": True},
                last_check=datetime.utcnow().isoformat()
            ))
        
        # Sentry
        sentry_dsn = os.getenv("SENTRY_DSN")
        if sentry_dsn:
            checks.append(ComponentHealth(
                name="Sentry Error Tracking",
                status=HealthStatus.HEALTHY if sentry_dsn.startswith("https://") else HealthStatus.DEGRADED,
                message="Error tracking enabled",
                details={"enabled": True},
                last_check=datetime.utcnow().isoformat()
            ))
        
        return checks
    
    def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all health checks.
        
        Returns:
            Dictionary with overall health status and component details
        """
        start_time = time.time()
        
        # Run all checks
        self.checks = [
            self.check_claude_api(),
            self.check_database(),
            self.check_redis(),
            self.check_stripe(),
        ]
        
        # Add optional API checks
        self.checks.extend(self.check_optional_apis())
        
        # Determine overall status
        has_unhealthy = any(c.status == HealthStatus.UNHEALTHY for c in self.checks)
        has_degraded = any(c.status == HealthStatus.DEGRADED for c in self.checks)
        
        if has_unhealthy:
            overall_status = HealthStatus.UNHEALTHY
        elif has_degraded:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        total_time = (time.time() - start_time) * 1000
        
        return {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": total_time,
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "components": [asdict(check) for check in self.checks],
            "summary": {
                "total_components": len(self.checks),
                "healthy": sum(1 for c in self.checks if c.status == HealthStatus.HEALTHY),
                "degraded": sum(1 for c in self.checks if c.status == HealthStatus.DEGRADED),
                "unhealthy": sum(1 for c in self.checks if c.status == HealthStatus.UNHEALTHY),
            }
        }


def get_health_status() -> Dict[str, Any]:
    """
    Convenience function to get system health status.
    
    Returns:
        Health status dictionary
    """
    monitor = HealthMonitor()
    return monitor.run_all_checks()

