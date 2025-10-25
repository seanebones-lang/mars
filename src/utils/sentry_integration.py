"""
Sentry Error Tracking Integration
P0-Critical: Production error monitoring and alerting
"""

import os
import logging
from typing import Optional, Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)

# Try to import Sentry, but don't fail if not available
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    logger.warning("Sentry SDK not installed - error tracking disabled")


class SentryMonitor:
    """Manages Sentry error tracking and monitoring."""
    
    def __init__(self):
        """Initialize Sentry monitoring."""
        self.enabled = False
        self.dsn = os.getenv("SENTRY_DSN")
        self.environment = os.getenv("ENVIRONMENT", "development")
        
        if SENTRY_AVAILABLE and self.dsn:
            self._initialize_sentry()
        else:
            logger.warning("Sentry not configured - set SENTRY_DSN environment variable")
    
    def _initialize_sentry(self):
        """Initialize Sentry SDK with integrations."""
        try:
            # Configure logging integration
            logging_integration = LoggingIntegration(
                level=logging.INFO,  # Capture info and above as breadcrumbs
                event_level=logging.ERROR  # Send errors as events
            )
            
            sentry_sdk.init(
                dsn=self.dsn,
                environment=self.environment,
                
                # Integrations
                integrations=[
                    FastApiIntegration(),
                    SqlalchemyIntegration(),
                    RedisIntegration(),
                    logging_integration,
                ],
                
                # Performance monitoring
                traces_sample_rate=1.0 if self.environment == "development" else 0.1,
                
                # Error sampling
                sample_rate=1.0,
                
                # Release tracking
                release=os.getenv("GIT_COMMIT", "unknown"),
                
                # Additional context
                before_send=self._before_send,
                
                # Debug mode
                debug=self.environment == "development",
            )
            
            self.enabled = True
            logger.info(f"Sentry initialized for {self.environment} environment")
            
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")
            self.enabled = False
    
    def _before_send(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process events before sending to Sentry.
        Can be used to filter, modify, or enrich events.
        """
        # Add custom tags
        event.setdefault("tags", {})
        event["tags"]["service"] = "agentguard-api"
        event["tags"]["company"] = "mothership-ai"
        
        # Add user context if available
        if "user" not in event:
            event["user"] = {
                "ip_address": "{{auto}}",
            }
        
        # Filter out certain errors (optional)
        if "exc_info" in hint:
            exc_type, exc_value, tb = hint["exc_info"]
            # Example: Don't send certain types of errors
            if isinstance(exc_value, KeyboardInterrupt):
                return None
        
        return event
    
    def capture_exception(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """
        Capture an exception and send to Sentry.
        
        Args:
            error: The exception to capture
            context: Additional context to include
        """
        if not self.enabled:
            logger.error(f"Exception (Sentry disabled): {error}")
            return
        
        try:
            with sentry_sdk.push_scope() as scope:
                # Add context
                if context:
                    for key, value in context.items():
                        scope.set_context(key, value)
                
                # Capture exception
                sentry_sdk.capture_exception(error)
                
        except Exception as e:
            logger.error(f"Failed to capture exception in Sentry: {e}")
    
    def capture_message(self, message: str, level: str = "info", context: Optional[Dict[str, Any]] = None):
        """
        Capture a message and send to Sentry.
        
        Args:
            message: The message to capture
            level: Severity level (debug, info, warning, error, fatal)
            context: Additional context to include
        """
        if not self.enabled:
            return
        
        try:
            with sentry_sdk.push_scope() as scope:
                # Add context
                if context:
                    for key, value in context.items():
                        scope.set_context(key, value)
                
                # Capture message
                sentry_sdk.capture_message(message, level=level)
                
        except Exception as e:
            logger.error(f"Failed to capture message in Sentry: {e}")
    
    def set_user(self, user_id: str, email: Optional[str] = None, username: Optional[str] = None):
        """
        Set user context for error tracking.
        
        Args:
            user_id: User identifier
            email: User email (optional)
            username: Username (optional)
        """
        if not self.enabled:
            return
        
        try:
            sentry_sdk.set_user({
                "id": user_id,
                "email": email,
                "username": username,
            })
        except Exception as e:
            logger.error(f"Failed to set user context: {e}")
    
    def set_tag(self, key: str, value: str):
        """
        Set a tag for error tracking.
        
        Args:
            key: Tag key
            value: Tag value
        """
        if not self.enabled:
            return
        
        try:
            sentry_sdk.set_tag(key, value)
        except Exception as e:
            logger.error(f"Failed to set tag: {e}")
    
    def add_breadcrumb(self, message: str, category: str = "default", level: str = "info", data: Optional[Dict] = None):
        """
        Add a breadcrumb for error tracking.
        
        Args:
            message: Breadcrumb message
            category: Breadcrumb category
            level: Severity level
            data: Additional data
        """
        if not self.enabled:
            return
        
        try:
            sentry_sdk.add_breadcrumb(
                message=message,
                category=category,
                level=level,
                data=data or {}
            )
        except Exception as e:
            logger.error(f"Failed to add breadcrumb: {e}")
    
    def start_transaction(self, name: str, op: str = "function") -> Any:
        """
        Start a performance transaction.
        
        Args:
            name: Transaction name
            op: Operation type
            
        Returns:
            Transaction context manager
        """
        if not self.enabled:
            # Return a no-op context manager
            class NoOpTransaction:
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    pass
            return NoOpTransaction()
        
        try:
            return sentry_sdk.start_transaction(name=name, op=op)
        except Exception as e:
            logger.error(f"Failed to start transaction: {e}")
            class NoOpTransaction:
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    pass
            return NoOpTransaction()


# Global Sentry monitor instance
_sentry_monitor: Optional[SentryMonitor] = None


def get_sentry_monitor() -> SentryMonitor:
    """Get the global Sentry monitor instance."""
    global _sentry_monitor
    if _sentry_monitor is None:
        _sentry_monitor = SentryMonitor()
    return _sentry_monitor


def monitor_errors(func):
    """
    Decorator to automatically capture exceptions in Sentry.
    
    Usage:
        @monitor_errors
        def my_function():
            # Your code here
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            monitor = get_sentry_monitor()
            monitor.capture_exception(e, context={
                "function": func.__name__,
                "args": str(args)[:100],  # Limit size
                "kwargs": str(kwargs)[:100],
            })
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            monitor = get_sentry_monitor()
            monitor.capture_exception(e, context={
                "function": func.__name__,
                "args": str(args)[:100],
                "kwargs": str(kwargs)[:100],
            })
            raise
    
    # Return appropriate wrapper based on function type
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def track_performance(name: str):
    """
    Decorator to track performance of a function.
    
    Usage:
        @track_performance("my_operation")
        def my_function():
            # Your code here
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            monitor = get_sentry_monitor()
            with monitor.start_transaction(name=name, op="function"):
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            monitor = get_sentry_monitor()
            with monitor.start_transaction(name=name, op="function"):
                return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

