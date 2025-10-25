"""
User Workspace Service
Manages user workspaces, projects, favorites, settings, and API keys.
"""

import logging
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, String, DateTime, Integer, JSON, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func

from src.models.workspace_schemas import (
    Project, ProjectCreate, ProjectUpdate, ProjectStatus,
    Favorite, FavoriteCreate, FavoriteType,
    WorkspaceSetting, WorkspaceSettingCreate,
    APIKey, APIKeyCreate, APIKeyResponse,
    DashboardStats, RecentActivity, UserWorkspace
)

logger = logging.getLogger(__name__)

Base = declarative_base()


# Database Models
class ProjectDB(Base):
    """Project database model."""
    __tablename__ = "projects"
    
    project_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="active")
    tags = Column(JSON, default=list)
    settings = Column(JSON, default=dict)
    test_count = Column(Integer, default=0)
    agent_count = Column(Integer, default=0)
    last_activity = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FavoriteDB(Base):
    """Favorite database model."""
    __tablename__ = "favorites"
    
    favorite_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    item_type = Column(String(50), nullable=False)
    item_id = Column(String, nullable=False)
    item_name = Column(String(200), nullable=False)
    item_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


class WorkspaceSettingDB(Base):
    """Workspace setting database model."""
    __tablename__ = "workspace_settings"
    
    setting_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    key = Column(String(100), nullable=False)
    value = Column(JSON, nullable=False)
    category = Column(String(50), default="general")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class APIKeyDB(Base):
    """API key database model."""
    __tablename__ = "api_keys"
    
    key_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    key_prefix = Column(String(20), nullable=False)
    key_hash = Column(String(64), nullable=False, unique=True)
    scopes = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ActivityLogDB(Base):
    """Activity log database model."""
    __tablename__ = "activity_logs"
    
    activity_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    activity_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    activity_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class WorkspaceService:
    """Service for managing user workspaces."""
    
    def __init__(self, database_url: str = "sqlite:///workspace.db"):
        """Initialize workspace service with database connection."""
        self.engine = create_engine(database_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info("Workspace service initialized")
    
    def _get_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()
    
    # Project Management
    def create_project(self, user_id: str, project_data: ProjectCreate) -> Project:
        """Create a new project."""
        session = self._get_session()
        try:
            project_id = f"proj_{uuid.uuid4().hex[:12]}"
            
            db_project = ProjectDB(
                project_id=project_id,
                user_id=user_id,
                name=project_data.name,
                description=project_data.description,
                tags=project_data.tags,
                settings=project_data.settings,
                status=ProjectStatus.ACTIVE.value
            )
            
            session.add(db_project)
            session.commit()
            session.refresh(db_project)
            
            # Log activity
            self._log_activity(
                session, user_id, "project_created",
                f"Created project: {project_data.name}",
                {"project_id": project_id}
            )
            
            return self._project_from_db(db_project)
        finally:
            session.close()
    
    def get_project(self, user_id: str, project_id: str) -> Optional[Project]:
        """Get a specific project."""
        session = self._get_session()
        try:
            db_project = session.query(ProjectDB).filter(
                ProjectDB.project_id == project_id,
                ProjectDB.user_id == user_id
            ).first()
            
            if not db_project:
                return None
            
            return self._project_from_db(db_project)
        finally:
            session.close()
    
    def list_projects(self, user_id: str, status: Optional[ProjectStatus] = None) -> List[Project]:
        """List all projects for a user."""
        session = self._get_session()
        try:
            query = session.query(ProjectDB).filter(ProjectDB.user_id == user_id)
            
            if status:
                query = query.filter(ProjectDB.status == status.value)
            
            db_projects = query.order_by(ProjectDB.updated_at.desc()).all()
            return [self._project_from_db(p) for p in db_projects]
        finally:
            session.close()
    
    def update_project(self, user_id: str, project_id: str, update_data: ProjectUpdate) -> Optional[Project]:
        """Update a project."""
        session = self._get_session()
        try:
            db_project = session.query(ProjectDB).filter(
                ProjectDB.project_id == project_id,
                ProjectDB.user_id == user_id
            ).first()
            
            if not db_project:
                return None
            
            # Update fields
            if update_data.name is not None:
                db_project.name = update_data.name
            if update_data.description is not None:
                db_project.description = update_data.description
            if update_data.tags is not None:
                db_project.tags = update_data.tags
            if update_data.status is not None:
                db_project.status = update_data.status.value
            if update_data.settings is not None:
                db_project.settings = update_data.settings
            
            db_project.updated_at = datetime.utcnow()
            
            session.commit()
            session.refresh(db_project)
            
            return self._project_from_db(db_project)
        finally:
            session.close()
    
    def delete_project(self, user_id: str, project_id: str) -> bool:
        """Delete a project."""
        session = self._get_session()
        try:
            result = session.query(ProjectDB).filter(
                ProjectDB.project_id == project_id,
                ProjectDB.user_id == user_id
            ).delete()
            
            session.commit()
            
            if result > 0:
                self._log_activity(
                    session, user_id, "project_deleted",
                    f"Deleted project: {project_id}",
                    {"project_id": project_id}
                )
            
            return result > 0
        finally:
            session.close()
    
    # Favorites Management
    def add_favorite(self, user_id: str, favorite_data: FavoriteCreate) -> Favorite:
        """Add an item to favorites."""
        session = self._get_session()
        try:
            favorite_id = f"fav_{uuid.uuid4().hex[:12]}"
            
            db_favorite = FavoriteDB(
                favorite_id=favorite_id,
                user_id=user_id,
                item_type=favorite_data.item_type.value,
                item_id=favorite_data.item_id,
                item_name=favorite_data.item_name,
                item_metadata=favorite_data.item_metadata
            )
            
            session.add(db_favorite)
            session.commit()
            session.refresh(db_favorite)
            
            return self._favorite_from_db(db_favorite)
        finally:
            session.close()
    
    def list_favorites(self, user_id: str, item_type: Optional[FavoriteType] = None) -> List[Favorite]:
        """List all favorites for a user."""
        session = self._get_session()
        try:
            query = session.query(FavoriteDB).filter(FavoriteDB.user_id == user_id)
            
            if item_type:
                query = query.filter(FavoriteDB.item_type == item_type.value)
            
            db_favorites = query.order_by(FavoriteDB.created_at.desc()).all()
            return [self._favorite_from_db(f) for f in db_favorites]
        finally:
            session.close()
    
    def remove_favorite(self, user_id: str, favorite_id: str) -> bool:
        """Remove an item from favorites."""
        session = self._get_session()
        try:
            result = session.query(FavoriteDB).filter(
                FavoriteDB.favorite_id == favorite_id,
                FavoriteDB.user_id == user_id
            ).delete()
            
            session.commit()
            return result > 0
        finally:
            session.close()
    
    # Settings Management
    def set_setting(self, user_id: str, setting_data: WorkspaceSettingCreate) -> WorkspaceSetting:
        """Set or update a workspace setting."""
        session = self._get_session()
        try:
            # Check if setting exists
            db_setting = session.query(WorkspaceSettingDB).filter(
                WorkspaceSettingDB.user_id == user_id,
                WorkspaceSettingDB.key == setting_data.key
            ).first()
            
            if db_setting:
                # Update existing
                db_setting.value = setting_data.value
                db_setting.category = setting_data.category
                db_setting.updated_at = datetime.utcnow()
            else:
                # Create new
                setting_id = f"set_{uuid.uuid4().hex[:12]}"
                db_setting = WorkspaceSettingDB(
                    setting_id=setting_id,
                    user_id=user_id,
                    key=setting_data.key,
                    value=setting_data.value,
                    category=setting_data.category
                )
                session.add(db_setting)
            
            session.commit()
            session.refresh(db_setting)
            
            return self._setting_from_db(db_setting)
        finally:
            session.close()
    
    def get_setting(self, user_id: str, key: str) -> Optional[WorkspaceSetting]:
        """Get a specific setting."""
        session = self._get_session()
        try:
            db_setting = session.query(WorkspaceSettingDB).filter(
                WorkspaceSettingDB.user_id == user_id,
                WorkspaceSettingDB.key == key
            ).first()
            
            if not db_setting:
                return None
            
            return self._setting_from_db(db_setting)
        finally:
            session.close()
    
    def list_settings(self, user_id: str) -> List[WorkspaceSetting]:
        """List all settings for a user."""
        session = self._get_session()
        try:
            db_settings = session.query(WorkspaceSettingDB).filter(
                WorkspaceSettingDB.user_id == user_id
            ).all()
            
            return [self._setting_from_db(s) for s in db_settings]
        finally:
            session.close()
    
    # API Key Management
    def create_api_key(self, user_id: str, key_data: APIKeyCreate) -> APIKeyResponse:
        """Create a new API key."""
        session = self._get_session()
        try:
            key_id = f"key_{uuid.uuid4().hex[:12]}"
            
            # Generate API key
            raw_key = f"ag_live_{secrets.token_urlsafe(32)}"
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
            key_prefix = raw_key[:15]
            
            db_key = APIKeyDB(
                key_id=key_id,
                user_id=user_id,
                name=key_data.name,
                description=key_data.description,
                key_prefix=key_prefix,
                key_hash=key_hash,
                scopes=key_data.scopes,
                expires_at=key_data.expires_at
            )
            
            session.add(db_key)
            session.commit()
            session.refresh(db_key)
            
            # Log activity
            self._log_activity(
                session, user_id, "api_key_created",
                f"Created API key: {key_data.name}",
                {"key_id": key_id}
            )
            
            return APIKeyResponse(
                key_id=key_id,
                name=key_data.name,
                api_key=raw_key,  # Only time the full key is returned
                key_prefix=key_prefix,
                scopes=key_data.scopes,
                created_at=db_key.created_at,
                expires_at=key_data.expires_at
            )
        finally:
            session.close()
    
    def list_api_keys(self, user_id: str) -> List[APIKey]:
        """List all API keys for a user."""
        session = self._get_session()
        try:
            db_keys = session.query(APIKeyDB).filter(
                APIKeyDB.user_id == user_id
            ).order_by(APIKeyDB.created_at.desc()).all()
            
            return [self._api_key_from_db(k) for k in db_keys]
        finally:
            session.close()
    
    def revoke_api_key(self, user_id: str, key_id: str) -> bool:
        """Revoke (deactivate) an API key."""
        session = self._get_session()
        try:
            db_key = session.query(APIKeyDB).filter(
                APIKeyDB.key_id == key_id,
                APIKeyDB.user_id == user_id
            ).first()
            
            if not db_key:
                return False
            
            db_key.is_active = False
            session.commit()
            
            self._log_activity(
                session, user_id, "api_key_revoked",
                f"Revoked API key: {db_key.name}",
                {"key_id": key_id}
            )
            
            return True
        finally:
            session.close()
    
    def delete_api_key(self, user_id: str, key_id: str) -> bool:
        """Permanently delete an API key."""
        session = self._get_session()
        try:
            result = session.query(APIKeyDB).filter(
                APIKeyDB.key_id == key_id,
                APIKeyDB.user_id == user_id
            ).delete()
            
            session.commit()
            return result > 0
        finally:
            session.close()
    
    def verify_api_key(self, raw_key: str) -> Optional[Dict[str, Any]]:
        """Verify an API key and return user info."""
        session = self._get_session()
        try:
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
            
            db_key = session.query(APIKeyDB).filter(
                APIKeyDB.key_hash == key_hash,
                APIKeyDB.is_active == True
            ).first()
            
            if not db_key:
                return None
            
            # Check expiration
            if db_key.expires_at and db_key.expires_at < datetime.utcnow():
                return None
            
            # Update last used
            db_key.last_used_at = datetime.utcnow()
            session.commit()
            
            return {
                "user_id": db_key.user_id,
                "key_id": db_key.key_id,
                "scopes": db_key.scopes
            }
        finally:
            session.close()
    
    # Dashboard & Analytics
    def get_dashboard_stats(self, user_id: str) -> DashboardStats:
        """Get dashboard statistics for a user."""
        session = self._get_session()
        try:
            # Count projects
            total_projects = session.query(ProjectDB).filter(
                ProjectDB.user_id == user_id,
                ProjectDB.status == ProjectStatus.ACTIVE.value
            ).count()
            
            # Sum test counts
            project_stats = session.query(
                func.sum(ProjectDB.test_count),
                func.sum(ProjectDB.agent_count)
            ).filter(ProjectDB.user_id == user_id).first()
            
            total_tests = project_stats[0] or 0
            total_agents = project_stats[1] or 0
            
            # Count favorites
            total_favorites = session.query(FavoriteDB).filter(
                FavoriteDB.user_id == user_id
            ).count()
            
            # Get last activity
            last_activity = session.query(ActivityLogDB).filter(
                ActivityLogDB.user_id == user_id
            ).order_by(ActivityLogDB.created_at.desc()).first()
            
            return DashboardStats(
                total_projects=total_projects,
                total_tests=total_tests,
                total_agents=total_agents,
                total_favorites=total_favorites,
                last_test_at=last_activity.created_at if last_activity else None
            )
        finally:
            session.close()
    
    def get_recent_activity(self, user_id: str, limit: int = 10) -> List[RecentActivity]:
        """Get recent activity for a user."""
        session = self._get_session()
        try:
            db_activities = session.query(ActivityLogDB).filter(
                ActivityLogDB.user_id == user_id
            ).order_by(ActivityLogDB.created_at.desc()).limit(limit).all()
            
            return [self._activity_from_db(a) for a in db_activities]
        finally:
            session.close()
    
    def get_workspace(self, user_id: str, email: str, subscription_tier: str) -> UserWorkspace:
        """Get complete workspace overview for a user."""
        stats = self.get_dashboard_stats(user_id)
        recent_activity = self.get_recent_activity(user_id, limit=5)
        active_projects = self.list_projects(user_id, status=ProjectStatus.ACTIVE)[:5]
        favorites = self.list_favorites(user_id)[:10]
        api_keys = self.list_api_keys(user_id)
        
        return UserWorkspace(
            user_id=user_id,
            email=email,
            subscription_tier=subscription_tier,
            stats=stats,
            recent_activity=recent_activity,
            active_projects=active_projects,
            favorites=favorites,
            api_keys=api_keys
        )
    
    # Helper Methods
    def _log_activity(self, session: Session, user_id: str, activity_type: str, 
                     title: str, metadata: Dict[str, Any] = None):
        """Log user activity."""
        activity_id = f"act_{uuid.uuid4().hex[:12]}"
        
        db_activity = ActivityLogDB(
            activity_id=activity_id,
            user_id=user_id,
            activity_type=activity_type,
            title=title,
            activity_metadata=metadata or {}
        )
        
        session.add(db_activity)
    
    def _project_from_db(self, db_project: ProjectDB) -> Project:
        """Convert database project to Pydantic model."""
        return Project(
            project_id=db_project.project_id,
            user_id=db_project.user_id,
            name=db_project.name,
            description=db_project.description,
            status=ProjectStatus(db_project.status),
            tags=db_project.tags or [],
            settings=db_project.settings or {},
            test_count=db_project.test_count,
            agent_count=db_project.agent_count,
            last_activity=db_project.last_activity,
            created_at=db_project.created_at,
            updated_at=db_project.updated_at
        )
    
    def _favorite_from_db(self, db_favorite: FavoriteDB) -> Favorite:
        """Convert database favorite to Pydantic model."""
        return Favorite(
            favorite_id=db_favorite.favorite_id,
            user_id=db_favorite.user_id,
            item_type=FavoriteType(db_favorite.item_type),
            item_id=db_favorite.item_id,
            item_name=db_favorite.item_name,
            item_metadata=db_favorite.item_metadata or {},
            created_at=db_favorite.created_at
        )
    
    def _setting_from_db(self, db_setting: WorkspaceSettingDB) -> WorkspaceSetting:
        """Convert database setting to Pydantic model."""
        return WorkspaceSetting(
            setting_id=db_setting.setting_id,
            user_id=db_setting.user_id,
            key=db_setting.key,
            value=db_setting.value,
            category=db_setting.category,
            created_at=db_setting.created_at,
            updated_at=db_setting.updated_at
        )
    
    def _api_key_from_db(self, db_key: APIKeyDB) -> APIKey:
        """Convert database API key to Pydantic model."""
        return APIKey(
            key_id=db_key.key_id,
            user_id=db_key.user_id,
            name=db_key.name,
            description=db_key.description,
            key_prefix=db_key.key_prefix,
            key_hash=db_key.key_hash,
            scopes=db_key.scopes or [],
            is_active=db_key.is_active,
            last_used_at=db_key.last_used_at,
            expires_at=db_key.expires_at,
            created_at=db_key.created_at
        )
    
    def _activity_from_db(self, db_activity: ActivityLogDB) -> RecentActivity:
        """Convert database activity to Pydantic model."""
        return RecentActivity(
            activity_id=db_activity.activity_id,
            activity_type=db_activity.activity_type,
            title=db_activity.title,
            description=db_activity.description,
            metadata=db_activity.activity_metadata or {},
            created_at=db_activity.created_at
        )

