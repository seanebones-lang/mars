#!/usr/bin/env python3
"""
Initialize AgentGuard Workspace Database
Creates all necessary tables and indexes for the workspace system
"""

import os
import sys
import asyncio
from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean, 
    DateTime, JSON, ForeignKey, Text, Enum as SQLEnum, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from datetime import datetime
import uuid
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

# ============================================
# MODELS
# ============================================

class User(Base):
    """User accounts"""
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    subscription_tier = Column(String(50), default='free')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("WorkspaceSetting", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    """User projects"""
    __tablename__ = 'projects'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    status = Column(String(20), default='active')  # active, archived, deleted
    tags = Column(ARRAY(String), default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="projects")
    
    # Indexes
    __table_args__ = (
        Index('idx_projects_user_updated', 'user_id', 'updated_at'),
        Index('idx_projects_status', 'user_id', 'status'),
        Index('idx_projects_tags', 'tags', postgresql_using='gin'),
    )


class APIKey(Base):
    """User API keys"""
    __tablename__ = 'api_keys'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    permissions = Column(ARRAY(String), default=['read', 'write'])
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    last_used_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    # Indexes
    __table_args__ = (
        Index('idx_api_keys_user_active', 'user_id', 'is_active'),
        Index('idx_api_keys_expires', 'expires_at', postgresql_where='expires_at IS NOT NULL'),
    )


class Favorite(Base):
    """User favorites"""
    __tablename__ = 'favorites'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    item_id = Column(String(255), nullable=False)
    item_type = Column(String(50), nullable=False)  # agent, prompt, workflow, project, report
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="favorites")
    
    # Indexes
    __table_args__ = (
        Index('idx_favorites_user_type', 'user_id', 'item_type', 'created_at'),
        Index('idx_favorites_item', 'item_type', 'item_id'),
    )


class WorkspaceSetting(Base):
    """User workspace settings"""
    __tablename__ = 'workspace_settings'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    key = Column(String(100), nullable=False)
    value = Column(JSON, nullable=False)
    category = Column(String(50))  # appearance, notifications, privacy, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="settings")
    
    # Indexes
    __table_args__ = (
        Index('idx_workspace_settings_user_key', 'user_id', 'key'),
        Index('idx_workspace_settings_category', 'user_id', 'category'),
    )


class ActivityLog(Base):
    """User activity logs"""
    __tablename__ = 'activity_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    activity_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    details = Column(JSON, default=dict)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="activity_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_activity_logs_user_created', 'user_id', 'created_at'),
        Index('idx_activity_logs_type', 'user_id', 'activity_type', 'created_at'),
    )


class UsageMetric(Base):
    """User usage metrics"""
    __tablename__ = 'usage_metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    total_api_calls = Column(Integer, default=0)
    hallucination_detections = Column(Integer, default=0)
    prompt_injection_blocks = Column(Integer, default=0)
    agents_monitored = Column(Integer, default=0)
    data_processed_gb = Column(Float, default=0.0)
    cost_usd = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_usage_metrics_user', 'user_id'),
    )


# ============================================
# DATABASE INITIALIZATION
# ============================================

def get_database_url():
    """Get database URL from environment"""
    db_url = os.getenv('WORKSPACE_DATABASE_URL') or os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("No database URL found. Set WORKSPACE_DATABASE_URL or DATABASE_URL environment variable.")
    return db_url


def init_database():
    """Initialize database with all tables and indexes"""
    try:
        db_url = get_database_url()
        logger.info(f"Connecting to database...")
        
        # Create engine
        engine = create_engine(db_url, echo=True)
        
        # Create all tables
        logger.info("Creating tables...")
        Base.metadata.create_all(engine)
        
        logger.info("✅ Database initialized successfully!")
        logger.info(f"Created tables: {', '.join(Base.metadata.tables.keys())}")
        
        # Verify tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Verified {len(tables)} tables in database")
        
        # Verify indexes
        for table_name in tables:
            indexes = inspector.get_indexes(table_name)
            logger.info(f"Table '{table_name}' has {len(indexes)} indexes")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False


def create_test_user():
    """Create a test user for development"""
    try:
        db_url = get_database_url()
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if test user exists
        test_email = "test@agentguard.ai"
        existing_user = session.query(User).filter_by(email=test_email).first()
        
        if existing_user:
            logger.info(f"Test user already exists: {test_email}")
            return existing_user.id
        
        # Create test user
        from passlib.hash import bcrypt
        test_user = User(
            email=test_email,
            username="testuser",
            hashed_password=bcrypt.hash("testpassword123"),
            full_name="Test User",
            is_active=True,
            is_verified=True,
            subscription_tier="pro"
        )
        
        session.add(test_user)
        session.commit()
        
        logger.info(f"✅ Created test user: {test_email}")
        logger.info(f"   Username: testuser")
        logger.info(f"   Password: testpassword123")
        logger.info(f"   User ID: {test_user.id}")
        
        # Create initial usage metrics
        usage = UsageMetric(user_id=test_user.id)
        session.add(usage)
        session.commit()
        
        return test_user.id
        
    except Exception as e:
        logger.error(f"❌ Failed to create test user: {e}")
        session.rollback()
        return None
    finally:
        session.close()


def seed_test_data(user_id):
    """Seed test data for development"""
    try:
        db_url = get_database_url()
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create test projects
        projects = [
            Project(
                user_id=user_id,
                name="RAG Pipeline",
                description="Document Q&A system with semantic search",
                status="active",
                tags=["rag", "langchain", "pinecone"]
            ),
            Project(
                user_id=user_id,
                name="Agent Swarm",
                description="Multi-agent collaboration system",
                status="active",
                tags=["agents", "crewai", "orchestration"]
            ),
            Project(
                user_id=user_id,
                name="Fine-Tuning Lab",
                description="Model fine-tuning experiments",
                status="archived",
                tags=["fine-tuning", "openai", "datasets"]
            )
        ]
        
        for project in projects:
            session.add(project)
        
        # Create test API key
        import hashlib
        test_key = "ag_test_" + str(uuid.uuid4()).replace('-', '')
        key_hash = hashlib.sha256(test_key.encode()).hexdigest()
        
        api_key = APIKey(
            user_id=user_id,
            key_hash=key_hash,
            name="Development Key",
            is_active=True,
            permissions=["read", "write", "admin"]
        )
        session.add(api_key)
        
        # Create test favorites
        favorites = [
            Favorite(user_id=user_id, item_id="agent_001", item_type="agent"),
            Favorite(user_id=user_id, item_id="prompt_042", item_type="prompt"),
        ]
        
        for favorite in favorites:
            session.add(favorite)
        
        # Create test settings
        settings = [
            WorkspaceSetting(
                user_id=user_id,
                key="theme",
                value={"mode": "dark", "accent": "blue"},
                category="appearance"
            ),
            WorkspaceSetting(
                user_id=user_id,
                key="notifications",
                value={"email": True, "push": False, "slack": True},
                category="notifications"
            )
        ]
        
        for setting in settings:
            session.add(setting)
        
        # Create test activity logs
        activities = [
            ActivityLog(
                user_id=user_id,
                activity_type="project_created",
                description="Created project 'RAG Pipeline'",
                details={"project_name": "RAG Pipeline"}
            ),
            ActivityLog(
                user_id=user_id,
                activity_type="api_key_generated",
                description="Generated API key 'Development Key'",
                details={"key_name": "Development Key"}
            )
        ]
        
        for activity in activities:
            session.add(activity)
        
        session.commit()
        
        logger.info("✅ Test data seeded successfully!")
        logger.info(f"   API Key: {test_key}")
        logger.info(f"   Projects: {len(projects)}")
        logger.info(f"   Favorites: {len(favorites)}")
        logger.info(f"   Settings: {len(settings)}")
        
    except Exception as e:
        logger.error(f"❌ Failed to seed test data: {e}")
        session.rollback()
    finally:
        session.close()


def main():
    """Main execution"""
    logger.info("=" * 60)
    logger.info("AgentGuard Workspace Database Initialization")
    logger.info("=" * 60)
    
    # Initialize database
    if not init_database():
        sys.exit(1)
    
    # Ask if user wants to create test data
    if os.getenv('PYTHON_ENV') == 'production':
        logger.info("Production environment detected. Skipping test data.")
        return
    
    create_test = input("\nCreate test user and seed data? (y/n): ").lower()
    
    if create_test == 'y':
        user_id = create_test_user()
        if user_id:
            seed_test_data(user_id)
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Workspace database setup complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

