"""
FastAPI authentication dependencies for JWT-based authentication and RBAC.
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
import logging

from ..services.auth_service import get_auth_service, AuthService, User, UserRole, Permission

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """
    Get current authenticated user from JWT token.
    Returns None if no valid token is provided (for optional authentication).
    """
    if not credentials:
        return None
    
    try:
        user = auth_service.get_current_user(credentials.credentials)
        return user
    except Exception as e:
        logger.warning(f"Token validation failed: {e}")
        return None


async def require_authentication(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """
    Require valid authentication. Raises 401 if not authenticated.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = auth_service.get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    return user


def require_role(required_role: UserRole):
    """
    Dependency factory to require specific user role.
    """
    async def role_checker(current_user: User = Depends(require_authentication)) -> User:
        # Admin can access everything
        if current_user.role == UserRole.ADMIN:
            return current_user
        
        # Check if user has required role or higher
        role_hierarchy = {
            UserRole.USER: 1,
            UserRole.SUPERVISOR: 2,
            UserRole.ADMIN: 3
        }
        
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role.value} role or higher"
            )
        
        return current_user
    
    return role_checker


def require_permission(required_permission: Permission):
    """
    Dependency factory to require specific permission.
    """
    async def permission_checker(
        current_user: User = Depends(require_authentication),
        auth_service: AuthService = Depends(get_auth_service)
    ) -> User:
        if not auth_service.verify_permission(current_user.role, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_permission.value} permission"
            )
        
        return current_user
    
    return permission_checker


def require_permissions(required_permissions: List[Permission]):
    """
    Dependency factory to require multiple permissions (all must be satisfied).
    """
    async def permissions_checker(
        current_user: User = Depends(require_authentication),
        auth_service: AuthService = Depends(get_auth_service)
    ) -> User:
        for permission in required_permissions:
            if not auth_service.verify_permission(current_user.role, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires {permission.value} permission"
                )
        
        return current_user
    
    return permissions_checker


def require_any_permission(required_permissions: List[Permission]):
    """
    Dependency factory to require any of the specified permissions.
    """
    async def any_permission_checker(
        current_user: User = Depends(require_authentication),
        auth_service: AuthService = Depends(get_auth_service)
    ) -> User:
        for permission in required_permissions:
            if auth_service.verify_permission(current_user.role, permission):
                return current_user
        
        permission_names = [p.value for p in required_permissions]
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Requires one of: {', '.join(permission_names)}"
        )
    
    return any_permission_checker


async def get_client_info(request: Request) -> dict:
    """
    Extract client information for audit logging.
    """
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "method": request.method,
        "url": str(request.url)
    }


# Convenience dependencies for common role requirements
require_admin = require_role(UserRole.ADMIN)
require_supervisor = require_role(UserRole.SUPERVISOR)
require_user = require_role(UserRole.USER)

# Convenience dependencies for common permissions
require_user_management = require_permission(Permission.CREATE_USER)
require_webhook_management = require_permission(Permission.CREATE_WEBHOOK)
require_analytics_access = require_any_permission([
    Permission.VIEW_ANALYTICS, 
    Permission.VIEW_ALL_ANALYTICS
])
require_agent_management = require_any_permission([
    Permission.VIEW_ALL_AGENTS,
    Permission.VIEW_ASSIGNED_AGENTS
])
