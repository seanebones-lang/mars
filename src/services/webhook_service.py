"""
Enterprise Webhook and Notification Service
Handles real-time alerts to Slack, Teams, email, and custom endpoints.
"""

import os
import json
import asyncio
import aiohttp
import smtplib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import ssl
from jinja2 import Template

logger = logging.getLogger(__name__)


@dataclass
class WebhookAlert:
    """Represents an alert to be sent via webhook."""
    alert_id: str
    alert_type: str  # 'hallucination', 'system_error', 'performance', 'security'
    severity: str    # 'low', 'medium', 'high', 'critical'
    title: str
    message: str
    agent_id: str
    agent_name: str
    hallucination_risk: float
    confidence: float
    timestamp: str
    details: Dict[str, Any]
    workstation_id: Optional[str] = None
    user_id: Optional[str] = None
    requires_acknowledgment: bool = False
    escalation_level: int = 0


@dataclass
class WebhookConfig:
    """Configuration for a webhook endpoint."""
    webhook_id: str
    name: str
    url: str
    webhook_type: str  # 'slack', 'teams', 'generic', 'email'
    enabled: bool = True
    alert_types: List[str] = None  # None means all types
    severity_threshold: str = 'medium'  # minimum severity to trigger
    headers: Dict[str, str] = None
    template: str = None
    retry_count: int = 3
    timeout_seconds: int = 30
    rate_limit_per_minute: int = 60
    escalation_delay_minutes: int = 15


