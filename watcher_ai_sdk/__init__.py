"""
Watcher-AI Python SDK
Enterprise-grade hallucination detection for AI systems.

Usage:
    from watcher_ai_sdk import WatcherClient
    
    client = WatcherClient(api_key="your-api-key")
    result = client.detect_hallucination("AI agent output text")
    
    if result.is_hallucination:
        print(f"Risk: {result.risk_score:.2f}")
        print(f"Recommendations: {result.recommendations}")
"""

__version__ = "1.0.0"
__author__ = "Mothership AI"
__email__ = "support@mothership-ai.com"

from .client import WatcherClient
from .models import (
    DetectionResult,
    CustomRule,
    RuleViolation,
    BatchResult,
    MonitoringConfig,
    WebhookConfig
)
from .exceptions import (
    WatcherError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    APIError
)
from .async_client import AsyncWatcherClient

__all__ = [
    "WatcherClient",
    "AsyncWatcherClient", 
    "DetectionResult",
    "CustomRule",
    "RuleViolation",
    "BatchResult",
    "MonitoringConfig",
    "WebhookConfig",
    "WatcherError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "APIError"
]
