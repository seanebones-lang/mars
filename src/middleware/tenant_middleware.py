"""
Multi-Tenant Middleware
Handles tenant identification, routing, and data isolation.
"""

import logging
from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import re
from urllib.parse import urlparse

from ..services.tenant_service import get_tenant_service, TenantConfig

logger = logging.getLogger(__name__)


class TenantContext:
    """Thread-local tenant context."""
    
    def __init__(self):
        self._tenant: Optional[TenantConfig] = None
    
    @property
    def tenant(self) -> Optional[TenantConfig]:
        return self._tenant
    
    @tenant.setter
    def tenant(self, value: Optional[TenantConfig]):
        self._tenant = value
    
    def clear(self):
        self._tenant = None


# Global tenant context
tenant_context = TenantContext()


def get_current_tenant() -> Optional[TenantConfig]:
    """Get current tenant from context."""
    return tenant_context.tenant


def set_current_tenant(tenant: Optional[TenantConfig]):
    """Set current tenant in context."""
    tenant_context.tenant = tenant


async def tenant_identification_middleware(request: Request, call_next: Callable):
    """
    Middleware to identify tenant from request and set context.
    
    Tenant identification methods (in order of priority):
    1. API Key header (X-API-Key)
    2. Subdomain (tenant.watcher-ai.com)
    3. Custom domain (client.com)
    4. Tenant ID header (X-Tenant-ID)
    5. Default tenant fallback
    """
    
    tenant_service = get_tenant_service()
    tenant = None
    
    try:
        # Clear previous context
        tenant_context.clear()
        
        # Method 1: API Key authentication
        api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "")
        if api_key and api_key.startswith("watcher_"):
            tenant = tenant_service.validate_api_key(api_key)
            if tenant:
                logger.debug(f"Tenant identified by API key: {tenant.name}")
        
        # Method 2: Subdomain identification
        if not tenant:
            host = request.headers.get("host", "")
            if host:
                # Extract subdomain
                subdomain_match = re.match(r"^([^.]+)\.watcher-ai\.com", host)
                if subdomain_match:
                    subdomain = subdomain_match.group(1)
                    tenant = tenant_service.get_tenant_by_subdomain(subdomain)
                    if tenant:
                        logger.debug(f"Tenant identified by subdomain: {tenant.name}")
        
        # Method 3: Custom domain identification
        if not tenant:
            host = request.headers.get("host", "")
            if host and not host.endswith("watcher-ai.com") and not host.startswith("localhost"):
                tenant = tenant_service.get_tenant_by_domain(host)
                if tenant:
                    logger.debug(f"Tenant identified by custom domain: {tenant.name}")
        
        # Method 4: Tenant ID header
        if not tenant:
            tenant_id = request.headers.get("X-Tenant-ID")
            if tenant_id:
                tenant = tenant_service.get_tenant(tenant_id)
                if tenant:
                    logger.debug(f"Tenant identified by header: {tenant.name}")
        
        # Method 5: Default tenant fallback
        if not tenant:
            tenant = tenant_service.get_tenant("default")
            if tenant:
                logger.debug("Using default tenant")
        
        # Set tenant context
        if tenant:
            set_current_tenant(tenant)
            
            # Add tenant info to request state
            request.state.tenant = tenant
            request.state.tenant_id = tenant.tenant_id
            
            # Check tenant status
            if tenant.status.value != "active":
                if tenant.status.value == "suspended":
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={
                            "error": "Tenant account suspended",
                            "tenant_id": tenant.tenant_id,
                            "status": tenant.status.value
                        }
                    )
                elif tenant.status.value == "trial" and _is_trial_expired(tenant):
                    return JSONResponse(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        content={
                            "error": "Trial period expired",
                            "tenant_id": tenant.tenant_id,
                            "message": "Please upgrade to continue using the service"
                        }
                    )
        else:
            # No tenant identified - return error for API endpoints
            if request.url.path.startswith("/api/") or request.url.path.startswith("/compliance/"):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": "Tenant not identified",
                        "message": "Please provide valid API key or access via tenant subdomain"
                    }
                )
        
        # Process request
        response = await call_next(request)
        
        # Add tenant headers to response
        if tenant:
            response.headers["X-Tenant-ID"] = tenant.tenant_id
            response.headers["X-Tenant-Name"] = tenant.name
        
        return response
        
    except Exception as e:
        logger.error(f"Error in tenant middleware: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Tenant identification failed"}
        )
    
    finally:
        # Clear context after request
        tenant_context.clear()


def _is_trial_expired(tenant: TenantConfig) -> bool:
    """Check if trial period is expired."""
    if tenant.status.value != "trial":
        return False
    
    from datetime import datetime, timedelta
    trial_days = tenant.metadata.get("trial_days", 14)
    expiry_date = tenant.created_at + timedelta(days=trial_days)
    
    return datetime.utcnow() > expiry_date


def require_tenant_feature(feature_name: str):
    """Decorator to require specific tenant feature."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            tenant = get_current_tenant()
            
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tenant not identified"
                )
            
            if not tenant.features.get(feature_name, False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Feature '{feature_name}' not available for your subscription tier"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def check_tenant_quota(quota_type: str, current_usage: int = None):
    """Check if tenant has exceeded quota."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            tenant = get_current_tenant()
            
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tenant not identified"
                )
            
            # Check quota limits
            quota_limits = {
                "api_calls": tenant.max_api_calls_per_month,
                "users": tenant.max_users,
                "storage": tenant.max_storage_gb,
                "custom_rules": tenant.max_custom_rules,
                "webhooks": tenant.max_webhooks
            }
            
            limit = quota_limits.get(quota_type)
            if limit and current_usage and current_usage >= limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Quota exceeded for {quota_type}. Limit: {limit}, Current: {current_usage}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def get_tenant_database_url(tenant_id: str = None) -> str:
    """Get database URL for current or specified tenant."""
    if not tenant_id:
        tenant = get_current_tenant()
        if not tenant:
            raise ValueError("No tenant context available")
        tenant_id = tenant.tenant_id
    
    # For SQLite implementation
    return f"sqlite:///data/tenant_{tenant_id}.db"


def add_tenant_middleware(app):
    """Add tenant middleware to FastAPI app."""
    app.middleware("http")(tenant_identification_middleware)
    logger.info("Tenant middleware added to application")
