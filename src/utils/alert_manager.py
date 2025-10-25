"""
Alert Manager
P0-Critical: Critical alerts and notifications for production incidents
"""

import os
import json
import logging
import requests
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Alert notification channels."""
    SLACK = "slack"
    EMAIL = "email"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"


@dataclass
class Alert:
    """Alert data structure."""
    title: str
    message: str
    severity: AlertSeverity
    timestamp: str
    service: str = "agentguard"
    environment: str = "production"
    tags: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None


class AlertManager:
    """Manages critical alerts and notifications."""
    
    def __init__(self):
        """Initialize alert manager."""
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        self.pagerduty_key = os.getenv("PAGERDUTY_API_KEY")
        self.alert_email = os.getenv("ALERT_EMAIL", "info@mothership-ai.com")
        
        # Alert thresholds
        self.error_rate_threshold = float(os.getenv("ERROR_RATE_THRESHOLD", "0.05"))  # 5%
        self.response_time_threshold = float(os.getenv("RESPONSE_TIME_THRESHOLD", "2000"))  # 2s
        
        logger.info(f"Alert manager initialized for {self.environment}")
    
    def send_alert(self, alert: Alert, channels: Optional[List[AlertChannel]] = None):
        """
        Send alert to specified channels.
        
        Args:
            alert: Alert to send
            channels: List of channels to send to (default: all configured)
        """
        if channels is None:
            channels = self._get_default_channels(alert.severity)
        
        for channel in channels:
            try:
                if channel == AlertChannel.SLACK and self.slack_webhook:
                    self._send_slack_alert(alert)
                elif channel == AlertChannel.PAGERDUTY and self.pagerduty_key:
                    self._send_pagerduty_alert(alert)
                elif channel == AlertChannel.EMAIL:
                    self._send_email_alert(alert)
                elif channel == AlertChannel.WEBHOOK:
                    self._send_webhook_alert(alert)
            except Exception as e:
                logger.error(f"Failed to send alert via {channel.value}: {e}")
    
    def _get_default_channels(self, severity: AlertSeverity) -> List[AlertChannel]:
        """Get default channels based on severity."""
        if severity == AlertSeverity.CRITICAL:
            return [AlertChannel.SLACK, AlertChannel.PAGERDUTY, AlertChannel.EMAIL]
        elif severity == AlertSeverity.ERROR:
            return [AlertChannel.SLACK, AlertChannel.EMAIL]
        elif severity == AlertSeverity.WARNING:
            return [AlertChannel.SLACK]
        else:
            return [AlertChannel.SLACK]
    
    def _send_slack_alert(self, alert: Alert):
        """Send alert to Slack."""
        if not self.slack_webhook:
            return
        
        # Emoji based on severity
        emoji_map = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.ERROR: "❌",
            AlertSeverity.CRITICAL: "🚨",
        }
        emoji = emoji_map.get(alert.severity, "📢")
        
        # Color based on severity
        color_map = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ff9800",
            AlertSeverity.ERROR: "#f44336",
            AlertSeverity.CRITICAL: "#d32f2f",
        }
        color = color_map.get(alert.severity, "#808080")
        
        # Build Slack message
        payload = {
            "text": f"{emoji} *{alert.title}*",
            "attachments": [
                {
                    "color": color,
                    "fields": [
                        {
                            "title": "Message",
                            "value": alert.message,
                            "short": False
                        },
                        {
                            "title": "Severity",
                            "value": alert.severity.value.upper(),
                            "short": True
                        },
                        {
                            "title": "Environment",
                            "value": alert.environment,
                            "short": True
                        },
                        {
                            "title": "Service",
                            "value": alert.service,
                            "short": True
                        },
                        {
                            "title": "Timestamp",
                            "value": alert.timestamp,
                            "short": True
                        }
                    ]
                }
            ]
        }
        
        # Add tags if present
        if alert.tags:
            tag_str = ", ".join([f"{k}={v}" for k, v in alert.tags.items()])
            payload["attachments"][0]["fields"].append({
                "title": "Tags",
                "value": tag_str,
                "short": False
            })
        
        # Send to Slack
        response = requests.post(
            self.slack_webhook,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        logger.info(f"Slack alert sent: {alert.title}")
    
    def _send_pagerduty_alert(self, alert: Alert):
        """Send alert to PagerDuty."""
        if not self.pagerduty_key:
            return
        
        payload = {
            "routing_key": self.pagerduty_key,
            "event_action": "trigger",
            "payload": {
                "summary": alert.title,
                "severity": alert.severity.value,
                "source": alert.service,
                "timestamp": alert.timestamp,
                "custom_details": {
                    "message": alert.message,
                    "environment": alert.environment,
                    "tags": alert.tags or {},
                    "metadata": alert.metadata or {}
                }
            }
        }
        
        response = requests.post(
            "https://events.pagerduty.com/v2/enqueue",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        logger.info(f"PagerDuty alert sent: {alert.title}")
    
    def _send_email_alert(self, alert: Alert):
        """Send alert via email (placeholder - requires email service)."""
        logger.info(f"Email alert (not implemented): {alert.title} to {self.alert_email}")
        # TODO: Implement email sending via SendGrid, SES, or similar
    
    def _send_webhook_alert(self, alert: Alert):
        """Send alert to custom webhook."""
        webhook_url = os.getenv("ALERT_WEBHOOK_URL")
        if not webhook_url:
            return
        
        payload = asdict(alert)
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        logger.info(f"Webhook alert sent: {alert.title}")
    
    # Predefined alert methods for common scenarios
    
    def alert_api_down(self, service_name: str, error: str):
        """Alert when API service is down."""
        alert = Alert(
            title=f"🚨 API Service Down: {service_name}",
            message=f"The {service_name} API is not responding. Error: {error}",
            severity=AlertSeverity.CRITICAL,
            timestamp=datetime.utcnow().isoformat(),
            environment=self.environment,
            tags={"service": service_name, "type": "availability"}
        )
        self.send_alert(alert)
    
    def alert_database_error(self, error: str):
        """Alert when database error occurs."""
        alert = Alert(
            title="❌ Database Error",
            message=f"Database operation failed: {error}",
            severity=AlertSeverity.CRITICAL,
            timestamp=datetime.utcnow().isoformat(),
            environment=self.environment,
            tags={"component": "database", "type": "error"}
        )
        self.send_alert(alert)
    
    def alert_high_error_rate(self, error_rate: float, threshold: float):
        """Alert when error rate exceeds threshold."""
        alert = Alert(
            title="⚠️ High Error Rate Detected",
            message=f"Error rate ({error_rate:.2%}) exceeds threshold ({threshold:.2%})",
            severity=AlertSeverity.ERROR,
            timestamp=datetime.utcnow().isoformat(),
            environment=self.environment,
            tags={"metric": "error_rate", "type": "performance"}
        )
        self.send_alert(alert)
    
    def alert_slow_response(self, endpoint: str, response_time: float):
        """Alert when API response time is slow."""
        alert = Alert(
            title="⚠️ Slow API Response",
            message=f"Endpoint {endpoint} responded in {response_time:.2f}ms (threshold: {self.response_time_threshold}ms)",
            severity=AlertSeverity.WARNING,
            timestamp=datetime.utcnow().isoformat(),
            environment=self.environment,
            tags={"endpoint": endpoint, "metric": "response_time", "type": "performance"}
        )
        self.send_alert(alert)
    
    def alert_deployment_success(self, version: str):
        """Alert when deployment succeeds."""
        alert = Alert(
            title="✅ Deployment Successful",
            message=f"Successfully deployed version {version} to {self.environment}",
            severity=AlertSeverity.INFO,
            timestamp=datetime.utcnow().isoformat(),
            environment=self.environment,
            tags={"version": version, "type": "deployment"}
        )
        self.send_alert(alert, channels=[AlertChannel.SLACK])
    
    def alert_deployment_failure(self, version: str, error: str):
        """Alert when deployment fails."""
        alert = Alert(
            title="🚨 Deployment Failed",
            message=f"Failed to deploy version {version}: {error}",
            severity=AlertSeverity.CRITICAL,
            timestamp=datetime.utcnow().isoformat(),
            environment=self.environment,
            tags={"version": version, "type": "deployment"}
        )
        self.send_alert(alert)
    
    def alert_security_incident(self, incident_type: str, details: str):
        """Alert for security incidents."""
        alert = Alert(
            title=f"🚨 SECURITY INCIDENT: {incident_type}",
            message=f"Security incident detected: {details}",
            severity=AlertSeverity.CRITICAL,
            timestamp=datetime.utcnow().isoformat(),
            environment=self.environment,
            tags={"type": "security", "incident_type": incident_type}
        )
        self.send_alert(alert)
    
    def alert_backup_failure(self, backup_name: str, error: str):
        """Alert when backup fails."""
        alert = Alert(
            title="❌ Backup Failed",
            message=f"Database backup '{backup_name}' failed: {error}",
            severity=AlertSeverity.ERROR,
            timestamp=datetime.utcnow().isoformat(),
            environment=self.environment,
            tags={"component": "backup", "type": "error"}
        )
        self.send_alert(alert)


# Global alert manager instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get the global alert manager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager

