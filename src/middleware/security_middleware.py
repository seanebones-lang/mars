"""
Enterprise Security Middleware for AgentGuard Backend
Implements comprehensive security controls for production deployment.
"""

import re
import time
import logging
import secrets
import hashlib
from typing import Callable, Optional, Dict, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import bleach
from pydantic import BaseModel, validator, Field

logger = logging.getLogger(__name__)

class SecurityConfig:
    """Security configuration constants."""
    
    # Input validation
    MAX_INPUT_LENGTH = 50000
    MAX_QUERY_LENGTH = 10000
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
    
    # Rate limiting
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_WINDOW = 60  # seconds
    
    # Security patterns
    SQL_INJECTION_PATTERNS = [
        r'\b(union|select|insert|update|delete|drop|exec|script|alert|eval|expression)\b',
        r'(\||&|;|`|\$\(|\$\{)',
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'\.\.\/',
    ]
    
    # Allowed origins
    ALLOWED_ORIGINS = [
        'https://watcher.mothership-ai.com',
        'https://agentguard-ui.onrender.com',
        'http://localhost:3000',
        'http://localhost:3001',
    ]

class SecurityValidator:
    """Input validation and sanitization utilities."""
    
    @staticmethod
    def validate_input(input_text: str, max_length: int = SecurityConfig.MAX_INPUT_LENGTH) -> str:
        """Validate and sanitize user input."""
        if not input_text or not isinstance(input_text, str):
            raise ValueError("Input must be a non-empty string")
        
        # Length validation
        if len(input_text) > max_length:
            raise ValueError(f"Input exceeds maximum length of {max_length} characters")
        
        # Check for malicious patterns
        for pattern in SecurityConfig.SQL_INJECTION_PATTERNS:
            if re.search(pattern, input_text, re.IGNORECASE):
                logger.warning(f"Malicious pattern detected: {pattern}")
                raise ValueError("Input contains potentially malicious content")
        
        # Sanitize HTML
        sanitized = bleach.clean(input_text, tags=[], attributes={}, strip=True)
        
        # Additional character filtering
        sanitized = re.sub(r'[<>]', '', sanitized)
        
        return sanitized.strip()
    
    @staticmethod
    def validate_file_upload(filename: str, content_type: str, file_size: int) -> None:
        """Validate file upload parameters."""
        allowed_types = ['application/json', 'text/csv', 'text/plain']
        max_size = 10 * 1024 * 1024  # 10MB
        
        if file_size > max_size:
            raise ValueError(f"File size exceeds {max_size / 1024 / 1024}MB limit")
        
        if content_type not in allowed_types:
            raise ValueError(f"File type {content_type} not allowed")
        
        # Check filename for path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            raise ValueError("Invalid filename")

class SecureAgentTestRequest(BaseModel):
    """Secure version of AgentTestRequest with validation."""
    
    agent_output: str = Field(..., max_length=SecurityConfig.MAX_INPUT_LENGTH)
    ground_truth: str = Field(..., max_length=SecurityConfig.MAX_INPUT_LENGTH)
    conversation_history: Optional[list] = Field(None, max_items=50)
    agent_id: Optional[str] = Field(None, max_length=100)
    agent_name: Optional[str] = Field(None, max_length=200)
    
    @validator('agent_output', 'ground_truth')
    def validate_text_fields(cls, v):
        return SecurityValidator.validate_input(v)
    
    @validator('conversation_history')
    def validate_conversation(cls, v):
        if v is None:
            return v
        
        if len(v) > 50:
            raise ValueError("Conversation history too long (max 50 messages)")
        
        return [SecurityValidator.validate_input(str(msg), 1000) for msg in v]
    
    @validator('agent_id', 'agent_name')
    def validate_optional_fields(cls, v):
        if v is None:
            return v
        return SecurityValidator.validate_input(v, 200)

