"""
Enterprise Performance Monitoring Service
Tracks API performance, system health, and Claude usage with real-time alerts.
"""

import os
import time
import psutil
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import statistics
from collections import defaultdict, deque
import redis.asyncio as redis
from fastapi import Request, Response

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of performance metrics."""
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    CLAUDE_USAGE = "claude_usage"
    SYSTEM_HEALTH = "system_health"
    USER_EXPERIENCE = "user_experience"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """Performance metric data point."""
    metric_id: str
    metric_type: MetricType
    endpoint: str
    value: float
    timestamp: datetime
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SystemHealthMetric:
    """System health metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    redis_connected: bool
    redis_memory_mb: float
    active_connections: int
    queue_size: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "disk_percent": self.disk_percent,
            "redis_connected": self.redis_connected,
            "redis_memory_mb": self.redis_memory_mb,
            "active_connections": self.active_connections,
            "queue_size": self.queue_size
        }


@dataclass
class ClaudeUsageMetric:
    """Claude API usage metrics."""
    timestamp: datetime
    endpoint: str
    tokens_used: int
    cost_usd: float
    response_time_ms: float
    success: bool
    error_type: Optional[str] = None
    user_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "endpoint": self.endpoint,
            "tokens_used": self.tokens_used,
            "cost_usd": self.cost_usd,
            "response_time_ms": self.response_time_ms,
            "success": self.success,
            "error_type": self.error_type,
            "user_id": self.user_id
        }


@dataclass
class PerformanceAlert:
    """Performance alert."""
    alert_id: str
    severity: AlertSeverity
    metric_type: MetricType
    message: str
    value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class SLATarget:
    """Service Level Agreement target."""
    name: str
    metric_type: MetricType
    target_value: float
    comparison: str  # "lt", "gt", "eq"
    time_window_minutes: int = 5
    enabled: bool = True


