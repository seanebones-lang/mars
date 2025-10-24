"""
Alert Escalation Service
Comprehensive alert management with multi-level escalation, on-call scheduling, and incident tracking.
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict, field
from enum import Enum
import sqlite3
import secrets
from collections import defaultdict
import uuid

from ..services.webhook_service import get_webhook_service
from ..services.auth_service import get_auth_service

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status enumeration."""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class EscalationLevel(Enum):
    """Escalation levels."""
    LEVEL_1 = "level_1"  # Primary on-call
    LEVEL_2 = "level_2"  # Supervisor
    LEVEL_3 = "level_3"  # Manager
    LEVEL_4 = "level_4"  # Executive
    LEVEL_5 = "level_5"  # Emergency contacts


class NotificationChannel(Enum):
    """Notification channels."""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    TEAMS = "teams"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"
    PHONE_CALL = "phone_call"


@dataclass
class Alert:
    """Alert definition."""
    alert_id: str
    tenant_id: str
    source_id: str  # workstation_id, agent_id, etc.
    source_type: str  # workstation, agent, system
    title: str
    description: str
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.OPEN
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    escalated_at: Optional[datetime] = None
    escalation_level: Optional[EscalationLevel] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.alert_id:
            self.alert_id = f"alert_{secrets.token_urlsafe(16)}"


@dataclass
class EscalationRule:
    """Escalation rule definition."""
    rule_id: str
    tenant_id: str
    name: str
    description: str
    enabled: bool = True
    
    # Conditions
    severity_levels: List[AlertSeverity] = field(default_factory=list)
    source_types: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    departments: List[str] = field(default_factory=list)
    
    # Escalation timing (minutes)
    level_1_timeout: int = 5    # 5 minutes
    level_2_timeout: int = 15   # 15 minutes
    level_3_timeout: int = 30   # 30 minutes
    level_4_timeout: int = 60   # 1 hour
    level_5_timeout: int = 120  # 2 hours
    
    # Notification preferences
    notification_channels: Dict[EscalationLevel, List[NotificationChannel]] = field(default_factory=dict)
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.rule_id:
            self.rule_id = f"rule_{secrets.token_urlsafe(16)}"
        
        # Default notification channels if not specified
        if not self.notification_channels:
            self.notification_channels = {
                EscalationLevel.LEVEL_1: [NotificationChannel.EMAIL, NotificationChannel.SLACK],
                EscalationLevel.LEVEL_2: [NotificationChannel.EMAIL, NotificationChannel.SMS],
                EscalationLevel.LEVEL_3: [NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.SLACK],
                EscalationLevel.LEVEL_4: [NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.PHONE_CALL],
                EscalationLevel.LEVEL_5: [NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.PHONE_CALL, NotificationChannel.PAGERDUTY]
            }


@dataclass
class OnCallSchedule:
    """On-call schedule definition."""
    schedule_id: str
    tenant_id: str
    name: str
    description: str
    enabled: bool = True
    
    # Schedule configuration
    escalation_level: EscalationLevel = EscalationLevel.LEVEL_1
    rotation_type: str = "weekly"  # daily, weekly, monthly
    rotation_start: datetime = field(default_factory=datetime.utcnow)
    
    # Team members (user_ids in rotation order)
    team_members: List[str] = field(default_factory=list)
    
    # Override schedules (specific dates/times)
    overrides: List[Dict[str, Any]] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.schedule_id:
            self.schedule_id = f"schedule_{secrets.token_urlsafe(16)}"


@dataclass
class EscalationEvent:
    """Escalation event tracking."""
    event_id: str
    alert_id: str
    escalation_level: EscalationLevel
    escalated_to: str  # user_id
    escalated_at: datetime
    notification_channels: List[NotificationChannel]
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = f"escalation_{secrets.token_urlsafe(16)}"


@dataclass
class Incident:
    """Incident tracking for major alerts."""
    incident_id: str
    tenant_id: str
    title: str
    description: str
    severity: AlertSeverity
    status: str = "open"  # open, investigating, resolved, closed
    
    # Related alerts
    alert_ids: List[str] = field(default_factory=list)
    
    # Incident management
    assigned_to: Optional[str] = None
    incident_commander: Optional[str] = None
    
    # Timeline
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    
    # Communication
    status_updates: List[Dict[str, Any]] = field(default_factory=list)
    
    # Post-mortem
    root_cause: Optional[str] = None
    resolution_summary: Optional[str] = None
    lessons_learned: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.incident_id:
            self.incident_id = f"incident_{secrets.token_urlsafe(16)}"