class RateLimiter:
    """In-memory rate limiter (use Redis in production)."""
    
    def __init__(self):
        self.requests: Dict[str, list] = {}
    
    def is_allowed(self, identifier: str, max_requests: int = SecurityConfig.RATE_LIMIT_REQUESTS, 
                   window_seconds: int = SecurityConfig.RATE_LIMIT_WINDOW) -> bool:
        """Check if request is within rate limit."""
        now = time.time()
        
        # Clean old requests
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier] 
                if now - req_time < window_seconds
            ]
        else:
            self.requests[identifier] = []
        
        # Check limit
        if len(self.requests[identifier]) >= max_requests:
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True
    
    def get_remaining(self, identifier: str, max_requests: int = SecurityConfig.RATE_LIMIT_REQUESTS) -> int:
        """Get remaining requests for identifier."""
        if identifier not in self.requests:
            return max_requests
        return max(0, max_requests - len(self.requests[identifier]))

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware."""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs", "/redoc", "/openapi.json", "/health", "/favicon.ico"
        ]
        self.rate_limiter = RateLimiter()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security checks."""
        
        # Skip security checks for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        try:
            # 1. Request size validation
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > SecurityConfig.MAX_REQUEST_SIZE:
                return JSONResponse(
                    status_code=413,
                    content={"error": "Request too large", "max_size": SecurityConfig.MAX_REQUEST_SIZE}
                )
            
            # 2. Rate limiting
            client_ip = self.get_client_ip(request)
            if not self.rate_limiter.is_allowed(client_ip):
                remaining = self.rate_limiter.get_remaining(client_ip)
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "retry_after": SecurityConfig.RATE_LIMIT_WINDOW,
                        "remaining": remaining
                    },
                    headers={
                        "Retry-After": str(SecurityConfig.RATE_LIMIT_WINDOW),
                        "X-RateLimit-Limit": str(SecurityConfig.RATE_LIMIT_REQUESTS),
                        "X-RateLimit-Remaining": str(remaining),
                    }
                )
            
            # 3. Origin validation for CORS
            origin = request.headers.get("origin")
            if origin and origin not in SecurityConfig.ALLOWED_ORIGINS:
                logger.warning(f"Blocked request from unauthorized origin: {origin}")
                return JSONResponse(
                    status_code=403,
                    content={"error": "Origin not allowed"}
                )
            
            # 4. SQL injection detection in query parameters
            for param_value in request.query_params.values():
                try:
                    SecurityValidator.validate_input(param_value, 1000)
                except ValueError as e:
                    logger.warning(f"Malicious query parameter detected: {param_value}")
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid query parameter", "details": str(e)}
                    )
            
            # 5. Security headers
            response = await call_next(request)
            return self.add_security_headers(response)
            
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal security error"}
            )
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        # Check for forwarded headers (from load balancers/proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to client IP
        return getattr(request.client, "host", "unknown")
    
    def add_security_headers(self, response: Response) -> Response:
        """Add security headers to response."""
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "X-DNS-Prefetch-Control": "off",
            "X-Download-Options": "noopen",
            "X-Permitted-Cross-Domain-Policies": "none",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response

class SecurityLogger:
    """Security event logging."""
    
    @staticmethod
    def log_security_event(event_type: str, request: Request, details: Dict[str, Any] = None):
        """Log security events for monitoring."""
        log_entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "client_ip": SecurityMiddleware(None).get_client_ip(request),
            "user_agent": request.headers.get("user-agent", ""),
            "path": request.url.path,
            "method": request.method,
            "details": details or {}
        }
        
        logger.warning(f"Security Event: {log_entry}")
        
        # In production, send to SIEM/security monitoring system
        # await send_to_security_monitoring(log_entry)

# Dependency for secure request validation
async def validate_secure_request(request: Request) -> Dict[str, Any]:
    """Dependency to validate and parse secure requests."""
    try:
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.json()
            
            # Validate based on endpoint
            if "test-agent" in request.url.path:
                validated_data = SecureAgentTestRequest(**body)
                return validated_data.dict()
            
            return body
        
        return {}
    
    except Exception as e:
        SecurityLogger.log_security_event(
            "INVALID_REQUEST", 
            request, 
            {"error": str(e)}
        )
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request format: {str(e)}"
        )

# Utility functions
def generate_csrf_token() -> str:
    """Generate CSRF token."""
    return secrets.token_urlsafe(32)

def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for logging."""
    return hashlib.sha256(data.encode()).hexdigest()[:16]

# Add middleware to FastAPI app
def add_security_middleware(app, exclude_paths: list = None):
    """Add security middleware to FastAPI application."""
    app.add_middleware(SecurityMiddleware, exclude_paths=exclude_paths)
    logger.info("Security middleware added to application")