class PerformanceMonitor:
    """Enterprise performance monitoring service."""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client: Optional[redis.Redis] = None
        
        # In-memory storage for recent metrics (fallback)
        self.recent_metrics: deque = deque(maxlen=1000)
        self.recent_health: deque = deque(maxlen=100)
        self.recent_claude: deque = deque(maxlen=500)
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        
        # Performance tracking
        self.request_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.request_counts: Dict[str, int] = defaultdict(int)
        
        # SLA targets
        self.sla_targets = self._init_sla_targets()
        
        # Monitoring task
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_monitoring = False
    
    def _init_sla_targets(self) -> List[SLATarget]:
        """Initialize default SLA targets."""
        return [
            SLATarget(
                name="API Response Time P95",
                metric_type=MetricType.RESPONSE_TIME,
                target_value=2000,  # 2 seconds
                comparison="lt"
            ),
            SLATarget(
                name="Error Rate",
                metric_type=MetricType.ERROR_RATE,
                target_value=1.0,  # 1%
                comparison="lt"
            ),
            SLATarget(
                name="Claude API Response Time",
                metric_type=MetricType.CLAUDE_USAGE,
                target_value=5000,  # 5 seconds
                comparison="lt"
            ),
            SLATarget(
                name="System CPU Usage",
                metric_type=MetricType.SYSTEM_HEALTH,
                target_value=80.0,  # 80%
                comparison="lt"
            ),
            SLATarget(
                name="System Memory Usage",
                metric_type=MetricType.SYSTEM_HEALTH,
                target_value=85.0,  # 85%
                comparison="lt"
            )
        ]
    
    async def connect(self):
        """Connect to Redis for metrics storage."""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            logger.info("Connected to Redis for performance monitoring")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Using in-memory fallback.")
            self.redis_client = None
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
    
    async def start_monitoring(self):
        """Start background monitoring tasks."""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop background monitoring tasks."""
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Performance monitoring stopped")
    
    async def _monitoring_loop(self):
        """Background monitoring loop."""
        while self.is_monitoring:
            try:
                # Collect system health metrics
                await self._collect_system_health()
                
                # Check SLA violations
                await self._check_sla_violations()
                
                # Cleanup old data
                await self._cleanup_old_data()
                
                # Wait before next collection
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _collect_system_health(self):
        """Collect system health metrics."""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Redis health
            redis_connected = False
            redis_memory_mb = 0.0
            if self.redis_client:
                try:
                    await self.redis_client.ping()
                    redis_connected = True
                    info = await self.redis_client.info('memory')
                    redis_memory_mb = info.get('used_memory', 0) / (1024 * 1024)
                except:
                    redis_connected = False
            
            # Active connections (simplified)
            active_connections = len(psutil.net_connections())
            
            health_metric = SystemHealthMetric(
                timestamp=datetime.utcnow(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk.percent,
                redis_connected=redis_connected,
                redis_memory_mb=redis_memory_mb,
                active_connections=active_connections
            )
            
            # Store metric
            await self._store_health_metric(health_metric)
            
        except Exception as e:
            logger.error(f"Error collecting system health: {e}")
    
    async def _store_health_metric(self, metric: SystemHealthMetric):
        """Store system health metric."""
        # Store in memory
        self.recent_health.append(metric)
        
        # Store in Redis if available
        if self.redis_client:
            try:
                key = f"watcher:health:{int(metric.timestamp.timestamp())}"
                await self.redis_client.setex(key, 86400, json.dumps(metric.to_dict()))
            except Exception as e:
                logger.warning(f"Failed to store health metric in Redis: {e}")
    
    async def record_request_metric(self, request: Request, response: Response, 
                                  processing_time: float, user_id: str = None):
        """Record API request performance metric."""
        endpoint = request.url.path
        status_code = response.status_code
        
        # Record response time
        self.request_times[endpoint].append(processing_time * 1000)  # Convert to ms
        self.request_counts[endpoint] += 1
        
        # Record errors
        if status_code >= 400:
            self.error_counts[endpoint] += 1
        
        # Create metric
        metric = PerformanceMetric(
            metric_id=f"{endpoint}-{int(time.time() * 1000000)}",
            metric_type=MetricType.RESPONSE_TIME,
            endpoint=endpoint,
            value=processing_time * 1000,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            metadata={
                "status_code": status_code,
                "method": request.method,
                "user_agent": request.headers.get("user-agent", ""),
                "ip_address": request.client.host if request.client else ""
            }
        )
        
        # Store metric
        await self._store_performance_metric(metric)
    
    async def record_claude_usage(self, endpoint: str, tokens_used: int, 
                                cost_usd: float, response_time_ms: float,
                                success: bool, error_type: str = None, 
                                user_id: str = None):
        """Record Claude API usage metric."""
        metric = ClaudeUsageMetric(
            timestamp=datetime.utcnow(),
            endpoint=endpoint,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            response_time_ms=response_time_ms,
            success=success,
            error_type=error_type,
            user_id=user_id
        )
        
        # Store in memory
        self.recent_claude.append(metric)
        
        # Store in Redis if available
        if self.redis_client:
            try:
                key = f"watcher:claude:{int(metric.timestamp.timestamp())}"
                await self.redis_client.setex(key, 86400 * 7, json.dumps(metric.to_dict()))
            except Exception as e:
                logger.warning(f"Failed to store Claude metric in Redis: {e}")
    
    async def _store_performance_metric(self, metric: PerformanceMetric):
        """Store performance metric."""
        # Store in memory
        self.recent_metrics.append(metric)
        
        # Store in Redis if available
        if self.redis_client:
            try:
                key = f"watcher:perf:{metric.endpoint}:{int(metric.timestamp.timestamp())}"
                await self.redis_client.setex(key, 86400, json.dumps(asdict(metric), default=str))
            except Exception as e:
                logger.warning(f"Failed to store performance metric in Redis: {e}")
    
    async def _check_sla_violations(self):
        """Check for SLA violations and create alerts."""
        for sla in self.sla_targets:
            if not sla.enabled:
                continue
            
            try:
                violation = await self._check_sla_target(sla)
                if violation:
                    await self._create_alert(violation)
            except Exception as e:
                logger.error(f"Error checking SLA {sla.name}: {e}")
    
    async def _check_sla_target(self, sla: SLATarget) -> Optional[PerformanceAlert]:
        """Check a specific SLA target."""
        if sla.metric_type == MetricType.RESPONSE_TIME:
            # Check P95 response time
            all_times = []
            for times in self.request_times.values():
                all_times.extend(times)
            
            if len(all_times) >= 10:  # Need minimum data points
                p95 = statistics.quantiles(all_times, n=20)[18]  # 95th percentile
                if sla.comparison == "lt" and p95 >= sla.target_value:
                    return PerformanceAlert(
                        alert_id=f"sla-{sla.name.lower().replace(' ', '-')}-{int(time.time())}",
                        severity=AlertSeverity.WARNING,
                        metric_type=sla.metric_type,
                        message=f"P95 response time ({p95:.0f}ms) exceeds target ({sla.target_value:.0f}ms)",
                        value=p95,
                        threshold=sla.target_value,
                        timestamp=datetime.utcnow()
                    )
        
        elif sla.metric_type == MetricType.ERROR_RATE:
            # Check error rate
            total_requests = sum(self.request_counts.values())
            total_errors = sum(self.error_counts.values())
            
            if total_requests > 0:
                error_rate = (total_errors / total_requests) * 100
                if sla.comparison == "lt" and error_rate >= sla.target_value:
                    return PerformanceAlert(
                        alert_id=f"sla-error-rate-{int(time.time())}",
                        severity=AlertSeverity.ERROR,
                        metric_type=sla.metric_type,
                        message=f"Error rate ({error_rate:.1f}%) exceeds target ({sla.target_value:.1f}%)",
                        value=error_rate,
                        threshold=sla.target_value,
                        timestamp=datetime.utcnow()
                    )
        
        elif sla.metric_type == MetricType.SYSTEM_HEALTH:
            # Check latest system health
            if self.recent_health:
                latest = self.recent_health[-1]
                
                if "CPU" in sla.name and latest.cpu_percent >= sla.target_value:
                    return PerformanceAlert(
                        alert_id=f"sla-cpu-{int(time.time())}",
                        severity=AlertSeverity.WARNING,
                        metric_type=sla.metric_type,
                        message=f"CPU usage ({latest.cpu_percent:.1f}%) exceeds target ({sla.target_value:.1f}%)",
                        value=latest.cpu_percent,
                        threshold=sla.target_value,
                        timestamp=datetime.utcnow()
                    )
                
                elif "Memory" in sla.name and latest.memory_percent >= sla.target_value:
                    return PerformanceAlert(
                        alert_id=f"sla-memory-{int(time.time())}",
                        severity=AlertSeverity.WARNING,
                        metric_type=sla.metric_type,
                        message=f"Memory usage ({latest.memory_percent:.1f}%) exceeds target ({sla.target_value:.1f}%)",
                        value=latest.memory_percent,
                        threshold=sla.target_value,
                        timestamp=datetime.utcnow()
                    )
        
        return None
    
    async def _create_alert(self, alert: PerformanceAlert):
        """Create and store performance alert."""
        # Check if similar alert already exists
        existing_key = f"{alert.metric_type.value}-{alert.severity.value}"
        if existing_key in self.active_alerts:
            # Update existing alert
            self.active_alerts[existing_key] = alert
        else:
            # Create new alert
            self.active_alerts[alert.alert_id] = alert
            logger.warning(f"Performance Alert: {alert.message}")
        
        # Store in Redis if available
        if self.redis_client:
            try:
                key = f"watcher:alert:{alert.alert_id}"
                await self.redis_client.setex(key, 86400, json.dumps(asdict(alert), default=str))
            except Exception as e:
                logger.warning(f"Failed to store alert in Redis: {e}")
    
    async def _cleanup_old_data(self):
        """Clean up old performance data."""
        # This would implement data retention policies
        # For now, the deque maxlen handles memory cleanup
        pass
    
    async def get_performance_overview(self) -> Dict[str, Any]:
        """Get comprehensive performance overview."""
        # Calculate response time statistics
        all_times = []
        for times in self.request_times.values():
            all_times.extend(times)
        
        response_stats = {}
        if all_times:
            response_stats = {
                "p50": statistics.median(all_times),
                "p95": statistics.quantiles(all_times, n=20)[18] if len(all_times) >= 20 else max(all_times),
                "p99": statistics.quantiles(all_times, n=100)[98] if len(all_times) >= 100 else max(all_times),
                "avg": statistics.mean(all_times),
                "min": min(all_times),
                "max": max(all_times)
            }
        
        # Calculate error rate
        total_requests = sum(self.request_counts.values())
        total_errors = sum(self.error_counts.values())
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        # Get latest system health
        latest_health = self.recent_health[-1].to_dict() if self.recent_health else {}
        
        # Calculate Claude usage stats
        claude_stats = {}
        if self.recent_claude:
            recent_claude_list = list(self.recent_claude)
            claude_stats = {
                "total_tokens": sum(m.tokens_used for m in recent_claude_list),
                "total_cost": sum(m.cost_usd for m in recent_claude_list),
                "avg_response_time": statistics.mean([m.response_time_ms for m in recent_claude_list]),
                "success_rate": sum(1 for m in recent_claude_list if m.success) / len(recent_claude_list) * 100,
                "requests_count": len(recent_claude_list)
            }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "response_times": response_stats,
            "error_rate": error_rate,
            "total_requests": total_requests,
            "system_health": latest_health,
            "claude_usage": claude_stats,
            "active_alerts": len(self.active_alerts),
            "sla_status": "healthy" if len(self.active_alerts) == 0 else "degraded"
        }
    
    async def get_endpoint_performance(self) -> Dict[str, Any]:
        """Get performance breakdown by endpoint."""
        endpoint_stats = {}
        
        for endpoint, times in self.request_times.items():
            if times:
                endpoint_stats[endpoint] = {
                    "avg_response_time": statistics.mean(times),
                    "p95_response_time": statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times),
                    "request_count": self.request_counts[endpoint],
                    "error_count": self.error_counts[endpoint],
                    "error_rate": (self.error_counts[endpoint] / self.request_counts[endpoint] * 100) if self.request_counts[endpoint] > 0 else 0
                }
        
        return endpoint_stats
    
    async def get_alerts(self, severity: AlertSeverity = None) -> List[Dict[str, Any]]:
        """Get active performance alerts."""
        alerts = []
        for alert in self.active_alerts.values():
            if severity is None or alert.severity == severity:
                alerts.append(asdict(alert))
        
        return sorted(alerts, key=lambda x: x['timestamp'], reverse=True)
    
    def resolve_alert(self, alert_id: str):
        """Resolve a performance alert."""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].resolved = True
            self.active_alerts[alert_id].resolved_at = datetime.utcnow()
            del self.active_alerts[alert_id]
            logger.info(f"Resolved performance alert: {alert_id}")


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None

def get_performance_monitor() -> PerformanceMonitor:
    """Get or create performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor
