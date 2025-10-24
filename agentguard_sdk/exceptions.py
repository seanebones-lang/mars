"""
AgentGuard SDK Exceptions
Custom exception classes for the AgentGuard Python SDK.
"""


class AgentGuardError(Exception):
    """Base exception for AgentGuard SDK errors."""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class AuthenticationError(AgentGuardError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR")


class ValidationError(AgentGuardError):
    """Raised when request validation fails."""
    
    def __init__(self, message: str, validation_errors: list = None):
        self.validation_errors = validation_errors or []
        super().__init__(message, "VALIDATION_ERROR", {"validation_errors": self.validation_errors})


class RateLimitError(AgentGuardError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(message, "RATE_LIMIT_ERROR", {"retry_after": retry_after})


class DeploymentError(AgentGuardError):
    """Raised when agent deployment fails."""
    
    def __init__(self, message: str, agent_id: str = None):
        self.agent_id = agent_id
        super().__init__(message, "DEPLOYMENT_ERROR", {"agent_id": agent_id})


class SafetyError(AgentGuardError):
    """Raised when safety validation fails."""
    
    def __init__(self, message: str, safety_score: float = None, issues: list = None):
        self.safety_score = safety_score
        self.issues = issues or []
        super().__init__(message, "SAFETY_ERROR", {
            "safety_score": safety_score,
            "issues": self.issues
        })


class QuotaExceededError(AgentGuardError):
    """Raised when API quota is exceeded."""
    
    def __init__(self, message: str = "API quota exceeded", quota_limit: int = None):
        self.quota_limit = quota_limit
        super().__init__(message, "QUOTA_EXCEEDED", {"quota_limit": quota_limit})


class ConfigurationError(AgentGuardError):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str, config_field: str = None):
        self.config_field = config_field
        super().__init__(message, "CONFIG_ERROR", {"config_field": config_field})


class NetworkError(AgentGuardError):
    """Raised when network operations fail."""
    
    def __init__(self, message: str, status_code: int = None):
        self.status_code = status_code
        super().__init__(message, "NETWORK_ERROR", {"status_code": status_code})


class TimeoutError(AgentGuardError):
    """Raised when operations timeout."""
    
    def __init__(self, message: str = "Operation timed out", timeout_seconds: int = None):
        self.timeout_seconds = timeout_seconds
        super().__init__(message, "TIMEOUT_ERROR", {"timeout_seconds": timeout_seconds})


class ComplianceError(AgentGuardError):
    """Raised when compliance requirements are not met."""
    
    def __init__(self, message: str, framework: str = None, violations: list = None):
        self.framework = framework
        self.violations = violations or []
        super().__init__(message, "COMPLIANCE_ERROR", {
            "framework": framework,
            "violations": self.violations
        })


# Export all exceptions
__all__ = [
    "AgentGuardError",
    "AuthenticationError",
    "ValidationError",
    "RateLimitError",
    "DeploymentError",
    "SafetyError",
    "QuotaExceededError",
    "ConfigurationError",
    "NetworkError",
    "TimeoutError",
    "ComplianceError"
]
