"""
AgentGuard SDK Models
Data models for the AgentGuard Python SDK.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator


class AgentTestRequest(BaseModel):
    """Request model for testing agent output."""
    agent_output: str = Field(..., description="The AI agent's output to test")
    context: str = Field(default="", description="Context about the query/conversation")
    expected_behavior: str = Field(default="", description="Expected behavior description")
    custom_rules: List[str] = Field(default_factory=list, description="Custom safety rules")
    
    @validator('agent_output')
    def validate_agent_output(cls, v):
        if not v or not v.strip():
            raise ValueError("Agent output cannot be empty")
        if len(v) > 10000:
            raise ValueError("Agent output too long (max 10,000 characters)")
        return v.strip()


class HallucinationReport(BaseModel):
    """Report containing hallucination detection results."""
    hallucination_risk: float = Field(..., description="Risk score (0-1)")
    confidence: float = Field(..., description="Confidence in the assessment (0-1)")
    explanation: str = Field(..., description="Human-readable explanation")
    statistical_score: float = Field(default=0.0, description="Statistical model score")
    claude_score: float = Field(default=0.0, description="Claude model score")
    uncertainty: float = Field(default=0.0, description="Uncertainty measure")
    requires_human_review: bool = Field(default=False, description="Whether human review is needed")
    processing_time_ms: float = Field(default=0.0, description="Processing time in milliseconds")
    model_consensus: Optional[float] = Field(None, description="Model consensus score")
    detailed_analysis: Optional[str] = Field(None, description="Detailed analysis")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @property
    def risk_level(self) -> str:
        """Get human-readable risk level."""
        if self.hallucination_risk < 0.3:
            return "Low"
        elif self.hallucination_risk < 0.7:
            return "Medium"
        else:
            return "High"
    
    @property
    def is_safe(self) -> bool:
        """Check if the output is considered safe."""
        return self.hallucination_risk < 0.5 and not self.requires_human_review


class SafetyRule(BaseModel):
    """Safety rule configuration."""
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    pattern: Optional[str] = Field(None, description="Regex pattern to match")
    severity: str = Field(default="medium", description="Rule severity (low, medium, high)")
    enabled: bool = Field(default=True, description="Whether the rule is enabled")


class AgentConfig(BaseModel):
    """Configuration for an AI agent."""
    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    model: str = Field(default="claude-3-sonnet", description="AI model to use")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Model temperature")
    max_tokens: int = Field(default=1000, ge=1, le=4000, description="Maximum tokens")
    system_prompt: str = Field(..., description="System prompt for the agent")
    safety_rules: List[str] = Field(default_factory=list, description="Safety rules")
    deployment_settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "auto_scale": True,
            "max_instances": 10,
            "timeout_seconds": 30,
            "memory_limit": "1GB"
        },
        description="Deployment configuration"
    )
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Agent name cannot be empty")
        if len(v) > 100:
            raise ValueError("Agent name too long (max 100 characters)")
        return v.strip()
    
    @validator('system_prompt')
    def validate_system_prompt(cls, v):
        if not v or not v.strip():
            raise ValueError("System prompt cannot be empty")
        if len(v) > 5000:
            raise ValueError("System prompt too long (max 5,000 characters)")
        return v.strip()


class Agent(BaseModel):
    """AI agent model."""
    id: str = Field(..., description="Agent identifier")
    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    status: str = Field(..., description="Agent status (draft, testing, deployed, archived)")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    safety_score: float = Field(..., ge=0.0, le=1.0, description="Safety score (0-1)")
    deployment_url: Optional[str] = Field(None, description="Deployment URL")
    webhook_url: Optional[str] = Field(None, description="Webhook URL")
    config: Optional[AgentConfig] = Field(None, description="Agent configuration")
    
    @property
    def is_deployed(self) -> bool:
        """Check if the agent is deployed."""
        return self.status == "deployed"
    
    @property
    def safety_grade(self) -> str:
        """Get safety grade based on score."""
        if self.safety_score >= 0.9:
            return "A"
        elif self.safety_score >= 0.8:
            return "B"
        elif self.safety_score >= 0.7:
            return "C"
        elif self.safety_score >= 0.6:
            return "D"
        else:
            return "F"


class TestResult(BaseModel):
    """Result from testing an agent."""
    id: str = Field(..., description="Test result identifier")
    timestamp: str = Field(..., description="Test timestamp")
    input: str = Field(..., description="Test input")
    output: str = Field(..., description="Agent output")
    safety_score: float = Field(..., ge=0.0, le=1.0, description="Safety score")
    issues: List[str] = Field(default_factory=list, description="Identified issues")
    passed: bool = Field(..., description="Whether the test passed")
    processing_time_ms: float = Field(default=0.0, description="Processing time")
    
    @property
    def status(self) -> str:
        """Get test status."""
        return "PASSED" if self.passed else "FAILED"


class DeploymentRequest(BaseModel):
    """Request for deploying an agent."""
    agent_id: str = Field(..., description="Agent identifier")
    environment: str = Field(default="production", description="Deployment environment")
    auto_scale: bool = Field(default=True, description="Enable auto-scaling")
    max_instances: int = Field(default=10, ge=1, le=100, description="Maximum instances")


class BatchJob(BaseModel):
    """Batch processing job."""
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Job status")
    created_at: str = Field(..., description="Creation timestamp")
    total_items: int = Field(..., description="Total items to process")
    processed_items: int = Field(default=0, description="Items processed")
    failed_items: int = Field(default=0, description="Items failed")
    results_url: Optional[str] = Field(None, description="Results download URL")
    
    @property
    def progress_percentage(self) -> float:
        """Get progress as percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100
    
    @property
    def is_complete(self) -> bool:
        """Check if job is complete."""
        return self.status in ["completed", "failed"]


class WorkstationInfo(BaseModel):
    """Workstation information."""
    id: str = Field(..., description="Workstation identifier")
    name: str = Field(..., description="Workstation name")
    ip_address: str = Field(..., description="IP address")
    status: str = Field(..., description="Status (online, offline, unknown)")
    last_seen: str = Field(..., description="Last seen timestamp")
    agent_count: int = Field(default=0, description="Number of agents")
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Risk score")
    
    @property
    def is_online(self) -> bool:
        """Check if workstation is online."""
        return self.status == "online"


class SystemMetrics(BaseModel):
    """System performance metrics."""
    timestamp: str = Field(..., description="Metrics timestamp")
    requests_per_minute: int = Field(..., description="Requests per minute")
    average_response_time_ms: float = Field(..., description="Average response time")
    error_rate: float = Field(..., ge=0.0, le=1.0, description="Error rate")
    active_connections: int = Field(..., description="Active connections")
    system: Dict[str, float] = Field(..., description="System resource usage")
    
    @property
    def health_status(self) -> str:
        """Get overall health status."""
        if self.error_rate > 0.1 or self.average_response_time_ms > 1000:
            return "unhealthy"
        elif self.error_rate > 0.05 or self.average_response_time_ms > 500:
            return "degraded"
        else:
            return "healthy"


class WebhookEvent(BaseModel):
    """Webhook event data."""
    event_type: str = Field(..., description="Event type")
    timestamp: str = Field(..., description="Event timestamp")
    agent_id: Optional[str] = Field(None, description="Related agent ID")
    data: Dict[str, Any] = Field(..., description="Event data")
    signature: Optional[str] = Field(None, description="Event signature for verification")


class APIUsage(BaseModel):
    """API usage statistics."""
    user_id: str = Field(..., description="User identifier")
    period_start: str = Field(..., description="Period start timestamp")
    period_end: str = Field(..., description="Period end timestamp")
    total_requests: int = Field(..., description="Total API requests")
    successful_requests: int = Field(..., description="Successful requests")
    failed_requests: int = Field(..., description="Failed requests")
    quota_limit: int = Field(..., description="Quota limit")
    quota_remaining: int = Field(..., description="Remaining quota")
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def quota_used_percentage(self) -> float:
        """Calculate quota usage percentage."""
        if self.quota_limit == 0:
            return 0.0
        used = self.quota_limit - self.quota_remaining
        return (used / self.quota_limit) * 100


class ComplianceReport(BaseModel):
    """Compliance audit report."""
    report_id: str = Field(..., description="Report identifier")
    generated_at: str = Field(..., description="Generation timestamp")
    framework: str = Field(..., description="Compliance framework (SOC2, HIPAA, etc.)")
    status: str = Field(..., description="Compliance status")
    findings: List[Dict[str, Any]] = Field(..., description="Audit findings")
    recommendations: List[str] = Field(..., description="Recommendations")
    next_review_date: str = Field(..., description="Next review date")
    
    @property
    def is_compliant(self) -> bool:
        """Check if compliant."""
        return self.status == "compliant"


# Export all models
__all__ = [
    "AgentTestRequest",
    "HallucinationReport", 
    "SafetyRule",
    "AgentConfig",
    "Agent",
    "TestResult",
    "DeploymentRequest",
    "BatchJob",
    "WorkstationInfo",
    "SystemMetrics",
    "WebhookEvent",
    "APIUsage",
    "ComplianceReport"
]
