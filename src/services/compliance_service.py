"""
Enterprise Compliance and Audit Trail Service
Implements comprehensive logging, audit trails, and regulatory compliance features.
"""

import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import asyncio
from pathlib import Path
import csv
import zipfile
from cryptography.fernet import Fernet
import secrets

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    DATA_ACCESS = "data_access"
    DATA_EXPORT = "data_export"
    DATA_DELETION = "data_deletion"
    DETECTION_PERFORMED = "detection_performed"
    RULE_CREATED = "rule_created"
    RULE_UPDATED = "rule_updated"
    RULE_DELETED = "rule_deleted"
    WEBHOOK_TRIGGERED = "webhook_triggered"
    BATCH_PROCESSED = "batch_processed"
    CONFIG_CHANGED = "config_changed"
    SECURITY_VIOLATION = "security_violation"
    COMPLIANCE_VIOLATION = "compliance_violation"
    SYSTEM_ERROR = "system_error"


class ComplianceFramework(Enum):
    """Supported compliance frameworks."""
    SOC2 = "soc2"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    ISO27001 = "iso27001"
    PCI_DSS = "pci_dss"
    CCPA = "ccpa"
    NIST = "nist"


class DataClassification(Enum):
    """Data classification levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"


class RetentionPolicy(Enum):
    """Data retention policies."""
    DAYS_30 = 30
    DAYS_90 = 90
    DAYS_180 = 180
    DAYS_365 = 365
    DAYS_2555 = 2555  # 7 years
    PERMANENT = -1


@dataclass
class AuditEvent:
    """Audit event record."""
    event_id: str
    event_type: AuditEventType
    user_id: Optional[str]
    session_id: Optional[str]
    timestamp: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    resource: Optional[str]
    action: str
    outcome: str  # success, failure, error
    details: Dict[str, Any]
    risk_level: str = "low"  # low, medium, high, critical
    compliance_frameworks: List[ComplianceFramework] = None
    data_classification: DataClassification = DataClassification.INTERNAL
    retention_policy: RetentionPolicy = RetentionPolicy.DAYS_2555
    hash_signature: Optional[str] = None
    
    def __post_init__(self):
        if self.compliance_frameworks is None:
            self.compliance_frameworks = []
        if not self.hash_signature:
            self.hash_signature = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """Generate cryptographic hash for tamper detection."""
        content = f"{self.event_id}{self.timestamp}{self.user_id}{self.action}{self.outcome}"
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class ComplianceRule:
    """Compliance rule definition."""
    rule_id: str
    name: str
    framework: ComplianceFramework
    description: str
    requirement: str
    control_id: str
    automated_check: bool
    severity: str  # low, medium, high, critical
    remediation: str
    enabled: bool = True
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ComplianceViolation:
    """Compliance violation record."""
    violation_id: str
    rule_id: str
    event_id: str
    timestamp: datetime
    severity: str
    description: str
    remediation_required: bool
    remediation_steps: List[str]
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    
    def __post_init__(self):
        if self.remediation_steps is None:
            self.remediation_steps = []


@dataclass
class DataProcessingRecord:
    """GDPR data processing record."""
    record_id: str
    data_subject_id: str
    processing_purpose: str
    legal_basis: str
    data_categories: List[str]
    recipients: List[str]
    retention_period: int
    cross_border_transfer: bool
    consent_given: bool
    consent_timestamp: Optional[datetime]
    processing_start: datetime
    processing_end: Optional[datetime] = None
    
    def __post_init__(self):
        if self.data_categories is None:
            self.data_categories = []
        if self.recipients is None:
            self.recipients = []


class ComplianceService:
    """Enterprise compliance and audit trail service."""
    
    def __init__(self, db_path: str = "compliance.db", encryption_key: bytes = None):
        self.db_path = db_path
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Compliance rules
        self.compliance_rules: Dict[str, ComplianceRule] = {}
        
        # Initialize database
        self._init_database()
        
        # Load compliance rules
        self._init_compliance_rules()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _init_database(self):
        """Initialize compliance database."""
        with sqlite3.connect(self.db_path) as conn:
            # Audit events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    user_id TEXT,
                    session_id TEXT,
                    timestamp TIMESTAMP NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    resource TEXT,
                    action TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    details TEXT,
                    risk_level TEXT DEFAULT 'low',
                    compliance_frameworks TEXT,
                    data_classification TEXT DEFAULT 'internal',
                    retention_policy INTEGER DEFAULT 2555,
                    hash_signature TEXT NOT NULL,
                    encrypted_data TEXT
                )
            """)
            
            # Compliance violations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS compliance_violations (
                    violation_id TEXT PRIMARY KEY,
                    rule_id TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT NOT NULL,
                    remediation_required BOOLEAN DEFAULT TRUE,
                    remediation_steps TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TIMESTAMP,
                    resolved_by TEXT
                )
            """)
            
            # Data processing records (GDPR)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS data_processing_records (
                    record_id TEXT PRIMARY KEY,
                    data_subject_id TEXT NOT NULL,
                    processing_purpose TEXT NOT NULL,
                    legal_basis TEXT NOT NULL,
                    data_categories TEXT,
                    recipients TEXT,
                    retention_period INTEGER,
                    cross_border_transfer BOOLEAN DEFAULT FALSE,
                    consent_given BOOLEAN DEFAULT FALSE,
                    consent_timestamp TIMESTAMP,
                    processing_start TIMESTAMP NOT NULL,
                    processing_end TIMESTAMP
                )
            """)
            
            # Compliance rules table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS compliance_rules (
                    rule_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    framework TEXT NOT NULL,
                    description TEXT,
                    requirement TEXT,
                    control_id TEXT,
                    automated_check BOOLEAN DEFAULT FALSE,
                    severity TEXT DEFAULT 'medium',
                    remediation TEXT,
                    enabled BOOLEAN DEFAULT TRUE,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            # Data retention tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS retention_tracking (
                    record_id TEXT PRIMARY KEY,
                    table_name TEXT NOT NULL,
                    record_key TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    retention_days INTEGER NOT NULL,
                    deletion_scheduled TIMESTAMP,
                    deleted BOOLEAN DEFAULT FALSE,
                    deleted_at TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_events(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_events(event_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_violations_timestamp ON compliance_violations(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_violations_severity ON compliance_violations(severity)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_data_processing_subject ON data_processing_records(data_subject_id)")
            
            conn.commit()
    
    def _init_compliance_rules(self):
        """Initialize default compliance rules."""
        default_rules = [
            # SOC 2 Rules
            ComplianceRule(
                rule_id="soc2_access_control",
                name="Access Control Monitoring",
                framework=ComplianceFramework.SOC2,
                description="Monitor and log all access to sensitive data",
                requirement="CC6.1 - Logical and Physical Access Controls",
                control_id="CC6.1",
                automated_check=True,
                severity="high",
                remediation="Review access logs and ensure proper authorization"
            ),
            
            # GDPR Rules
            ComplianceRule(
                rule_id="gdpr_data_processing_log",
                name="Data Processing Logging",
                framework=ComplianceFramework.GDPR,
                description="Log all personal data processing activities",
                requirement="Article 30 - Records of processing activities",
                control_id="Art30",
                automated_check=True,
                severity="critical",
                remediation="Ensure all data processing is logged with legal basis"
            ),
            
            ComplianceRule(
                rule_id="gdpr_consent_tracking",
                name="Consent Tracking",
                framework=ComplianceFramework.GDPR,
                description="Track and validate user consent for data processing",
                requirement="Article 7 - Conditions for consent",
                control_id="Art7",
                automated_check=True,
                severity="critical",
                remediation="Obtain and document valid consent before processing"
            ),
            
            # HIPAA Rules
            ComplianceRule(
                rule_id="hipaa_access_logging",
                name="PHI Access Logging",
                framework=ComplianceFramework.HIPAA,
                description="Log all access to protected health information",
                requirement="164.312(b) - Audit controls",
                control_id="164.312(b)",
                automated_check=True,
                severity="critical",
                remediation="Implement comprehensive audit logging for PHI access"
            ),
            
            # ISO 27001 Rules
            ComplianceRule(
                rule_id="iso27001_security_events",
                name="Security Event Logging",
                framework=ComplianceFramework.ISO27001,
                description="Log and monitor security events",
                requirement="A.12.4.1 - Event logging",
                control_id="A.12.4.1",
                automated_check=True,
                severity="high",
                remediation="Ensure all security events are logged and monitored"
            )
        ]
        
        # Store rules in database
        with sqlite3.connect(self.db_path) as conn:
            for rule in default_rules:
                conn.execute("""
                    INSERT OR REPLACE INTO compliance_rules (
                        rule_id, name, framework, description, requirement,
                        control_id, automated_check, severity, remediation, enabled, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rule.rule_id, rule.name, rule.framework.value, rule.description,
                    rule.requirement, rule.control_id, rule.automated_check,
                    rule.severity, rule.remediation, rule.enabled, json.dumps(rule.metadata)
                ))
                
                self.compliance_rules[rule.rule_id] = rule
            
            conn.commit()
    
    def _start_background_tasks(self):
        """Start background compliance tasks."""
        # In a real implementation, this would start async tasks for:
        # - Data retention cleanup
        # - Compliance monitoring
        # - Automated reporting
        pass
    
    async def log_audit_event(self, event: AuditEvent) -> str:
        """Log an audit event with compliance checking."""
        try:
            # Encrypt sensitive details
            encrypted_details = self.cipher.encrypt(json.dumps(event.details).encode())
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO audit_events (
                        event_id, event_type, user_id, session_id, timestamp,
                        ip_address, user_agent, resource, action, outcome,
                        details, risk_level, compliance_frameworks, data_classification,
                        retention_policy, hash_signature, encrypted_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id, event.event_type.value, event.user_id, event.session_id,
                    event.timestamp, event.ip_address, event.user_agent, event.resource,
                    event.action, event.outcome, json.dumps(event.details), event.risk_level,
                    json.dumps([f.value for f in event.compliance_frameworks]),
                    event.data_classification.value, event.retention_policy.value,
                    event.hash_signature, encrypted_details.decode()
                ))
                conn.commit()
            
            # Schedule retention tracking
            await self._schedule_retention(event.event_id, "audit_events", event.retention_policy)
            
            # Check for compliance violations
            await self._check_compliance_violations(event)
            
            logger.info(f"Audit event logged: {event.event_id}")
            return event.event_id
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            raise
    
    async def _schedule_retention(self, record_id: str, table_name: str, retention_policy: RetentionPolicy):
        """Schedule data retention cleanup."""
        if retention_policy == RetentionPolicy.PERMANENT:
            return
        
        deletion_date = datetime.utcnow() + timedelta(days=retention_policy.value)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO retention_tracking (
                    record_id, table_name, record_key, created_at,
                    retention_days, deletion_scheduled
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                f"{table_name}_{record_id}", table_name, record_id,
                datetime.utcnow(), retention_policy.value, deletion_date
            ))
            conn.commit()
    
    async def _check_compliance_violations(self, event: AuditEvent):
        """Check event against compliance rules."""
        for rule in self.compliance_rules.values():
            if not rule.enabled or not rule.automated_check:
                continue
            
            violation = await self._evaluate_compliance_rule(rule, event)
            if violation:
                await self._record_compliance_violation(violation)
    
    async def _evaluate_compliance_rule(self, rule: ComplianceRule, event: AuditEvent) -> Optional[ComplianceViolation]:
        """Evaluate a specific compliance rule against an event."""
        # Example rule evaluations
        
        if rule.rule_id == "soc2_access_control":
            if event.event_type == AuditEventType.DATA_ACCESS and event.outcome == "failure":
                return ComplianceViolation(
                    violation_id=f"viol_{secrets.token_urlsafe(16)}",
                    rule_id=rule.rule_id,
                    event_id=event.event_id,
                    timestamp=datetime.utcnow(),
                    severity=rule.severity,
                    description="Failed data access attempt detected",
                    remediation_required=True,
                    remediation_steps=[
                        "Investigate failed access attempt",
                        "Verify user authorization",
                        "Check for security breach indicators"
                    ]
                )
        
        elif rule.rule_id == "gdpr_data_processing_log":
            if event.event_type == AuditEventType.DETECTION_PERFORMED:
                # Check if personal data processing is properly logged
                if not event.details.get("gdpr_legal_basis"):
                    return ComplianceViolation(
                        violation_id=f"viol_{secrets.token_urlsafe(16)}",
                        rule_id=rule.rule_id,
                        event_id=event.event_id,
                        timestamp=datetime.utcnow(),
                        severity=rule.severity,
                        description="Data processing without documented legal basis",
                        remediation_required=True,
                        remediation_steps=[
                            "Document legal basis for data processing",
                            "Update data processing records",
                            "Ensure GDPR compliance"
                        ]
                    )
        
        return None
    
    async def _record_compliance_violation(self, violation: ComplianceViolation):
        """Record a compliance violation."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO compliance_violations (
                    violation_id, rule_id, event_id, timestamp, severity,
                    description, remediation_required, remediation_steps,
                    resolved, resolved_at, resolved_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                violation.violation_id, violation.rule_id, violation.event_id,
                violation.timestamp, violation.severity, violation.description,
                violation.remediation_required, json.dumps(violation.remediation_steps),
                violation.resolved, violation.resolved_at, violation.resolved_by
            ))
            conn.commit()
        
        logger.warning(f"Compliance violation recorded: {violation.violation_id}")
    
    async def record_data_processing(self, record: DataProcessingRecord):
        """Record GDPR data processing activity."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO data_processing_records (
                    record_id, data_subject_id, processing_purpose, legal_basis,
                    data_categories, recipients, retention_period, cross_border_transfer,
                    consent_given, consent_timestamp, processing_start, processing_end
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.record_id, record.data_subject_id, record.processing_purpose,
                record.legal_basis, json.dumps(record.data_categories),
                json.dumps(record.recipients), record.retention_period,
                record.cross_border_transfer, record.consent_given,
                record.consent_timestamp, record.processing_start, record.processing_end
            ))
            conn.commit()
    
    async def get_audit_trail(self, start_date: datetime = None, end_date: datetime = None,
                            user_id: str = None, event_types: List[AuditEventType] = None,
                            limit: int = 1000) -> List[Dict[str, Any]]:
        """Retrieve audit trail with filtering."""
        query = "SELECT * FROM audit_events WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if event_types:
            placeholders = ",".join("?" * len(event_types))
            query += f" AND event_type IN ({placeholders})"
            params.extend([et.value for et in event_types])
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                # Decrypt sensitive data
                try:
                    encrypted_data = row['encrypted_data'].encode()
                    decrypted_details = json.loads(self.cipher.decrypt(encrypted_data).decode())
                except:
                    decrypted_details = json.loads(row['details']) if row['details'] else {}
                
                results.append({
                    "event_id": row['event_id'],
                    "event_type": row['event_type'],
                    "user_id": row['user_id'],
                    "timestamp": row['timestamp'],
                    "ip_address": row['ip_address'],
                    "action": row['action'],
                    "outcome": row['outcome'],
                    "details": decrypted_details,
                    "risk_level": row['risk_level'],
                    "hash_signature": row['hash_signature']
                })
            
            return results
    
    async def generate_compliance_report(self, framework: ComplianceFramework,
                                       start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate compliance report for specific framework."""
        
        # Get relevant audit events
        events = await self.get_audit_trail(start_date, end_date)
        
        # Get compliance violations
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT cv.*, cr.framework 
                FROM compliance_violations cv
                JOIN compliance_rules cr ON cv.rule_id = cr.rule_id
                WHERE cr.framework = ? AND cv.timestamp BETWEEN ? AND ?
            """, (framework.value, start_date, end_date))
            
            violations = [dict(row) for row in cursor.fetchall()]
        
        # Calculate metrics
        total_events = len(events)
        total_violations = len(violations)
        critical_violations = len([v for v in violations if v['severity'] == 'critical'])
        resolved_violations = len([v for v in violations if v['resolved']])
        
        compliance_score = max(0, 100 - (total_violations * 10) - (critical_violations * 20))
        
        return {
            "framework": framework.value,
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_events": total_events,
                "total_violations": total_violations,
                "critical_violations": critical_violations,
                "resolved_violations": resolved_violations,
                "compliance_score": compliance_score
            },
            "violations": violations,
            "recommendations": self._generate_compliance_recommendations(violations),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _generate_compliance_recommendations(self, violations: List[Dict]) -> List[str]:
        """Generate compliance recommendations based on violations."""
        recommendations = []
        
        if violations:
            critical_count = len([v for v in violations if v['severity'] == 'critical'])
            if critical_count > 0:
                recommendations.append(f"Address {critical_count} critical compliance violations immediately")
            
            unresolved_count = len([v for v in violations if not v['resolved']])
            if unresolved_count > 0:
                recommendations.append(f"Resolve {unresolved_count} outstanding compliance violations")
            
            recommendations.extend([
                "Implement regular compliance training for staff",
                "Review and update compliance procedures quarterly",
                "Conduct regular compliance audits",
                "Enhance monitoring and alerting for compliance violations"
            ])
        else:
            recommendations.append("Maintain current compliance practices")
            recommendations.append("Continue regular compliance monitoring")
        
        return recommendations
    
    async def export_audit_data(self, format_type: str = "csv", 
                              start_date: datetime = None, end_date: datetime = None) -> str:
        """Export audit data in specified format."""
        events = await self.get_audit_trail(start_date, end_date, limit=10000)
        
        if format_type.lower() == "csv":
            return await self._export_csv(events)
        elif format_type.lower() == "json":
            return json.dumps(events, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    async def _export_csv(self, events: List[Dict]) -> str:
        """Export events to CSV format."""
        if not events:
            return ""
        
        import io
        output = io.StringIO()
        
        fieldnames = ["event_id", "event_type", "user_id", "timestamp", "ip_address", 
                     "action", "outcome", "risk_level"]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for event in events:
            row = {k: v for k, v in event.items() if k in fieldnames}
            writer.writerow(row)
        
        return output.getvalue()


# Global compliance service instance
_compliance_service: Optional[ComplianceService] = None

def get_compliance_service() -> ComplianceService:
    """Get or create compliance service instance."""
    global _compliance_service
    if _compliance_service is None:
        _compliance_service = ComplianceService()
    return _compliance_service
