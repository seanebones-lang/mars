"""
Multi-Tenant Architecture Service
Provides complete tenant isolation, custom branding, and resource management.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import sqlite3
import secrets
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)


class TenantStatus(Enum):
    """Tenant status enumeration."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    PENDING = "pending"
    CANCELLED = "cancelled"


class SubscriptionTier(Enum):
    """Subscription tier enumeration."""
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class BillingCycle(Enum):
    """Billing cycle enumeration."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


@dataclass
class TenantConfig:
    """Tenant configuration settings."""
    tenant_id: str
    name: str
    display_name: str
    domain: Optional[str] = None
    subdomain: Optional[str] = None
    status: TenantStatus = TenantStatus.ACTIVE
    subscription_tier: SubscriptionTier = SubscriptionTier.STARTER
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Branding
    logo_url: Optional[str] = None
    primary_color: str = "#1976D2"
    secondary_color: str = "#1565C0"
    custom_css: Optional[str] = None
    
    # Contact Information
    admin_email: str = ""
    support_email: str = ""
    billing_email: str = ""
    
    # Feature Flags
    features: Dict[str, bool] = field(default_factory=dict)
    
    # Resource Limits
    max_users: int = 10
    max_api_calls_per_month: int = 10000
    max_storage_gb: int = 5
    max_custom_rules: int = 10
    max_webhooks: int = 5
    
    # Compliance Settings
    compliance_frameworks: List[str] = field(default_factory=list)
    data_retention_days: int = 365
    audit_logging_enabled: bool = True
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.features:
            self.features = self._get_default_features()
        if not self.subdomain and self.name:
            self.subdomain = self.name.lower().replace(" ", "-").replace("_", "-")
    
    def _get_default_features(self) -> Dict[str, bool]:
        """Get default features based on subscription tier."""
        base_features = {
            "hallucination_detection": True,
            "basic_analytics": True,
            "email_alerts": True,
            "api_access": True,
            "audit_logs": True
        }
        
        if self.subscription_tier in [SubscriptionTier.PROFESSIONAL, SubscriptionTier.ENTERPRISE, SubscriptionTier.CUSTOM]:
            base_features.update({
                "advanced_analytics": True,
                "custom_rules": True,
                "webhook_integrations": True,
                "batch_processing": True,
                "performance_monitoring": True
            })
        
        if self.subscription_tier in [SubscriptionTier.ENTERPRISE, SubscriptionTier.CUSTOM]:
            base_features.update({
                "white_labeling": True,
                "sso_integration": True,
                "dedicated_support": True,
                "compliance_reporting": True,
                "custom_domains": True,
                "priority_processing": True
            })
        
        return base_features


@dataclass
class TenantUsage:
    """Tenant usage tracking."""
    tenant_id: str
    period_start: datetime
    period_end: datetime
    
    # API Usage
    api_calls_total: int = 0
    api_calls_by_endpoint: Dict[str, int] = field(default_factory=dict)
    
    # Detection Usage
    detections_performed: int = 0
    tokens_processed: int = 0
    
    # Storage Usage
    storage_used_gb: float = 0.0
    audit_logs_count: int = 0
    
    # User Activity
    active_users: int = 0
    total_sessions: int = 0
    
    # Custom Rules
    custom_rules_created: int = 0
    custom_rules_executed: int = 0
    
    # Webhooks
    webhooks_triggered: int = 0
    webhook_failures: int = 0
    
    # Costs
    estimated_cost_usd: float = 0.0
    claude_cost_usd: float = 0.0
    
    def calculate_cost(self, pricing_config: Dict[str, float]) -> float:
        """Calculate usage-based cost."""
        cost = 0.0
        
        # API call costs
        cost += self.api_calls_total * pricing_config.get("api_call_cost", 0.001)
        
        # Detection costs (higher rate)
        cost += self.detections_performed * pricing_config.get("detection_cost", 0.01)
        
        # Token processing costs
        cost += self.tokens_processed * pricing_config.get("token_cost", 0.00001)
        
        # Storage costs
        cost += self.storage_used_gb * pricing_config.get("storage_gb_cost", 0.1)
        
        # Add Claude API costs
        cost += self.claude_cost_usd
        
        self.estimated_cost_usd = cost
        return cost


@dataclass
class TenantDatabase:
    """Tenant database configuration."""
    tenant_id: str
    database_name: str
    connection_string: str
    schema_version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Database isolation settings
    isolated_schema: bool = True
    encryption_enabled: bool = True
    backup_enabled: bool = True
    
    # Performance settings
    connection_pool_size: int = 10
    query_timeout_seconds: int = 30


class TenantService:
    """Multi-tenant architecture service."""
    
    def __init__(self, db_path: str = "tenants.db"):
        self.db_path = db_path
        self.tenants: Dict[str, TenantConfig] = {}
        
        # Pricing configuration
        self.pricing_config = {
            "api_call_cost": 0.001,      # $0.001 per API call
            "detection_cost": 0.01,      # $0.01 per detection
            "token_cost": 0.00001,       # $0.00001 per token
            "storage_gb_cost": 0.1,      # $0.1 per GB per month
            "user_cost": 5.0,            # $5 per user per month
        }
        
        # Initialize database
        self._init_database()
        
        # Load existing tenants
        self._load_tenants()
        
        # Create default tenant if none exist
        self._create_default_tenant()
    
    def _init_database(self):
        """Initialize tenant management database."""
        with sqlite3.connect(self.db_path) as conn:
            # Tenants table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tenants (
                    tenant_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    domain TEXT,
                    subdomain TEXT UNIQUE,
                    status TEXT DEFAULT 'active',
                    subscription_tier TEXT DEFAULT 'starter',
                    billing_cycle TEXT DEFAULT 'monthly',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    logo_url TEXT,
                    primary_color TEXT DEFAULT '#1976D2',
                    secondary_color TEXT DEFAULT '#1565C0',
                    custom_css TEXT,
                    admin_email TEXT,
                    support_email TEXT,
                    billing_email TEXT,
                    features TEXT DEFAULT '{}',
                    max_users INTEGER DEFAULT 10,
                    max_api_calls_per_month INTEGER DEFAULT 10000,
                    max_storage_gb INTEGER DEFAULT 5,
                    max_custom_rules INTEGER DEFAULT 10,
                    max_webhooks INTEGER DEFAULT 5,
                    compliance_frameworks TEXT DEFAULT '[]',
                    data_retention_days INTEGER DEFAULT 365,
                    audit_logging_enabled BOOLEAN DEFAULT TRUE,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # Tenant usage tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tenant_usage (
                    usage_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    period_start TIMESTAMP NOT NULL,
                    period_end TIMESTAMP NOT NULL,
                    api_calls_total INTEGER DEFAULT 0,
                    api_calls_by_endpoint TEXT DEFAULT '{}',
                    detections_performed INTEGER DEFAULT 0,
                    tokens_processed INTEGER DEFAULT 0,
                    storage_used_gb REAL DEFAULT 0.0,
                    audit_logs_count INTEGER DEFAULT 0,
                    active_users INTEGER DEFAULT 0,
                    total_sessions INTEGER DEFAULT 0,
                    custom_rules_created INTEGER DEFAULT 0,
                    custom_rules_executed INTEGER DEFAULT 0,
                    webhooks_triggered INTEGER DEFAULT 0,
                    webhook_failures INTEGER DEFAULT 0,
                    estimated_cost_usd REAL DEFAULT 0.0,
                    claude_cost_usd REAL DEFAULT 0.0,
                    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id)
                )
            """)
            
            # Tenant databases
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tenant_databases (
                    tenant_id TEXT PRIMARY KEY,
                    database_name TEXT NOT NULL,
                    connection_string TEXT NOT NULL,
                    schema_version TEXT DEFAULT '1.0',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    isolated_schema BOOLEAN DEFAULT TRUE,
                    encryption_enabled BOOLEAN DEFAULT TRUE,
                    backup_enabled BOOLEAN DEFAULT TRUE,
                    connection_pool_size INTEGER DEFAULT 10,
                    query_timeout_seconds INTEGER DEFAULT 30,
                    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id)
                )
            """)
            
            # Tenant API keys
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tenant_api_keys (
                    key_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    api_key TEXT NOT NULL UNIQUE,
                    key_name TEXT,
                    permissions TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    last_used_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id)
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tenants_subdomain ON tenants(subdomain)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_tenant_period ON tenant_usage(tenant_id, period_start)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_tenant ON tenant_api_keys(tenant_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_key ON tenant_api_keys(api_key)")
            
            conn.commit()
    
    def _load_tenants(self):
        """Load existing tenants from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM tenants")
                
                for row in cursor.fetchall():
                    tenant = TenantConfig(
                        tenant_id=row['tenant_id'],
                        name=row['name'],
                        display_name=row['display_name'],
                        domain=row['domain'],
                        subdomain=row['subdomain'],
                        status=TenantStatus(row['status']),
                        subscription_tier=SubscriptionTier(row['subscription_tier']),
                        billing_cycle=BillingCycle(row['billing_cycle']),
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at']),
                        logo_url=row['logo_url'],
                        primary_color=row['primary_color'],
                        secondary_color=row['secondary_color'],
                        custom_css=row['custom_css'],
                        admin_email=row['admin_email'] or "",
                        support_email=row['support_email'] or "",
                        billing_email=row['billing_email'] or "",
                        features=json.loads(row['features']) if row['features'] else {},
                        max_users=row['max_users'],
                        max_api_calls_per_month=row['max_api_calls_per_month'],
                        max_storage_gb=row['max_storage_gb'],
                        max_custom_rules=row['max_custom_rules'],
                        max_webhooks=row['max_webhooks'],
                        compliance_frameworks=json.loads(row['compliance_frameworks']) if row['compliance_frameworks'] else [],
                        data_retention_days=row['data_retention_days'],
                        audit_logging_enabled=bool(row['audit_logging_enabled']),
                        metadata=json.loads(row['metadata']) if row['metadata'] else {}
                    )
                    
                    self.tenants[tenant.tenant_id] = tenant
                    
            logger.info(f"Loaded {len(self.tenants)} tenants")
            
        except Exception as e:
            logger.error(f"Error loading tenants: {e}")
    
    def _create_default_tenant(self):
        """Create default tenant if none exist."""
        if not self.tenants:
            default_tenant = TenantConfig(
                tenant_id="default",
                name="Mothership AI",
                display_name="Mothership AI - Watcher Demo",
                subdomain="demo",
                admin_email="admin@mothership-ai.com",
                support_email="support@mothership-ai.com",
                billing_email="billing@mothership-ai.com",
                subscription_tier=SubscriptionTier.ENTERPRISE,
                max_users=100,
                max_api_calls_per_month=100000,
                max_storage_gb=50,
                max_custom_rules=100,
                max_webhooks=50,
                compliance_frameworks=["soc2", "gdpr", "hipaa", "iso27001"]
            )
            
            self.create_tenant(default_tenant)
            logger.info("Created default tenant")
    
    def create_tenant(self, tenant: TenantConfig) -> bool:
        """Create a new tenant."""
        try:
            # Generate tenant ID if not provided
            if not tenant.tenant_id:
                tenant.tenant_id = f"tenant_{secrets.token_urlsafe(16)}"
            
            # Ensure subdomain is unique
            if self.get_tenant_by_subdomain(tenant.subdomain):
                tenant.subdomain = f"{tenant.subdomain}-{secrets.token_urlsafe(4)}"
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO tenants (
                        tenant_id, name, display_name, domain, subdomain, status,
                        subscription_tier, billing_cycle, created_at, updated_at,
                        logo_url, primary_color, secondary_color, custom_css,
                        admin_email, support_email, billing_email, features,
                        max_users, max_api_calls_per_month, max_storage_gb,
                        max_custom_rules, max_webhooks, compliance_frameworks,
                        data_retention_days, audit_logging_enabled, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tenant.tenant_id, tenant.name, tenant.display_name, tenant.domain,
                    tenant.subdomain, tenant.status.value, tenant.subscription_tier.value,
                    tenant.billing_cycle.value, tenant.created_at, tenant.updated_at,
                    tenant.logo_url, tenant.primary_color, tenant.secondary_color,
                    tenant.custom_css, tenant.admin_email, tenant.support_email,
                    tenant.billing_email, json.dumps(tenant.features), tenant.max_users,
                    tenant.max_api_calls_per_month, tenant.max_storage_gb,
                    tenant.max_custom_rules, tenant.max_webhooks,
                    json.dumps(tenant.compliance_frameworks), tenant.data_retention_days,
                    tenant.audit_logging_enabled, json.dumps(tenant.metadata)
                ))
                conn.commit()
            
            # Create tenant database
            self._create_tenant_database(tenant.tenant_id)
            
            # Store in memory
            self.tenants[tenant.tenant_id] = tenant
            
            logger.info(f"Created tenant: {tenant.name} ({tenant.tenant_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error creating tenant: {e}")
            return False
    
    def _create_tenant_database(self, tenant_id: str):
        """Create isolated database for tenant."""
        try:
            # For SQLite, create separate database file
            db_name = f"tenant_{tenant_id}.db"
            db_path = f"data/{db_name}"
            
            # Ensure data directory exists
            Path("data").mkdir(exist_ok=True)
            
            # Create tenant database with schema
            with sqlite3.connect(db_path) as conn:
                # Create tenant-specific tables
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS tenant_users (
                        user_id TEXT PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS tenant_detections (
                        detection_id TEXT PRIMARY KEY,
                        user_id TEXT,
                        agent_output TEXT NOT NULL,
                        ground_truth TEXT,
                        hallucination_risk REAL NOT NULL,
                        confidence REAL NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT DEFAULT '{}'
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS tenant_custom_rules (
                        rule_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        pattern TEXT,
                        enabled BOOLEAN DEFAULT TRUE,
                        created_by TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
            
            # Store database configuration
            tenant_db = TenantDatabase(
                tenant_id=tenant_id,
                database_name=db_name,
                connection_string=f"sqlite:///{db_path}"
            )
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO tenant_databases (
                        tenant_id, database_name, connection_string, schema_version,
                        created_at, isolated_schema, encryption_enabled, backup_enabled,
                        connection_pool_size, query_timeout_seconds
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tenant_db.tenant_id, tenant_db.database_name, tenant_db.connection_string,
                    tenant_db.schema_version, tenant_db.created_at, tenant_db.isolated_schema,
                    tenant_db.encryption_enabled, tenant_db.backup_enabled,
                    tenant_db.connection_pool_size, tenant_db.query_timeout_seconds
                ))
                conn.commit()
            
            logger.info(f"Created database for tenant: {tenant_id}")
            
        except Exception as e:
            logger.error(f"Error creating tenant database: {e}")
    
    def get_tenant(self, tenant_id: str) -> Optional[TenantConfig]:
        """Get tenant by ID."""
        return self.tenants.get(tenant_id)
    
    def get_tenant_by_subdomain(self, subdomain: str) -> Optional[TenantConfig]:
        """Get tenant by subdomain."""
        for tenant in self.tenants.values():
            if tenant.subdomain == subdomain:
                return tenant
        return None
    
    def get_tenant_by_domain(self, domain: str) -> Optional[TenantConfig]:
        """Get tenant by custom domain."""
        for tenant in self.tenants.values():
            if tenant.domain == domain:
                return tenant
        return None
    
    def update_tenant(self, tenant_id: str, updates: Dict[str, Any]) -> bool:
        """Update tenant configuration."""
        if tenant_id not in self.tenants:
            return False
        
        try:
            tenant = self.tenants[tenant_id]
            
            # Update fields
            for key, value in updates.items():
                if hasattr(tenant, key):
                    setattr(tenant, key, value)
            
            tenant.updated_at = datetime.utcnow()
            
            # Update database
            with sqlite3.connect(self.db_path) as conn:
                # Build dynamic update query
                set_clauses = []
                params = []
                
                for key, value in updates.items():
                    if hasattr(tenant, key):
                        set_clauses.append(f"{key} = ?")
                        if key in ['features', 'compliance_frameworks', 'metadata']:
                            params.append(json.dumps(value))
                        elif key in ['status', 'subscription_tier', 'billing_cycle']:
                            params.append(value.value if hasattr(value, 'value') else value)
                        else:
                            params.append(value)
                
                if set_clauses:
                    set_clauses.append("updated_at = ?")
                    params.append(tenant.updated_at)
                    params.append(tenant_id)
                    
                    query = f"UPDATE tenants SET {', '.join(set_clauses)} WHERE tenant_id = ?"
                    conn.execute(query, params)
                    conn.commit()
            
            logger.info(f"Updated tenant: {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating tenant: {e}")
            return False
    
    def record_usage(self, tenant_id: str, usage_data: Dict[str, Any]):
        """Record tenant usage data."""
        if tenant_id not in self.tenants:
            return
        
        try:
            # Get current month period
            now = datetime.utcnow()
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
            
            # Get or create usage record
            usage_id = f"{tenant_id}_{period_start.strftime('%Y%m')}"
            
            with sqlite3.connect(self.db_path) as conn:
                # Check if usage record exists
                cursor = conn.execute("""
                    SELECT * FROM tenant_usage WHERE usage_id = ?
                """, (usage_id,))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing record
                    conn.execute("""
                        UPDATE tenant_usage SET
                            api_calls_total = api_calls_total + ?,
                            detections_performed = detections_performed + ?,
                            tokens_processed = tokens_processed + ?,
                            claude_cost_usd = claude_cost_usd + ?
                        WHERE usage_id = ?
                    """, (
                        usage_data.get('api_calls', 0),
                        usage_data.get('detections', 0),
                        usage_data.get('tokens', 0),
                        usage_data.get('claude_cost', 0.0),
                        usage_id
                    ))
                else:
                    # Create new record
                    conn.execute("""
                        INSERT INTO tenant_usage (
                            usage_id, tenant_id, period_start, period_end,
                            api_calls_total, detections_performed, tokens_processed, claude_cost_usd
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        usage_id, tenant_id, period_start, period_end,
                        usage_data.get('api_calls', 0),
                        usage_data.get('detections', 0),
                        usage_data.get('tokens', 0),
                        usage_data.get('claude_cost', 0.0)
                    ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error recording usage for tenant {tenant_id}: {e}")
    
    def get_tenant_usage(self, tenant_id: str, months: int = 1) -> List[TenantUsage]:
        """Get tenant usage for specified months."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get usage records
                cursor = conn.execute("""
                    SELECT * FROM tenant_usage 
                    WHERE tenant_id = ? 
                    ORDER BY period_start DESC 
                    LIMIT ?
                """, (tenant_id, months))
                
                usage_records = []
                for row in cursor.fetchall():
                    usage = TenantUsage(
                        tenant_id=row['tenant_id'],
                        period_start=datetime.fromisoformat(row['period_start']),
                        period_end=datetime.fromisoformat(row['period_end']),
                        api_calls_total=row['api_calls_total'],
                        api_calls_by_endpoint=json.loads(row['api_calls_by_endpoint']) if row['api_calls_by_endpoint'] else {},
                        detections_performed=row['detections_performed'],
                        tokens_processed=row['tokens_processed'],
                        storage_used_gb=row['storage_used_gb'],
                        audit_logs_count=row['audit_logs_count'],
                        active_users=row['active_users'],
                        total_sessions=row['total_sessions'],
                        custom_rules_created=row['custom_rules_created'],
                        custom_rules_executed=row['custom_rules_executed'],
                        webhooks_triggered=row['webhooks_triggered'],
                        webhook_failures=row['webhook_failures'],
                        estimated_cost_usd=row['estimated_cost_usd'],
                        claude_cost_usd=row['claude_cost_usd']
                    )
                    
                    # Recalculate cost with current pricing
                    usage.calculate_cost(self.pricing_config)
                    usage_records.append(usage)
                
                return usage_records
                
        except Exception as e:
            logger.error(f"Error getting usage for tenant {tenant_id}: {e}")
            return []
    
    def list_tenants(self, status: TenantStatus = None) -> List[TenantConfig]:
        """List all tenants with optional status filter."""
        tenants = list(self.tenants.values())
        
        if status:
            tenants = [t for t in tenants if t.status == status]
        
        return sorted(tenants, key=lambda t: t.created_at, reverse=True)
    
    def generate_api_key(self, tenant_id: str, key_name: str = None, 
                        permissions: List[str] = None, expires_days: int = None) -> Optional[str]:
        """Generate API key for tenant."""
        if tenant_id not in self.tenants:
            return None
        
        try:
            # Generate secure API key
            api_key = f"watcher_{tenant_id}_{secrets.token_urlsafe(32)}"
            key_id = f"key_{secrets.token_urlsafe(16)}"
            
            expires_at = None
            if expires_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_days)
            
            # Store API key
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO tenant_api_keys (
                        key_id, tenant_id, api_key, key_name, permissions,
                        created_at, expires_at, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    key_id, tenant_id, api_key, key_name or "Default Key",
                    json.dumps(permissions or []), datetime.utcnow(), expires_at, True
                ))
                conn.commit()
            
            logger.info(f"Generated API key for tenant: {tenant_id}")
            return api_key
            
        except Exception as e:
            logger.error(f"Error generating API key: {e}")
            return None
    
    def validate_api_key(self, api_key: str) -> Optional[TenantConfig]:
        """Validate API key and return associated tenant."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT tenant_id FROM tenant_api_keys 
                    WHERE api_key = ? AND is_active = TRUE 
                    AND (expires_at IS NULL OR expires_at > ?)
                """, (api_key, datetime.utcnow()))
                
                row = cursor.fetchone()
                if row:
                    # Update last used timestamp
                    conn.execute("""
                        UPDATE tenant_api_keys SET last_used_at = ? WHERE api_key = ?
                    """, (datetime.utcnow(), api_key))
                    conn.commit()
                    
                    return self.get_tenant(row['tenant_id'])
            
            return None
            
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return None


# Global tenant service instance
_tenant_service: Optional[TenantService] = None

def get_tenant_service() -> TenantService:
    """Get or create tenant service instance."""
    global _tenant_service
    if _tenant_service is None:
        _tenant_service = TenantService()
    return _tenant_service
