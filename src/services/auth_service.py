"""
Enterprise Authentication and Authorization Service
Implements JWT-based authentication with Role-Based Access Control (RBAC).
"""

import os
import jwt
import bcrypt
import secrets
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from contextlib import asynccontextmanager
import sqlite3
import aiosqlite
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """User roles with hierarchical permissions."""
    ADMIN = "admin"
    SUPERVISOR = "supervisor" 
    USER = "user"


class Permission(Enum):
    """System permissions."""
    # User Management
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    VIEW_USERS = "view_users"
    
    # Agent Management
    CREATE_AGENT = "create_agent"
    UPDATE_AGENT = "update_agent"
    DELETE_AGENT = "delete_agent"
    VIEW_ALL_AGENTS = "view_all_agents"
    VIEW_ASSIGNED_AGENTS = "view_assigned_agents"
    
    # Webhook Management
    CREATE_WEBHOOK = "create_webhook"
    UPDATE_WEBHOOK = "update_webhook"
    DELETE_WEBHOOK = "delete_webhook"
    VIEW_WEBHOOKS = "view_webhooks"
    TEST_WEBHOOK = "test_webhook"
    
    # Analytics & Monitoring
    VIEW_ANALYTICS = "view_analytics"
    VIEW_ALL_ANALYTICS = "view_all_analytics"
    VIEW_SYSTEM_HEALTH = "view_system_health"
    
    # Alert Management
    ACKNOWLEDGE_ALERTS = "acknowledge_alerts"
    CREATE_ALERTS = "create_alerts"
    VIEW_ALL_ALERTS = "view_all_alerts"
    VIEW_ASSIGNED_ALERTS = "view_assigned_alerts"
    
    # System Configuration
    UPDATE_SYSTEM_CONFIG = "update_system_config"
    VIEW_SYSTEM_CONFIG = "view_system_config"
    MANAGE_API_KEYS = "manage_api_keys"
    
    # Audit & Compliance
    VIEW_AUDIT_LOGS = "view_audit_logs"
    EXPORT_DATA = "export_data"


@dataclass
class User:
    """User model with authentication and authorization data."""
    user_id: str
    username: str
    email: str
    password_hash: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    assigned_agents: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.assigned_agents is None:
            self.assigned_agents = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class TokenData:
    """JWT token payload data."""
    user_id: str
    username: str
    role: UserRole
    permissions: List[Permission]
    exp: datetime
    iat: datetime
    jti: str  # JWT ID for token revocation


@dataclass
class LoginRequest:
    """Login request data."""
    username: str
    password: str
    mfa_code: Optional[str] = None


@dataclass
class LoginResponse:
    """Login response data."""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: Dict[str, Any]


