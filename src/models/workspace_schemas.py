"""
User Workspace Data Models
Defines schemas for user workspaces, projects, favorites, and settings.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ProjectStatus(str, Enum):
    """Project status enumeration."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    PAUSED = "paused"


class FavoriteType(str, Enum):
    """Types of items that can be favorited."""
    AGENT = "agent"
    PROMPT = "prompt"
    WORKFLOW = "workflow"
    TEST = "test"
    RULE = "rule"


class WorkspaceSettingKey(str, Enum):
    """Workspace setting keys."""
    THEME = "theme"
    NOTIFICATIONS = "notifications"
    DEFAULT_MODEL = "default_model"
    AUTO_SAVE = "auto_save"
    LANGUAGE = "language"


# Project Models
class ProjectCreate(BaseModel):
    """Schema for creating a new project."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    tags: List[str] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(default_factory=dict)


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    tags: Optional[List[str]] = None
    status: Optional[ProjectStatus] = None
    settings: Optional[Dict[str, Any]] = None


class Project(BaseModel):
    """Complete project schema."""
    project_id: str
    user_id: str
    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    tags: List[str] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    
    # Statistics
    test_count: int = 0
    agent_count: int = 0
    last_activity: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "proj_abc123",
                "user_id": "user_xyz789",
                "name": "Healthcare AI Agents",
                "description": "Testing medical chatbot responses",
                "status": "active",
                "tags": ["healthcare", "production"],
                "test_count": 45,
                "agent_count": 3
            }
        }


# Favorite Models
class FavoriteCreate(BaseModel):
    """Schema for creating a favorite."""
    item_type: FavoriteType
    item_id: str
    item_name: str
    item_metadata: Dict[str, Any] = Field(default_factory=dict)


class Favorite(BaseModel):
    """Complete favorite schema."""
    favorite_id: str
    user_id: str
    item_type: FavoriteType
    item_id: str
    item_name: str
    item_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "favorite_id": "fav_123",
                "user_id": "user_xyz789",
                "item_type": "agent",
                "item_id": "agent_456",
                "item_name": "Medical Chatbot",
                "item_metadata": {"accuracy": 0.95}
            }
        }


# Workspace Settings Models
class WorkspaceSettingCreate(BaseModel):
    """Schema for creating/updating a workspace setting."""
    key: str
    value: Any
    category: Optional[str] = "general"


class WorkspaceSetting(BaseModel):
    """Complete workspace setting schema."""
    setting_id: str
    user_id: str
    key: str
    value: Any
    category: str = "general"
    created_at: datetime
    updated_at: datetime


# API Key Models
class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    scopes: List[str] = Field(default_factory=lambda: ["read", "write"])
    expires_at: Optional[datetime] = None


class APIKey(BaseModel):
    """Complete API key schema."""
    key_id: str
    user_id: str
    name: str
    description: Optional[str] = None
    key_prefix: str  # First 8 characters for identification
    key_hash: str  # Hashed full key
    scopes: List[str]
    is_active: bool = True
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "key_id": "key_abc123",
                "user_id": "user_xyz789",
                "name": "Production API Key",
                "key_prefix": "ag_live_",
                "scopes": ["read", "write"],
                "is_active": True
            }
        }


class APIKeyResponse(BaseModel):
    """Response when creating an API key (includes full key once)."""
    key_id: str
    name: str
    api_key: str  # Full key - only shown once
    key_prefix: str
    scopes: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None


# Dashboard Models
class DashboardStats(BaseModel):
    """User dashboard statistics."""
    total_projects: int = 0
    total_tests: int = 0
    total_agents: int = 0
    total_favorites: int = 0
    
    # Usage stats
    queries_this_month: int = 0
    queries_limit: int = 0
    api_calls_today: int = 0
    
    # Performance metrics
    avg_accuracy: float = 0.0
    avg_latency_ms: float = 0.0
    
    # Recent activity
    last_test_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None


class RecentActivity(BaseModel):
    """Recent user activity item."""
    activity_id: str
    activity_type: str  # "test", "project_created", "agent_added", etc.
    title: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class UserWorkspace(BaseModel):
    """Complete user workspace overview."""
    user_id: str
    email: str
    subscription_tier: str
    stats: DashboardStats
    recent_activity: List[RecentActivity] = Field(default_factory=list)
    active_projects: List[Project] = Field(default_factory=list)
    favorites: List[Favorite] = Field(default_factory=list)
    api_keys: List[APIKey] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_xyz789",
                "email": "user@example.com",
                "subscription_tier": "pro",
                "stats": {
                    "total_projects": 5,
                    "total_tests": 120,
                    "queries_this_month": 450,
                    "queries_limit": 1000
                }
            }
        }

