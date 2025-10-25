"""
User Workspace API Endpoints
Provides REST API for user workspaces, projects, favorites, settings, and API keys.
"""

import logging
import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.models.workspace_schemas import (
    Project, ProjectCreate, ProjectUpdate, ProjectStatus,
    Favorite, FavoriteCreate, FavoriteType,
    WorkspaceSetting, WorkspaceSettingCreate,
    APIKey, APIKeyCreate, APIKeyResponse,
    DashboardStats, RecentActivity, UserWorkspace
)
from src.services.workspace_service import WorkspaceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workspace", tags=["workspace"])
security = HTTPBearer()

# Initialize workspace service
DATABASE_URL = os.getenv("WORKSPACE_DATABASE_URL", "sqlite:///workspace.db")
workspace_service = WorkspaceService(DATABASE_URL)


# Authentication Helper
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Verify API key and return user information.
    In production, this would validate JWT tokens or API keys.
    """
    token = credentials.credentials
    
    # Verify API key
    user_info = workspace_service.verify_api_key(token)
    
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid or expired API key")
    
    return user_info


# Workspace Overview
@router.get("/", response_model=UserWorkspace)
async def get_workspace(
    current_user: dict = Depends(get_current_user)
):
    """
    Get complete workspace overview for the authenticated user.
    
    Returns:
    - Dashboard statistics
    - Recent activity
    - Active projects
    - Favorites
    - API keys
    """
    try:
        # In production, fetch email and subscription from user service
        user_id = current_user["user_id"]
        email = "user@example.com"  # TODO: Fetch from user service
        subscription_tier = "pro"  # TODO: Fetch from subscription service
        
        workspace = workspace_service.get_workspace(user_id, email, subscription_tier)
        return workspace
    except Exception as e:
        logger.error(f"Error fetching workspace: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch workspace")


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: dict = Depends(get_current_user)
):
    """Get dashboard statistics for the authenticated user."""
    try:
        stats = workspace_service.get_dashboard_stats(current_user["user_id"])
        return stats
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")


@router.get("/activity", response_model=List[RecentActivity])
async def get_recent_activity(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Get recent activity for the authenticated user."""
    try:
        activity = workspace_service.get_recent_activity(current_user["user_id"], limit)
        return activity
    except Exception as e:
        logger.error(f"Error fetching activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch activity")


# Project Management
@router.post("/projects", response_model=Project, status_code=201)
async def create_project(
    project_data: ProjectCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new project."""
    try:
        project = workspace_service.create_project(current_user["user_id"], project_data)
        return project
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail="Failed to create project")


@router.get("/projects", response_model=List[Project])
async def list_projects(
    status: Optional[ProjectStatus] = None,
    current_user: dict = Depends(get_current_user)
):
    """List all projects for the authenticated user."""
    try:
        projects = workspace_service.list_projects(current_user["user_id"], status)
        return projects
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to list projects")


@router.get("/projects/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific project."""
    try:
        project = workspace_service.get_project(current_user["user_id"], project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch project")


@router.patch("/projects/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    update_data: ProjectUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a project."""
    try:
        project = workspace_service.update_project(
            current_user["user_id"], project_id, update_data
        )
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project: {e}")
        raise HTTPException(status_code=500, detail="Failed to update project")


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a project."""
    try:
        success = workspace_service.delete_project(current_user["user_id"], project_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete project")


# Favorites Management
@router.post("/favorites", response_model=Favorite, status_code=201)
async def add_favorite(
    favorite_data: FavoriteCreate,
    current_user: dict = Depends(get_current_user)
):
    """Add an item to favorites."""
    try:
        favorite = workspace_service.add_favorite(current_user["user_id"], favorite_data)
        return favorite
    except Exception as e:
        logger.error(f"Error adding favorite: {e}")
        raise HTTPException(status_code=500, detail="Failed to add favorite")


@router.get("/favorites", response_model=List[Favorite])
async def list_favorites(
    item_type: Optional[FavoriteType] = None,
    current_user: dict = Depends(get_current_user)
):
    """List all favorites for the authenticated user."""
    try:
        favorites = workspace_service.list_favorites(current_user["user_id"], item_type)
        return favorites
    except Exception as e:
        logger.error(f"Error listing favorites: {e}")
        raise HTTPException(status_code=500, detail="Failed to list favorites")


@router.delete("/favorites/{favorite_id}", status_code=204)
async def remove_favorite(
    favorite_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove an item from favorites."""
    try:
        success = workspace_service.remove_favorite(current_user["user_id"], favorite_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Favorite not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing favorite: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove favorite")


# Settings Management
@router.put("/settings", response_model=WorkspaceSetting)
async def set_setting(
    setting_data: WorkspaceSettingCreate,
    current_user: dict = Depends(get_current_user)
):
    """Set or update a workspace setting."""
    try:
        setting = workspace_service.set_setting(current_user["user_id"], setting_data)
        return setting
    except Exception as e:
        logger.error(f"Error setting workspace setting: {e}")
        raise HTTPException(status_code=500, detail="Failed to set setting")


@router.get("/settings", response_model=List[WorkspaceSetting])
async def list_settings(
    current_user: dict = Depends(get_current_user)
):
    """List all workspace settings for the authenticated user."""
    try:
        settings = workspace_service.list_settings(current_user["user_id"])
        return settings
    except Exception as e:
        logger.error(f"Error listing settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to list settings")


@router.get("/settings/{key}", response_model=WorkspaceSetting)
async def get_setting(
    key: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific workspace setting."""
    try:
        setting = workspace_service.get_setting(current_user["user_id"], key)
        
        if not setting:
            raise HTTPException(status_code=404, detail="Setting not found")
        
        return setting
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching setting: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch setting")


# API Key Management
@router.post("/api-keys", response_model=APIKeyResponse, status_code=201)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new API key.
    
    WARNING: The full API key is only returned once during creation.
    Store it securely - it cannot be retrieved later.
    """
    try:
        api_key_response = workspace_service.create_api_key(current_user["user_id"], key_data)
        return api_key_response
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to create API key")


@router.get("/api-keys", response_model=List[APIKey])
async def list_api_keys(
    current_user: dict = Depends(get_current_user)
):
    """List all API keys for the authenticated user."""
    try:
        api_keys = workspace_service.list_api_keys(current_user["user_id"])
        return api_keys
    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        raise HTTPException(status_code=500, detail="Failed to list API keys")


@router.post("/api-keys/{key_id}/revoke", status_code=200)
async def revoke_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Revoke (deactivate) an API key."""
    try:
        success = workspace_service.revoke_api_key(current_user["user_id"], key_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="API key not found")
        
        return {"message": "API key revoked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to revoke API key")


@router.delete("/api-keys/{key_id}", status_code=204)
async def delete_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Permanently delete an API key."""
    try:
        success = workspace_service.delete_api_key(current_user["user_id"], key_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="API key not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete API key")


# Health Check
@router.get("/health")
async def workspace_health():
    """Health check endpoint for workspace service."""
    return {
        "status": "healthy",
        "service": "workspace",
        "version": "1.0.0"
    }