class AuthService:
    """Enterprise authentication and authorization service."""
    
    # Role-based permissions mapping
    ROLE_PERMISSIONS = {
        UserRole.ADMIN: [
            # Full system access
            Permission.CREATE_USER, Permission.UPDATE_USER, Permission.DELETE_USER, Permission.VIEW_USERS,
            Permission.CREATE_AGENT, Permission.UPDATE_AGENT, Permission.DELETE_AGENT, Permission.VIEW_ALL_AGENTS,
            Permission.CREATE_WEBHOOK, Permission.UPDATE_WEBHOOK, Permission.DELETE_WEBHOOK, Permission.VIEW_WEBHOOKS, Permission.TEST_WEBHOOK,
            Permission.VIEW_ALL_ANALYTICS, Permission.VIEW_SYSTEM_HEALTH,
            Permission.ACKNOWLEDGE_ALERTS, Permission.CREATE_ALERTS, Permission.VIEW_ALL_ALERTS,
            Permission.UPDATE_SYSTEM_CONFIG, Permission.VIEW_SYSTEM_CONFIG, Permission.MANAGE_API_KEYS,
            Permission.VIEW_AUDIT_LOGS, Permission.EXPORT_DATA
        ],
        UserRole.SUPERVISOR: [
            # Multi-agent monitoring and management
            Permission.VIEW_USERS, Permission.VIEW_ALL_AGENTS, Permission.UPDATE_AGENT,
            Permission.VIEW_WEBHOOKS, Permission.TEST_WEBHOOK,
            Permission.VIEW_ALL_ANALYTICS, Permission.VIEW_SYSTEM_HEALTH,
            Permission.ACKNOWLEDGE_ALERTS, Permission.CREATE_ALERTS, Permission.VIEW_ALL_ALERTS,
            Permission.VIEW_SYSTEM_CONFIG, Permission.EXPORT_DATA
        ],
        UserRole.USER: [
            # Limited access to assigned agents
            Permission.VIEW_ASSIGNED_AGENTS, Permission.VIEW_ANALYTICS,
            Permission.ACKNOWLEDGE_ALERTS, Permission.VIEW_ASSIGNED_ALERTS
        ]
    }
    
    def __init__(self, db_path: str = "watcher_auth.db"):
        self.db_path = db_path
        self.jwt_secret = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
        self.jwt_algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        self.max_failed_attempts = int(os.getenv("MAX_FAILED_LOGIN_ATTEMPTS", "5"))
        self.lockout_duration_minutes = int(os.getenv("LOCKOUT_DURATION_MINUTES", "30"))
        
        # Initialize database
        self._init_database()
        
        # Create default admin user if none exists
        self._create_default_admin()
    
    def _init_database(self):
        """Initialize SQLite database for user management."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_verified BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    failed_login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP,
                    mfa_enabled BOOLEAN DEFAULT FALSE,
                    mfa_secret TEXT,
                    assigned_agents TEXT DEFAULT '[]',
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS revoked_tokens (
                    jti TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    revoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    log_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    action TEXT NOT NULL,
                    resource TEXT,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_revoked_tokens_jti ON revoked_tokens(jti)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp)")
            
            conn.commit()
    
    def _create_default_admin(self):
        """Create default admin user if no users exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            if user_count == 0:
                admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123!")
                admin_user = User(
                    user_id=secrets.token_urlsafe(16),
                    username="admin",
                    email="admin@watcher-ai.com",
                    password_hash=self._hash_password(admin_password),
                    role=UserRole.ADMIN,
                    is_active=True,
                    is_verified=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                self._save_user(admin_user)
                logger.info("Created default admin user (username: admin)")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def _save_user(self, user: User):
        """Save user to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO users (
                    user_id, username, email, password_hash, role, is_active, is_verified,
                    created_at, updated_at, last_login, failed_login_attempts, locked_until,
                    mfa_enabled, mfa_secret, assigned_agents, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user.user_id, user.username, user.email, user.password_hash, user.role.value,
                user.is_active, user.is_verified, user.created_at, user.updated_at,
                user.last_login, user.failed_login_attempts, user.locked_until,
                user.mfa_enabled, user.mfa_secret, str(user.assigned_agents), str(user.metadata)
            ))
            conn.commit()
    
    def _get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            
            if row:
                return User(
                    user_id=row['user_id'],
                    username=row['username'],
                    email=row['email'],
                    password_hash=row['password_hash'],
                    role=UserRole(row['role']),
                    is_active=bool(row['is_active']),
                    is_verified=bool(row['is_verified']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']),
                    last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
                    failed_login_attempts=row['failed_login_attempts'],
                    locked_until=datetime.fromisoformat(row['locked_until']) if row['locked_until'] else None,
                    mfa_enabled=bool(row['mfa_enabled']),
                    mfa_secret=row['mfa_secret'],
                    assigned_agents=eval(row['assigned_agents']) if row['assigned_agents'] else [],
                    metadata=eval(row['metadata']) if row['metadata'] else {}
                )
            return None
    
    def _get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            
            if row:
                return User(
                    user_id=row['user_id'],
                    username=row['username'],
                    email=row['email'],
                    password_hash=row['password_hash'],
                    role=UserRole(row['role']),
                    is_active=bool(row['is_active']),
                    is_verified=bool(row['is_verified']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']),
                    last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
                    failed_login_attempts=row['failed_login_attempts'],
                    locked_until=datetime.fromisoformat(row['locked_until']) if row['locked_until'] else None,
                    mfa_enabled=bool(row['mfa_enabled']),
                    mfa_secret=row['mfa_secret'],
                    assigned_agents=eval(row['assigned_agents']) if row['assigned_agents'] else [],
                    metadata=eval(row['metadata']) if row['metadata'] else {}
                )
            return None
    
    def _create_token(self, user: User, token_type: str = "access") -> Tuple[str, datetime]:
        """Create JWT token for user."""
        now = datetime.now(timezone.utc)
        
        if token_type == "access":
            expire_delta = timedelta(minutes=self.access_token_expire_minutes)
        else:  # refresh token
            expire_delta = timedelta(days=self.refresh_token_expire_days)
        
        expire_time = now + expire_delta
        
        payload = {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role.value,
            "permissions": [p.value for p in self.ROLE_PERMISSIONS[user.role]],
            "token_type": token_type,
            "exp": expire_time,
            "iat": now,
            "jti": secrets.token_urlsafe(16)
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token, expire_time
    
    def _verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Check if token is revoked
            if self._is_token_revoked(payload.get("jti")):
                return None
            
            return TokenData(
                user_id=payload["user_id"],
                username=payload["username"],
                role=UserRole(payload["role"]),
                permissions=[Permission(p) for p in payload["permissions"]],
                exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
                iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
                jti=payload["jti"]
            )
        except jwt.InvalidTokenError:
            return None
    
    def _is_token_revoked(self, jti: str) -> bool:
        """Check if token is revoked."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT 1 FROM revoked_tokens WHERE jti = ?", (jti,))
            return cursor.fetchone() is not None
    
    def _revoke_token(self, jti: str, user_id: str, expires_at: datetime):
        """Revoke a token."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR IGNORE INTO revoked_tokens (jti, user_id, expires_at)
                VALUES (?, ?, ?)
            """, (jti, user_id, expires_at))
            conn.commit()
    
    def _log_audit_event(self, user_id: Optional[str], action: str, resource: str = None,
                        details: str = None, ip_address: str = None, user_agent: str = None):
        """Log audit event."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO audit_logs (log_id, user_id, action, resource, details, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                secrets.token_urlsafe(16), user_id, action, resource, details, ip_address, user_agent
            ))
            conn.commit()
    
    def _verify_mfa_code(self, user: User, mfa_code: str) -> bool:
        """Verify MFA TOTP code."""
        if not user.mfa_enabled or not user.mfa_secret:
            return True  # MFA not enabled
        
        totp = pyotp.TOTP(user.mfa_secret)
        return totp.verify(mfa_code, valid_window=1)  # Allow 30-second window
    
    async def authenticate_user(self, login_request: LoginRequest, 
                              ip_address: str = None, user_agent: str = None) -> LoginResponse:
        """Authenticate user and return tokens."""
        user = self._get_user_by_username(login_request.username)
        
        if not user:
            self._log_audit_event(None, "LOGIN_FAILED", details="User not found", 
                                ip_address=ip_address, user_agent=user_agent)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            self._log_audit_event(user.user_id, "LOGIN_BLOCKED", details="Account locked",
                                ip_address=ip_address, user_agent=user_agent)
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account locked until {user.locked_until}"
            )
        
        # Check if account is active
        if not user.is_active:
            self._log_audit_event(user.user_id, "LOGIN_FAILED", details="Account inactive",
                                ip_address=ip_address, user_agent=user_agent)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        # Verify password
        if not self._verify_password(login_request.password, user.password_hash):
            # Increment failed attempts
            user.failed_login_attempts += 1
            
            # Lock account if too many failed attempts
            if user.failed_login_attempts >= self.max_failed_attempts:
                user.locked_until = datetime.utcnow() + timedelta(minutes=self.lockout_duration_minutes)
            
            user.updated_at = datetime.utcnow()
            self._save_user(user)
            
            self._log_audit_event(user.user_id, "LOGIN_FAILED", details="Invalid password",
                                ip_address=ip_address, user_agent=user_agent)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Verify MFA if enabled
        if user.mfa_enabled:
            if not login_request.mfa_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="MFA code required"
                )
            
            if not self._verify_mfa_code(user, login_request.mfa_code):
                self._log_audit_event(user.user_id, "LOGIN_FAILED", details="Invalid MFA code",
                                    ip_address=ip_address, user_agent=user_agent)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid MFA code"
                )
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        self._save_user(user)
        
        # Create tokens
        access_token, access_expire = self._create_token(user, "access")
        refresh_token, refresh_expire = self._create_token(user, "refresh")
        
        self._log_audit_event(user.user_id, "LOGIN_SUCCESS", 
                            ip_address=ip_address, user_agent=user_agent)
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60,
            user={
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "permissions": [p.value for p in self.ROLE_PERMISSIONS[user.role]],
                "is_verified": user.is_verified,
                "mfa_enabled": user.mfa_enabled,
                "assigned_agents": user.assigned_agents,
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
        )
    
    async def refresh_token(self, refresh_token: str) -> LoginResponse:
        """Refresh access token using refresh token."""
        token_data = self._verify_token(refresh_token)
        
        if not token_data or token_data.exp < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        user = self._get_user_by_id(token_data.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Revoke old refresh token
        self._revoke_token(token_data.jti, user.user_id, token_data.exp)
        
        # Create new tokens
        access_token, access_expire = self._create_token(user, "access")
        new_refresh_token, refresh_expire = self._create_token(user, "refresh")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60,
            user={
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "permissions": [p.value for p in self.ROLE_PERMISSIONS[user.role]],
                "is_verified": user.is_verified,
                "mfa_enabled": user.mfa_enabled,
                "assigned_agents": user.assigned_agents,
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
        )
    
    async def logout(self, token: str, user_id: str):
        """Logout user and revoke token."""
        token_data = self._verify_token(token)
        if token_data:
            self._revoke_token(token_data.jti, user_id, token_data.exp)
            self._log_audit_event(user_id, "LOGOUT")
    
    def verify_permission(self, user_role: UserRole, required_permission: Permission) -> bool:
        """Check if user role has required permission."""
        return required_permission in self.ROLE_PERMISSIONS.get(user_role, [])
    
    def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from token."""
        token_data = self._verify_token(token)
        if token_data:
            return self._get_user_by_id(token_data.user_id)
        return None


# Global auth service instance
_auth_service: Optional[AuthService] = None

def get_auth_service() -> AuthService:
    """Get or create auth service instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


# FastAPI dependency function for getting current user
async def get_current_user(token: str) -> Optional[User]:
    """
    FastAPI dependency to get current authenticated user from token.
    This is a convenience wrapper for use in endpoint dependencies.
    """
    auth_service = get_auth_service()
    return auth_service.get_current_user(token)
