"""
AgentGuard Python SDK
Official Python client for the AgentGuard AI Safety Platform.

Author: AgentGuard Engineering Team
Date: October 2025
Version: 2.0.0
"""

from .client import AgentGuardClient
from .models import (
    DetectionResult,
    MultimodalResult,
    BiasAuditResult,
    RedTeamReport,
    ComplianceReport
)
from .exceptions import (
    AgentGuardError,
    AuthenticationError,
    RateLimitError,
    ValidationError
)

__version__ = "2.0.0"
__all__ = [
    "AgentGuardClient",
    "DetectionResult",
    "MultimodalResult",
    "BiasAuditResult",
    "RedTeamReport",
    "ComplianceReport",
    "AgentGuardError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError"
]