class AlertEscalationService:
    """
    Comprehensive alert escalation service with multi-level escalation,
    on-call scheduling, and incident management.
    """
    
    def __init__(self, db_path: str = "alert_escalation.db"):
        self.db_path = db_path
        
        # In-memory tracking
        self.active_alerts: Dict[str, Alert] = {}
        self.escalation_rules: Dict[str, EscalationRule] = {}
        self.on_call_schedules: Dict[str, OnCallSchedule] = {}
        self.escalation_timers: Dict[str, asyncio.Task] = {}
        
        # Background tasks
        self._background_tasks: Set[asyncio.Task] = set()
        self._shutdown_event = asyncio.Event()
        
        # Initialize database
        self._init_database()
        
        # Load existing data
        self._load_data()
        
        # Start background tasks
        asyncio.create_task(self._start_background_tasks())
    
    def _init_database(self):
        """Initialize alert escalation database."""
        with sqlite3.connect(self.db_path) as conn:
            # Alerts table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    alert_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    severity TEXT NOT NULL,
                    status TEXT DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    acknowledged_at TIMESTAMP,
                    acknowledged_by TEXT,
                    resolved_at TIMESTAMP,
                    resolved_by TEXT,
                    escalated_at TIMESTAMP,
                    escalation_level TEXT,
                    tags TEXT DEFAULT '[]',
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # Escalation rules table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS escalation_rules (
                    rule_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    enabled BOOLEAN DEFAULT TRUE,
                    severity_levels TEXT DEFAULT '[]',
                    source_types TEXT DEFAULT '[]',
                    tags TEXT DEFAULT '[]',
                    departments TEXT DEFAULT '[]',
                    level_1_timeout INTEGER DEFAULT 5,
                    level_2_timeout INTEGER DEFAULT 15,
                    level_3_timeout INTEGER DEFAULT 30,
                    level_4_timeout INTEGER DEFAULT 60,
                    level_5_timeout INTEGER DEFAULT 120,
                    notification_channels TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # On-call schedules table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS on_call_schedules (
                    schedule_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    enabled BOOLEAN DEFAULT TRUE,
                    escalation_level TEXT DEFAULT 'level_1',
                    rotation_type TEXT DEFAULT 'weekly',
                    rotation_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    team_members TEXT DEFAULT '[]',
                    overrides TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Escalation events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS escalation_events (
                    event_id TEXT PRIMARY KEY,
                    alert_id TEXT NOT NULL,
                    escalation_level TEXT NOT NULL,
                    escalated_to TEXT NOT NULL,
                    escalated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notification_channels TEXT DEFAULT '[]',
                    acknowledged BOOLEAN DEFAULT FALSE,
                    acknowledged_at TIMESTAMP,
                    FOREIGN KEY (alert_id) REFERENCES alerts (alert_id)
                )
            """)
            
            # Incidents table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    severity TEXT NOT NULL,
                    status TEXT DEFAULT 'open',
                    alert_ids TEXT DEFAULT '[]',
                    assigned_to TEXT,
                    incident_commander TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    status_updates TEXT DEFAULT '[]',
                    root_cause TEXT,
                    resolution_summary TEXT,
                    lessons_learned TEXT DEFAULT '[]'
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_tenant ON alerts(tenant_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_escalation_events_alert ON escalation_events(alert_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_tenant ON incidents(tenant_id)")
            
            conn.commit()
    
    def _load_data(self):
        """Load existing data from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Load active alerts
                cursor = conn.execute("""
                    SELECT * FROM alerts WHERE status IN ('open', 'acknowledged', 'in_progress', 'escalated')
                """)
                
                for row in cursor.fetchall():
                    alert = Alert(
                        alert_id=row['alert_id'],
                        tenant_id=row['tenant_id'],
                        source_id=row['source_id'],
                        source_type=row['source_type'],
                        title=row['title'],
                        description=row['description'],
                        severity=AlertSeverity(row['severity']),
                        status=AlertStatus(row['status']),
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at']),
                        acknowledged_at=datetime.fromisoformat(row['acknowledged_at']) if row['acknowledged_at'] else None,
                        acknowledged_by=row['acknowledged_by'],
                        resolved_at=datetime.fromisoformat(row['resolved_at']) if row['resolved_at'] else None,
                        resolved_by=row['resolved_by'],
                        escalated_at=datetime.fromisoformat(row['escalated_at']) if row['escalated_at'] else None,
                        escalation_level=EscalationLevel(row['escalation_level']) if row['escalation_level'] else None,
                        tags=json.loads(row['tags']) if row['tags'] else [],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {}
                    )
                    self.active_alerts[alert.alert_id] = alert
                
                # Load escalation rules
                cursor = conn.execute("SELECT * FROM escalation_rules WHERE enabled = TRUE")
                
                for row in cursor.fetchall():
                    rule = EscalationRule(
                        rule_id=row['rule_id'],
                        tenant_id=row['tenant_id'],
                        name=row['name'],
                        description=row['description'],
                        enabled=bool(row['enabled']),
                        severity_levels=[AlertSeverity(s) for s in json.loads(row['severity_levels'])],
                        source_types=json.loads(row['source_types']),
                        tags=json.loads(row['tags']),
                        departments=json.loads(row['departments']),
                        level_1_timeout=row['level_1_timeout'],
                        level_2_timeout=row['level_2_timeout'],
                        level_3_timeout=row['level_3_timeout'],
                        level_4_timeout=row['level_4_timeout'],
                        level_5_timeout=row['level_5_timeout'],
                        notification_channels={
                            EscalationLevel(k): [NotificationChannel(c) for c in v]
                            for k, v in json.loads(row['notification_channels']).items()
                        } if row['notification_channels'] else {},
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at'])
                    )
                    self.escalation_rules[rule.rule_id] = rule
                
                # Load on-call schedules
                cursor = conn.execute("SELECT * FROM on_call_schedules WHERE enabled = TRUE")
                
                for row in cursor.fetchall():
                    schedule = OnCallSchedule(
                        schedule_id=row['schedule_id'],
                        tenant_id=row['tenant_id'],
                        name=row['name'],
                        description=row['description'],
                        enabled=bool(row['enabled']),
                        escalation_level=EscalationLevel(row['escalation_level']),
                        rotation_type=row['rotation_type'],
                        rotation_start=datetime.fromisoformat(row['rotation_start']),
                        team_members=json.loads(row['team_members']),
                        overrides=json.loads(row['overrides']),
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at'])
                    )
                    self.on_call_schedules[schedule.schedule_id] = schedule
                
            logger.info(f"Loaded {len(self.active_alerts)} active alerts, {len(self.escalation_rules)} rules, {len(self.on_call_schedules)} schedules")
            
        except Exception as e:
            logger.error(f"Error loading escalation data: {e}")
    
    async def _start_background_tasks(self):
        """Start background maintenance tasks."""
        tasks = [
            self._escalation_monitor(),
            self._alert_cleanup(),
            self._schedule_rotation_monitor()
        ]
        
        for task_coro in tasks:
            task = asyncio.create_task(task_coro)
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
    
    async def create_alert(self, alert: Alert) -> str:
        """Create a new alert and start escalation monitoring."""
        try:
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO alerts (
                        alert_id, tenant_id, source_id, source_type, title, description,
                        severity, status, created_at, updated_at, tags, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.alert_id, alert.tenant_id, alert.source_id, alert.source_type,
                    alert.title, alert.description, alert.severity.value, alert.status.value,
                    alert.created_at, alert.updated_at, json.dumps(alert.tags),
                    json.dumps(alert.metadata)
                ))
                conn.commit()
            
            # Store in memory
            self.active_alerts[alert.alert_id] = alert
            
            # Start escalation monitoring
            await self._start_escalation_monitoring(alert)
            
            # Send initial notifications
            await self._send_initial_notifications(alert)
            
            logger.info(f"Created alert: {alert.alert_id} ({alert.severity.value})")
            return alert.alert_id
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            raise
    
    async def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """Acknowledge an alert and stop escalation."""
        if alert_id not in self.active_alerts:
            return False
        
        try:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = user_id
            alert.updated_at = datetime.utcnow()
            
            # Update database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE alerts SET 
                        status = ?, acknowledged_at = ?, acknowledged_by = ?, updated_at = ?
                    WHERE alert_id = ?
                """, (
                    alert.status.value, alert.acknowledged_at, alert.acknowledged_by,
                    alert.updated_at, alert_id
                ))
                conn.commit()
            
            # Stop escalation timer
            if alert_id in self.escalation_timers:
                self.escalation_timers[alert_id].cancel()
                del self.escalation_timers[alert_id]
            
            # Send acknowledgment notifications
            await self._send_acknowledgment_notifications(alert, user_id)
            
            logger.info(f"Alert acknowledged: {alert_id} by {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}")
            return False
    
    async def resolve_alert(self, alert_id: str, user_id: str, resolution_notes: str = None) -> bool:
        """Resolve an alert."""
        if alert_id not in self.active_alerts:
            return False
        
        try:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by = user_id
            alert.updated_at = datetime.utcnow()
            
            if resolution_notes:
                alert.metadata['resolution_notes'] = resolution_notes
            
            # Update database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE alerts SET 
                        status = ?, resolved_at = ?, resolved_by = ?, updated_at = ?, metadata = ?
                    WHERE alert_id = ?
                """, (
                    alert.status.value, alert.resolved_at, alert.resolved_by,
                    alert.updated_at, json.dumps(alert.metadata), alert_id
                ))
                conn.commit()
            
            # Stop escalation timer
            if alert_id in self.escalation_timers:
                self.escalation_timers[alert_id].cancel()
                del self.escalation_timers[alert_id]
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            
            # Send resolution notifications
            await self._send_resolution_notifications(alert, user_id, resolution_notes)
            
            logger.info(f"Alert resolved: {alert_id} by {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            return False
    
    async def _start_escalation_monitoring(self, alert: Alert):
        """Start escalation monitoring for an alert."""
        # Find applicable escalation rules
        applicable_rules = self._find_applicable_rules(alert)
        
        if not applicable_rules:
            logger.warning(f"No escalation rules found for alert: {alert.alert_id}")
            return
        
        # Use the first applicable rule (could be enhanced to use priority)
        rule = applicable_rules[0]
        
        # Start escalation timer for Level 1
        timeout = rule.level_1_timeout * 60  # Convert to seconds
        task = asyncio.create_task(self._escalation_timer(alert, rule, EscalationLevel.LEVEL_1, timeout))
        self.escalation_timers[alert.alert_id] = task
    
    def _find_applicable_rules(self, alert: Alert) -> List[EscalationRule]:
        """Find escalation rules applicable to an alert."""
        applicable_rules = []
        
        for rule in self.escalation_rules.values():
            if rule.tenant_id != alert.tenant_id or not rule.enabled:
                continue
            
            # Check severity
            if rule.severity_levels and alert.severity not in rule.severity_levels:
                continue
            
            # Check source type
            if rule.source_types and alert.source_type not in rule.source_types:
                continue
            
            # Check tags
            if rule.tags and not any(tag in alert.tags for tag in rule.tags):
                continue
            
            applicable_rules.append(rule)
        
        return applicable_rules
    
    async def _escalation_timer(self, alert: Alert, rule: EscalationRule, level: EscalationLevel, timeout: int):
        """Escalation timer for a specific level."""
        try:
            await asyncio.sleep(timeout)
            
            # Check if alert is still active and not acknowledged
            if (alert.alert_id in self.active_alerts and 
                self.active_alerts[alert.alert_id].status == AlertStatus.OPEN):
                
                await self._escalate_alert(alert, rule, level)
                
        except asyncio.CancelledError:
            logger.debug(f"Escalation timer cancelled for alert: {alert.alert_id}")
        except Exception as e:
            logger.error(f"Error in escalation timer: {e}")
    
    async def _escalate_alert(self, alert: Alert, rule: EscalationRule, level: EscalationLevel):
        """Escalate an alert to the next level."""
        try:
            # Update alert
            alert.status = AlertStatus.ESCALATED
            alert.escalated_at = datetime.utcnow()
            alert.escalation_level = level
            alert.updated_at = datetime.utcnow()
            
            # Update database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE alerts SET 
                        status = ?, escalated_at = ?, escalation_level = ?, updated_at = ?
                    WHERE alert_id = ?
                """, (
                    alert.status.value, alert.escalated_at, alert.escalation_level.value,
                    alert.updated_at, alert.alert_id
                ))
                conn.commit()
            
            # Find on-call person for this level
            on_call_user = await self._get_on_call_user(alert.tenant_id, level)
            
            if on_call_user:
                # Create escalation event
                escalation_event = EscalationEvent(
                    event_id="",
                    alert_id=alert.alert_id,
                    escalation_level=level,
                    escalated_to=on_call_user,
                    escalated_at=datetime.utcnow(),
                    notification_channels=rule.notification_channels.get(level, [])
                )
                
                # Store escalation event
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT INTO escalation_events (
                            event_id, alert_id, escalation_level, escalated_to,
                            escalated_at, notification_channels
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        escalation_event.event_id, escalation_event.alert_id,
                        escalation_event.escalation_level.value, escalation_event.escalated_to,
                        escalation_event.escalated_at, json.dumps([c.value for c in escalation_event.notification_channels])
                    ))
                    conn.commit()
                
                # Send escalation notifications
                await self._send_escalation_notifications(alert, escalation_event, rule)
                
                # Schedule next escalation level
                await self._schedule_next_escalation(alert, rule, level)
            
            logger.warning(f"Alert escalated to {level.value}: {alert.alert_id}")
            
        except Exception as e:
            logger.error(f"Error escalating alert: {e}")
    
    async def _get_on_call_user(self, tenant_id: str, level: EscalationLevel) -> Optional[str]:
        """Get the current on-call user for a specific escalation level."""
        # Find schedule for this level
        for schedule in self.on_call_schedules.values():
            if (schedule.tenant_id == tenant_id and 
                schedule.escalation_level == level and 
                schedule.enabled and 
                schedule.team_members):
                
                # Calculate current on-call person based on rotation
                return self._calculate_current_on_call(schedule)
        
        return None
    
    def _calculate_current_on_call(self, schedule: OnCallSchedule) -> Optional[str]:
        """Calculate who is currently on-call based on rotation schedule."""
        if not schedule.team_members:
            return None
        
        now = datetime.utcnow()
        rotation_start = schedule.rotation_start
        
        # Calculate rotation period
        if schedule.rotation_type == "daily":
            days_since_start = (now - rotation_start).days
            rotation_index = days_since_start % len(schedule.team_members)
        elif schedule.rotation_type == "weekly":
            weeks_since_start = (now - rotation_start).days // 7
            rotation_index = weeks_since_start % len(schedule.team_members)
        elif schedule.rotation_type == "monthly":
            months_since_start = ((now.year - rotation_start.year) * 12 + 
                                 (now.month - rotation_start.month))
            rotation_index = months_since_start % len(schedule.team_members)
        else:
            rotation_index = 0
        
        # Check for overrides
        for override in schedule.overrides:
            override_start = datetime.fromisoformat(override['start'])
            override_end = datetime.fromisoformat(override['end'])
            
            if override_start <= now <= override_end:
                return override['user_id']
        
        return schedule.team_members[rotation_index]
    
    async def _schedule_next_escalation(self, alert: Alert, rule: EscalationRule, current_level: EscalationLevel):
        """Schedule the next escalation level."""
        next_level = None
        timeout = 0
        
        if current_level == EscalationLevel.LEVEL_1:
            next_level = EscalationLevel.LEVEL_2
            timeout = rule.level_2_timeout * 60
        elif current_level == EscalationLevel.LEVEL_2:
            next_level = EscalationLevel.LEVEL_3
            timeout = rule.level_3_timeout * 60
        elif current_level == EscalationLevel.LEVEL_3:
            next_level = EscalationLevel.LEVEL_4
            timeout = rule.level_4_timeout * 60
        elif current_level == EscalationLevel.LEVEL_4:
            next_level = EscalationLevel.LEVEL_5
            timeout = rule.level_5_timeout * 60
        
        if next_level and timeout > 0:
            # Cancel existing timer
            if alert.alert_id in self.escalation_timers:
                self.escalation_timers[alert.alert_id].cancel()
            
            # Start new timer
            task = asyncio.create_task(self._escalation_timer(alert, rule, next_level, timeout))
            self.escalation_timers[alert.alert_id] = task
    
    async def _send_initial_notifications(self, alert: Alert):
        """Send initial alert notifications."""
        # Implementation would integrate with webhook service
        webhook_service = get_webhook_service()
        
        notification_data = {
            "alert_id": alert.alert_id,
            "title": alert.title,
            "description": alert.description,
            "severity": alert.severity.value,
            "source": f"{alert.source_type}:{alert.source_id}",
            "created_at": alert.created_at.isoformat(),
            "type": "alert_created"
        }
        
        # Send to configured channels
        await webhook_service.send_notification("alert_created", notification_data, alert.tenant_id)
    
    async def _send_escalation_notifications(self, alert: Alert, escalation_event: EscalationEvent, rule: EscalationRule):
        """Send escalation notifications."""
        webhook_service = get_webhook_service()
        
        notification_data = {
            "alert_id": alert.alert_id,
            "title": alert.title,
            "description": alert.description,
            "severity": alert.severity.value,
            "escalation_level": escalation_event.escalation_level.value,
            "escalated_to": escalation_event.escalated_to,
            "escalated_at": escalation_event.escalated_at.isoformat(),
            "type": "alert_escalated"
        }
        
        # Send to configured channels
        await webhook_service.send_notification("alert_escalated", notification_data, alert.tenant_id)
    
    async def _send_acknowledgment_notifications(self, alert: Alert, user_id: str):
        """Send acknowledgment notifications."""
        webhook_service = get_webhook_service()
        
        notification_data = {
            "alert_id": alert.alert_id,
            "title": alert.title,
            "acknowledged_by": user_id,
            "acknowledged_at": alert.acknowledged_at.isoformat(),
            "type": "alert_acknowledged"
        }
        
        await webhook_service.send_notification("alert_acknowledged", notification_data, alert.tenant_id)
    
    async def _send_resolution_notifications(self, alert: Alert, user_id: str, resolution_notes: str = None):
        """Send resolution notifications."""
        webhook_service = get_webhook_service()
        
        notification_data = {
            "alert_id": alert.alert_id,
            "title": alert.title,
            "resolved_by": user_id,
            "resolved_at": alert.resolved_at.isoformat(),
            "resolution_notes": resolution_notes,
            "type": "alert_resolved"
        }
        
        await webhook_service.send_notification("alert_resolved", notification_data, alert.tenant_id)
    
    async def _escalation_monitor(self):
        """Monitor escalation timers and handle timeouts."""
        while not self._shutdown_event.is_set():
            try:
                # Check for any escalation issues
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in escalation monitor: {e}")
                await asyncio.sleep(60)
    
    async def _alert_cleanup(self):
        """Clean up old resolved alerts."""
        while not self._shutdown_event.is_set():
            try:
                # Clean up alerts older than 30 days
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        DELETE FROM alerts 
                        WHERE status IN ('resolved', 'closed') AND updated_at < ?
                    """, (cutoff_date,))
                    
                    if cursor.rowcount > 0:
                        logger.info(f"Cleaned up {cursor.rowcount} old alerts")
                    
                    conn.commit()
                
                await asyncio.sleep(86400)  # Check daily
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert cleanup: {e}")
                await asyncio.sleep(3600)
    
    async def _schedule_rotation_monitor(self):
        """Monitor on-call schedule rotations."""
        while not self._shutdown_event.is_set():
            try:
                # Check for schedule rotations
                await asyncio.sleep(3600)  # Check hourly
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in schedule rotation monitor: {e}")
                await asyncio.sleep(3600)
    
    async def create_escalation_rule(self, rule: EscalationRule) -> str:
        """Create a new escalation rule."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO escalation_rules (
                        rule_id, tenant_id, name, description, enabled,
                        severity_levels, source_types, tags, departments,
                        level_1_timeout, level_2_timeout, level_3_timeout,
                        level_4_timeout, level_5_timeout, notification_channels,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rule.rule_id, rule.tenant_id, rule.name, rule.description, rule.enabled,
                    json.dumps([s.value for s in rule.severity_levels]),
                    json.dumps(rule.source_types), json.dumps(rule.tags), json.dumps(rule.departments),
                    rule.level_1_timeout, rule.level_2_timeout, rule.level_3_timeout,
                    rule.level_4_timeout, rule.level_5_timeout,
                    json.dumps({k.value: [c.value for c in v] for k, v in rule.notification_channels.items()}),
                    rule.created_at, rule.updated_at
                ))
                conn.commit()
            
            self.escalation_rules[rule.rule_id] = rule
            logger.info(f"Created escalation rule: {rule.name}")
            return rule.rule_id
            
        except Exception as e:
            logger.error(f"Error creating escalation rule: {e}")
            raise
    
    async def create_on_call_schedule(self, schedule: OnCallSchedule) -> str:
        """Create a new on-call schedule."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO on_call_schedules (
                        schedule_id, tenant_id, name, description, enabled,
                        escalation_level, rotation_type, rotation_start,
                        team_members, overrides, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    schedule.schedule_id, schedule.tenant_id, schedule.name, schedule.description,
                    schedule.enabled, schedule.escalation_level.value, schedule.rotation_type,
                    schedule.rotation_start, json.dumps(schedule.team_members),
                    json.dumps(schedule.overrides), schedule.created_at, schedule.updated_at
                ))
                conn.commit()
            
            self.on_call_schedules[schedule.schedule_id] = schedule
            logger.info(f"Created on-call schedule: {schedule.name}")
            return schedule.schedule_id
            
        except Exception as e:
            logger.error(f"Error creating on-call schedule: {e}")
            raise
    
    async def get_alert_statistics(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """Get alert statistics for a tenant."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Total alerts
                cursor = conn.execute("""
                    SELECT COUNT(*) as total FROM alerts 
                    WHERE tenant_id = ? AND created_at >= ?
                """, (tenant_id, start_date))
                total_alerts = cursor.fetchone()['total']
                
                # Alerts by severity
                cursor = conn.execute("""
                    SELECT severity, COUNT(*) as count FROM alerts 
                    WHERE tenant_id = ? AND created_at >= ?
                    GROUP BY severity
                """, (tenant_id, start_date))
                alerts_by_severity = {row['severity']: row['count'] for row in cursor.fetchall()}
                
                # Alerts by status
                cursor = conn.execute("""
                    SELECT status, COUNT(*) as count FROM alerts 
                    WHERE tenant_id = ? AND created_at >= ?
                    GROUP BY status
                """, (tenant_id, start_date))
                alerts_by_status = {row['status']: row['count'] for row in cursor.fetchall()}
                
                # Escalation statistics
                cursor = conn.execute("""
                    SELECT escalation_level, COUNT(*) as count FROM escalation_events e
                    JOIN alerts a ON e.alert_id = a.alert_id
                    WHERE a.tenant_id = ? AND e.escalated_at >= ?
                    GROUP BY escalation_level
                """, (tenant_id, start_date))
                escalations_by_level = {row['escalation_level']: row['count'] for row in cursor.fetchall()}
                
                # Average resolution time
                cursor = conn.execute("""
                    SELECT AVG(
                        (julianday(resolved_at) - julianday(created_at)) * 24 * 60
                    ) as avg_resolution_minutes
                    FROM alerts 
                    WHERE tenant_id = ? AND status = 'resolved' AND created_at >= ?
                """, (tenant_id, start_date))
                avg_resolution = cursor.fetchone()['avg_resolution_minutes'] or 0
                
                return {
                    "total_alerts": total_alerts,
                    "alerts_by_severity": alerts_by_severity,
                    "alerts_by_status": alerts_by_status,
                    "escalations_by_level": escalations_by_level,
                    "avg_resolution_minutes": round(avg_resolution, 2),
                    "period_days": days
                }
                
        except Exception as e:
            logger.error(f"Error getting alert statistics: {e}")
            return {}
    
    async def shutdown(self):
        """Gracefully shutdown the escalation service."""
        logger.info("Shutting down alert escalation service...")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel all escalation timers
        for task in self.escalation_timers.values():
            task.cancel()
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        logger.info("Alert escalation service shutdown complete")


# Global escalation service instance
_escalation_service: Optional[AlertEscalationService] = None

def get_escalation_service() -> AlertEscalationService:
    """Get or create escalation service instance."""
    global _escalation_service
    if _escalation_service is None:
        _escalation_service = AlertEscalationService()
    return _escalation_service