class WebhookService:
    """Enterprise webhook and notification service."""
    
    def __init__(self):
        self.webhooks: Dict[str, WebhookConfig] = {}
        self.alert_history: List[WebhookAlert] = []
        self.rate_limits: Dict[str, List[datetime]] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Email configuration
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_from_email = os.getenv("SMTP_FROM_EMAIL", "alerts@watcher-ai.com")
        
        # Load default webhook configurations
        self._load_default_webhooks()
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _load_default_webhooks(self):
        """Load default webhook configurations from environment."""
        
        # Slack webhook
        slack_url = os.getenv("SLACK_WEBHOOK_URL")
        if slack_url:
            self.add_webhook(WebhookConfig(
                webhook_id="default_slack",
                name="Default Slack Channel",
                url=slack_url,
                webhook_type="slack",
                alert_types=["hallucination", "system_error"],
                severity_threshold="medium"
            ))
        
        # Teams webhook
        teams_url = os.getenv("TEAMS_WEBHOOK_URL")
        if teams_url:
            self.add_webhook(WebhookConfig(
                webhook_id="default_teams",
                name="Default Teams Channel",
                url=teams_url,
                webhook_type="teams",
                alert_types=["hallucination", "security"],
                severity_threshold="high"
            ))
        
        # PagerDuty integration key
        pagerduty_key = os.getenv("PAGERDUTY_INTEGRATION_KEY")
        if pagerduty_key:
            self.add_webhook(WebhookConfig(
                webhook_id="default_pagerduty",
                name="PagerDuty Critical Alerts",
                url=f"https://events.pagerduty.com/v2/enqueue",
                webhook_type="pagerduty",
                alert_types=["hallucination", "system_error", "security"],
                severity_threshold="critical",
                headers={"Content-Type": "application/json"}
            ))
    
    def add_webhook(self, config: WebhookConfig):
        """Add a webhook configuration."""
        if config.alert_types is None:
            config.alert_types = ["hallucination", "system_error", "performance", "security"]
        if config.headers is None:
            config.headers = {"Content-Type": "application/json"}
        
        self.webhooks[config.webhook_id] = config
        logger.info(f"Added webhook: {config.name} ({config.webhook_type})")
    
    def remove_webhook(self, webhook_id: str):
        """Remove a webhook configuration."""
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            logger.info(f"Removed webhook: {webhook_id}")
    
    def _check_rate_limit(self, webhook_id: str, limit_per_minute: int) -> bool:
        """Check if webhook is within rate limits."""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        if webhook_id not in self.rate_limits:
            self.rate_limits[webhook_id] = []
        
        # Clean old entries
        self.rate_limits[webhook_id] = [
            timestamp for timestamp in self.rate_limits[webhook_id]
            if timestamp > minute_ago
        ]
        
        # Check limit
        if len(self.rate_limits[webhook_id]) >= limit_per_minute:
            return False
        
        # Add current request
        self.rate_limits[webhook_id].append(now)
        return True
    
    def _should_trigger_webhook(self, alert: WebhookAlert, config: WebhookConfig) -> bool:
        """Determine if webhook should be triggered for this alert."""
        
        # Check if webhook is enabled
        if not config.enabled:
            return False
        
        # Check alert type filter
        if config.alert_types and alert.alert_type not in config.alert_types:
            return False
        
        # Check severity threshold
        severity_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        alert_level = severity_levels.get(alert.severity, 0)
        threshold_level = severity_levels.get(config.severity_threshold, 2)
        
        if alert_level < threshold_level:
            return False
        
        # Check rate limits
        if not self._check_rate_limit(config.webhook_id, config.rate_limit_per_minute):
            logger.warning(f"Rate limit exceeded for webhook: {config.webhook_id}")
            return False
        
        return True
    
    def _format_slack_message(self, alert: WebhookAlert, config: WebhookConfig) -> Dict[str, Any]:
        """Format alert for Slack webhook."""
        
        # Color based on severity
        colors = {
            "low": "#36a64f",      # Green
            "medium": "#ff9500",   # Orange  
            "high": "#ff0000",     # Red
            "critical": "#8B0000"  # Dark Red
        }
        
        color = colors.get(alert.severity, "#36a64f")
        
        # Risk emoji
        risk_emoji = "🟢" if alert.hallucination_risk < 0.3 else "🟡" if alert.hallucination_risk < 0.7 else "🔴"
        
        payload = {
            "text": f"{risk_emoji} *Watcher-AI Alert*: {alert.title}",
            "attachments": [
                {
                    "color": color,
                    "fields": [
                        {
                            "title": "Agent",
                            "value": f"{alert.agent_name} (`{alert.agent_id}`)",
                            "short": True
                        },
                        {
                            "title": "Risk Level",
                            "value": f"{alert.hallucination_risk:.1%}",
                            "short": True
                        },
                        {
                            "title": "Confidence",
                            "value": f"{alert.confidence:.1%}",
                            "short": True
                        },
                        {
                            "title": "Severity",
                            "value": alert.severity.upper(),
                            "short": True
                        },
                        {
                            "title": "Message",
                            "value": alert.message,
                            "short": False
                        }
                    ],
                    "footer": "Watcher-AI",
                    "footer_icon": "https://watcher.mothership-ai.com/favicon.ico",
                    "ts": int(datetime.fromisoformat(alert.timestamp.replace('Z', '+00:00')).timestamp())
                }
            ]
        }
        
        if alert.workstation_id:
            payload["attachments"][0]["fields"].insert(1, {
                "title": "Workstation",
                "value": alert.workstation_id,
                "short": True
            })
        
        return payload
    
    def _format_teams_message(self, alert: WebhookAlert, config: WebhookConfig) -> Dict[str, Any]:
        """Format alert for Microsoft Teams webhook."""
        
        # Color based on severity
        colors = {
            "low": "Good",
            "medium": "Warning", 
            "high": "Attention",
            "critical": "Attention"
        }
        
        theme_color = colors.get(alert.severity, "Good")
        
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": theme_color,
            "summary": f"Watcher-AI Alert: {alert.title}",
            "sections": [
                {
                    "activityTitle": f"🔍 **Watcher-AI Alert**",
                    "activitySubtitle": alert.title,
                    "activityImage": "https://watcher.mothership-ai.com/favicon.ico",
                    "facts": [
                        {"name": "Agent", "value": f"{alert.agent_name} ({alert.agent_id})"},
                        {"name": "Risk Level", "value": f"{alert.hallucination_risk:.1%}"},
                        {"name": "Confidence", "value": f"{alert.confidence:.1%}"},
                        {"name": "Severity", "value": alert.severity.upper()},
                        {"name": "Timestamp", "value": alert.timestamp}
                    ],
                    "markdown": True
                }
            ]
        }
        
        if alert.workstation_id:
            payload["sections"][0]["facts"].insert(1, {
                "name": "Workstation", 
                "value": alert.workstation_id
            })
        
        return payload
    
    def _format_pagerduty_message(self, alert: WebhookAlert, config: WebhookConfig) -> Dict[str, Any]:
        """Format alert for PagerDuty webhook."""
        
        integration_key = os.getenv("PAGERDUTY_INTEGRATION_KEY")
        if not integration_key:
            raise ValueError("PagerDuty integration key not configured")
        
        payload = {
            "routing_key": integration_key,
            "event_action": "trigger",
            "dedup_key": f"watcher-ai-{alert.alert_id}",
            "payload": {
                "summary": f"Watcher-AI: {alert.title}",
                "source": f"watcher-ai-{alert.agent_id}",
                "severity": alert.severity,
                "component": "watcher-ai",
                "group": "hallucination-detection",
                "class": alert.alert_type,
                "custom_details": {
                    "agent_name": alert.agent_name,
                    "agent_id": alert.agent_id,
                    "hallucination_risk": alert.hallucination_risk,
                    "confidence": alert.confidence,
                    "message": alert.message,
                    "workstation_id": alert.workstation_id,
                    "details": alert.details
                }
            }
        }
        
        return payload
    
    def _format_generic_message(self, alert: WebhookAlert, config: WebhookConfig) -> Dict[str, Any]:
        """Format alert for generic webhook."""
        
        if config.template:
            # Use Jinja2 template if provided
            template = Template(config.template)
            return json.loads(template.render(alert=alert))
        else:
            # Default JSON format
            return {
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "agent": {
                    "id": alert.agent_id,
                    "name": alert.agent_name
                },
                "metrics": {
                    "hallucination_risk": alert.hallucination_risk,
                    "confidence": alert.confidence
                },
                "timestamp": alert.timestamp,
                "workstation_id": alert.workstation_id,
                "user_id": alert.user_id,
                "details": alert.details
            }
    
    async def _send_webhook(self, alert: WebhookAlert, config: WebhookConfig) -> bool:
        """Send webhook notification."""
        
        try:
            # Format message based on webhook type
            if config.webhook_type == "slack":
                payload = self._format_slack_message(alert, config)
            elif config.webhook_type == "teams":
                payload = self._format_teams_message(alert, config)
            elif config.webhook_type == "pagerduty":
                payload = self._format_pagerduty_message(alert, config)
            else:
                payload = self._format_generic_message(alert, config)
            
            # Send HTTP request
            async with self.session.post(
                config.url,
                json=payload,
                headers=config.headers,
                timeout=aiohttp.ClientTimeout(total=config.timeout_seconds)
            ) as response:
                
                if response.status == 200:
                    logger.info(f"Webhook sent successfully: {config.name}")
                    return True
                else:
                    logger.error(f"Webhook failed: {config.name} - Status: {response.status}")
                    return False
        
        except Exception as e:
            logger.error(f"Webhook error: {config.name} - {str(e)}")
            return False
    
    async def _send_email(self, alert: WebhookAlert, recipients: List[str]) -> bool:
        """Send email notification."""
        
        if not self.smtp_username or not self.smtp_password:
            logger.warning("SMTP credentials not configured, skipping email")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Watcher-AI Alert: {alert.title}"
            msg['From'] = self.smtp_from_email
            msg['To'] = ", ".join(recipients)
            
            # HTML email template
            html_template = """
            <html>
            <body style="font-family: Arial, sans-serif; margin: 20px;">
                <div style="background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h2 style="margin: 0;">🔍 Watcher-AI Alert</h2>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">Real-Time Hallucination Defense</p>
                </div>
                
                <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="color: #d32f2f; margin-top: 0;">{{ alert.title }}</h3>
                    <p><strong>Message:</strong> {{ alert.message }}</p>
                </div>
                
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr style="background: #e3f2fd;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Agent</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{{ alert.agent_name }} ({{ alert.agent_id }})</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Risk Level</td>
                        <td style="padding: 10px; border: 1px solid #ddd; color: {% if alert.hallucination_risk > 0.7 %}#d32f2f{% elif alert.hallucination_risk > 0.3 %}#f57c00{% else %}#388e3c{% endif %};">
                            {{ "%.1f%%" | format(alert.hallucination_risk * 100) }}
                        </td>
                    </tr>
                    <tr style="background: #e3f2fd;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Confidence</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{{ "%.1f%%" | format(alert.confidence * 100) }}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Severity</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">
                            <span style="background: {% if alert.severity == 'critical' %}#d32f2f{% elif alert.severity == 'high' %}#f57c00{% elif alert.severity == 'medium' %}#fbc02d{% else %}#388e3c{% endif %}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                                {{ alert.severity.upper() }}
                            </span>
                        </td>
                    </tr>
                    <tr style="background: #e3f2fd;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Timestamp</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{{ alert.timestamp }}</td>
                    </tr>
                    {% if alert.workstation_id %}
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Workstation</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{{ alert.workstation_id }}</td>
                    </tr>
                    {% endif %}
                </table>
                
                <div style="background: #fff3e0; padding: 15px; border-left: 4px solid #ff9800; margin-bottom: 20px;">
                    <p style="margin: 0;"><strong>Action Required:</strong> Please review this alert and take appropriate action if necessary.</p>
                </div>
                
                <div style="text-align: center; padding: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px;">
                    <p>© 2025 Watcher-AI | Real-Time Hallucination Defense</p>
                    <p>Visit <a href="https://watcher.mothership-ai.com" style="color: #1976D2;">watcher.mothership-ai.com</a> for more information</p>
                </div>
            </body>
            </html>
            """
            
            template = Template(html_template)
            html_content = template.render(alert=alert)
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to: {recipients}")
            return True
            
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            return False
    
    async def send_alert(self, alert: WebhookAlert, email_recipients: List[str] = None) -> Dict[str, bool]:
        """Send alert to all configured webhooks and email recipients."""
        
        results = {}
        
        # Store alert in history
        self.alert_history.append(alert)
        
        # Keep only last 1000 alerts in memory
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
        
        # Send to webhooks
        webhook_tasks = []
        for webhook_id, config in self.webhooks.items():
            if self._should_trigger_webhook(alert, config):
                task = self._send_webhook(alert, config)
                webhook_tasks.append((webhook_id, task))
        
        # Execute webhook tasks
        for webhook_id, task in webhook_tasks:
            try:
                success = await task
                results[f"webhook_{webhook_id}"] = success
            except Exception as e:
                logger.error(f"Webhook task failed: {webhook_id} - {str(e)}")
                results[f"webhook_{webhook_id}"] = False
        
        # Send email if recipients provided
        if email_recipients:
            email_success = await self._send_email(alert, email_recipients)
            results["email"] = email_success
        
        return results
    
    def get_webhook_configs(self) -> List[Dict[str, Any]]:
        """Get all webhook configurations."""
        return [asdict(config) for config in self.webhooks.values()]
    
    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent alert history."""
        recent_alerts = self.alert_history[-limit:] if limit else self.alert_history
        return [asdict(alert) for alert in reversed(recent_alerts)]
    
    def get_webhook_stats(self) -> Dict[str, Any]:
        """Get webhook statistics."""
        total_alerts = len(self.alert_history)
        
        # Count by severity
        severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for alert in self.alert_history:
            severity_counts[alert.severity] += 1
        
        # Count by type
        type_counts = {}
        for alert in self.alert_history:
            type_counts[alert.alert_type] = type_counts.get(alert.alert_type, 0) + 1
        
        return {
            "total_alerts": total_alerts,
            "total_webhooks": len(self.webhooks),
            "enabled_webhooks": len([w for w in self.webhooks.values() if w.enabled]),
            "severity_distribution": severity_counts,
            "alert_type_distribution": type_counts,
            "rate_limits": {wid: len(timestamps) for wid, timestamps in self.rate_limits.items()}
        }


# Global webhook service instance
_webhook_service: Optional[WebhookService] = None

def get_webhook_service() -> WebhookService:
    """Get or create webhook service instance."""
    global _webhook_service
    if _webhook_service is None:
        _webhook_service = WebhookService()
    return _webhook_service
