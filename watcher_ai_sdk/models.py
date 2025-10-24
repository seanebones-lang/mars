"""
Watcher-AI SDK Data Models
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum


class RiskLevel(Enum):
    """Risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RuleType(Enum):
    """Custom rule types."""
    PATTERN_MATCH = "pattern_match"
    CONFIDENCE_THRESHOLD = "confidence_threshold"
    DOMAIN_SPECIFIC = "domain_specific"
    FACTUAL_ACCURACY = "factual_accuracy"
    CONSISTENCY_CHECK = "consistency_check"
    BIAS_DETECTION = "bias_detection"


class RuleCategory(Enum):
    """Rule categories."""
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    LEGAL = "legal"
    TECHNICAL = "technical"
    GENERAL = "general"
    SAFETY = "safety"
    COMPLIANCE = "compliance"


class RuleSeverity(Enum):
    """Rule violation severity."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DetectionResult:
    """Result of hallucination detection."""
    text: str
    hallucination_risk: float
    confidence: float
    risk_level: RiskLevel
    is_hallucination: bool
    reasoning: str
    recommendations: List[str] = field(default_factory=list)
    custom_violations: List['RuleViolation'] = field(default_factory=list)
    statistical_score: Optional[float] = None
    ensemble_weights: Optional[Dict[str, float]] = None
    processing_time_ms: Optional[float] = None
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        
        # Determine if hallucination based on risk threshold
        self.is_hallucination = self.hallucination_risk > 0.5
        
        # Set risk level based on score
        if self.hallucination_risk >= 0.8:
            self.risk_level = RiskLevel.CRITICAL
        elif self.hallucination_risk >= 0.6:
            self.risk_level = RiskLevel.HIGH
        elif self.hallucination_risk >= 0.4:
            self.risk_level = RiskLevel.MEDIUM
        else:
            self.risk_level = RiskLevel.LOW


@dataclass
class RuleViolation:
    """Custom rule violation."""
    rule_id: str
    rule_name: str
    severity: RuleSeverity
    confidence: float
    matched_text: str
    explanation: str
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CustomRule:
    """Custom detection rule."""
    rule_id: str
    name: str
    description: str
    rule_type: RuleType
    category: RuleCategory
    severity: RuleSeverity
    pattern: Optional[str] = None
    threshold: Optional[float] = None
    keywords: List[str] = field(default_factory=list)
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchItem:
    """Single item in batch processing."""
    id: str
    text: str
    ground_truth: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchResult:
    """Result of batch processing."""
    job_id: str
    status: str
    total_items: int
    processed_items: int
    results: List[DetectionResult] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[float] = None
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100
    
    @property
    def is_complete(self) -> bool:
        """Check if batch is complete."""
        return self.status in ["completed", "failed"]
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.processed_items == 0:
            return 0.0
        return ((self.processed_items - len(self.errors)) / self.processed_items) * 100


@dataclass
class MonitoringConfig:
    """Real-time monitoring configuration."""
    enabled: bool = True
    risk_threshold: float = 0.5
    alert_webhooks: List[str] = field(default_factory=list)
    custom_rules_enabled: bool = True
    batch_size: int = 10
    processing_interval_seconds: int = 5
    max_queue_size: int = 1000
    retry_attempts: int = 3
    timeout_seconds: int = 30


@dataclass
class WebhookConfig:
    """Webhook configuration."""
    webhook_id: str
    name: str
    url: str
    webhook_type: str
    enabled: bool = True
    events: List[str] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 30
    rate_limit_per_minute: int = 60
    retry_attempts: int = 3


@dataclass
class PerformanceMetrics:
    """Performance monitoring metrics."""
    total_requests: int
    avg_response_time_ms: float
    p95_response_time_ms: float
    error_rate_percent: float
    throughput_per_second: float
    claude_usage: Dict[str, Any] = field(default_factory=dict)
    system_health: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class UsageStats:
    """API usage statistics."""
    period_days: int
    total_requests: int
    total_cost_usd: float
    requests_by_endpoint: Dict[str, int] = field(default_factory=dict)
    daily_usage: List[Dict[str, Any]] = field(default_factory=list)
    rate_limit_status: Dict[str, Any] = field(default_factory=dict)
    quota_status: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthToken:
    """Authentication token information."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes
    user_info: Dict[str, Any] = field(default_factory=dict)
    issued_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.issued_at is None:
            self.issued_at = datetime.utcnow()
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        if not self.issued_at:
            return True
        
        from datetime import timedelta
        expiry_time = self.issued_at + timedelta(seconds=self.expires_in)
        return datetime.utcnow() >= expiry_time
    
    @property
    def authorization_header(self) -> str:
        """Get authorization header value."""
        return f"{self.token_type.title()} {self.access_token}"
