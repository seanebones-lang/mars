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
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict, field
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import ssl
from jinja2 import Template
from enum import Enum
from uuid import uuid4

logger = logging.getLogger(__name__)


class WebhookStatus(str, Enum):
    """Webhook delivery status"""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class WebhookDelivery:
    """Tracks webhook delivery attempts"""
    delivery_id: str
    webhook_id: str
    alert_id: str
    url: str
    payload: Dict[str, Any]
    status: WebhookStatus
    attempts: int = 0
    max_attempts: int = 3
    last_attempt_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None
    
    def should_retry(self) -> bool:
        """Check if delivery should be retried"""
        if self.status == WebhookStatus.DELIVERED:
            return False
        if self.attempts >= self.max_attempts:
            return False
        if self.next_retry_at and datetime.utcnow() < self.next_retry_at:
            return False
        return True
    
    def calculate_next_retry(self) -> datetime:
        """Calculate next retry time using exponential backoff"""
        # Exponential backoff: 1min, 5min, 15min
        delays = [60, 300, 900]  # seconds
        delay = delays[min(self.attempts, len(delays) - 1)]
        return datetime.utcnow() + timedelta(seconds=delay)


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
    secret: Optional[str] = None  # Secret for HMAC signature
    verify_ssl: bool = True


class WebhookService:
    """Enterprise webhook and notification service with retry logic and delivery tracking."""
    
    def __init__(self):
        self.webhooks: Dict[str, WebhookConfig] = {}
        self.alert_history: List[WebhookAlert] = []
        self.rate_limits: Dict[str, List[datetime]] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Delivery tracking
        self.deliveries: Dict[str, WebhookDelivery] = {}
        self.failed_queue: List[WebhookDelivery] = []
        self.retry_task: Optional[asyncio.Task] = None
        
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
        # Start retry background task
        self.retry_task = asyncio.create_task(self._retry_failed_webhooks())
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Cancel retry task
        if self.retry_task:
            self.retry_task.cancel()
            try:
                await self.retry_task
            except asyncio.CancelledError:
                pass
        
        if self.session:
            await self.session.close()
    
    def _generate_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """Generate HMAC signature for webhook payload."""
        payload_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    async def _retry_failed_webhooks(self):
        """Background task to retry failed webhook deliveries."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Find deliveries that need retry
                to_retry = [
                    delivery for delivery in self.deliveries.values()
                    if delivery.should_retry()
                ]
                
                for delivery in to_retry:
                    logger.info(f"Retrying webhook delivery: {delivery.delivery_id} (attempt {delivery.attempts + 1})")
                    
                    # Get webhook config
                    config = self.webhooks.get(delivery.webhook_id)
                    if not config or not config.enabled:
                        delivery.status = WebhookStatus.FAILED
                        delivery.error_message = "Webhook disabled or removed"
                        continue
                    
                    # Attempt delivery
                    success = await self._deliver_webhook(delivery, config)
                    
                    if success:
                        delivery.status = WebhookStatus.DELIVERED
                        delivery.delivered_at = datetime.utcnow()
                        logger.info(f"Webhook delivery succeeded on retry: {delivery.delivery_id}")
                    else:
                        delivery.attempts += 1
                        delivery.last_attempt_at = datetime.utcnow()
                        
                        if delivery.attempts >= delivery.max_attempts:
                            delivery.status = WebhookStatus.FAILED
                            self.failed_queue.append(delivery)
                            logger.error(f"Webhook delivery failed permanently: {delivery.delivery_id}")
                        else:
                            delivery.status = WebhookStatus.RETRYING
                            delivery.next_retry_at = delivery.calculate_next_retry()
                            logger.warning(f"Webhook delivery failed, will retry: {delivery.delivery_id}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in retry task: {e}")
    
    async def _deliver_webhook(self, delivery: WebhookDelivery, config: WebhookConfig) -> bool:
        """Attempt to deliver a webhook."""
        try:
            # Add signature header if secret is configured
            headers = dict(config.headers or {})
            if config.secret:
                signature = self._generate_signature(delivery.payload, config.secret)
                headers['X-Webhook-Signature'] = signature
            
            # Add delivery tracking headers
            headers['X-Delivery-ID'] = delivery.delivery_id
            headers['X-Delivery-Attempt'] = str(delivery.attempts + 1)
            
            # Send request
            ssl_context = None if config.verify_ssl else False
            async with self.session.post(
                delivery.url,
                json=delivery.payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=config.timeout_seconds),
                ssl=ssl_context
            ) as response:
                delivery.response_status = response.status
                delivery.response_body = await response.text()
                
                if response.status == 200:
                    return True
                else:
                    delivery.error_message = f"HTTP {response.status}: {delivery.response_body[:200]}"
                    return False
        
        except asyncio.TimeoutError:
            delivery.error_message = f"Timeout after {config.timeout_seconds}s"
            return False
        except Exception as e:
            delivery.error_message = str(e)
            return False
    
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
        """Send webhook notification with delivery tracking."""
        
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
            
            # Create delivery record
            delivery = WebhookDelivery(
                delivery_id=str(uuid4()),
                webhook_id=config.webhook_id,
                alert_id=alert.alert_id,
                url=config.url,
                payload=payload,
                status=WebhookStatus.PENDING,
                max_attempts=config.retry_count
            )
            
            # Store delivery
            self.deliveries[delivery.delivery_id] = delivery
            
            # Attempt delivery
            success = await self._deliver_webhook(delivery, config)
            
            if success:
                delivery.status = WebhookStatus.DELIVERED
                delivery.delivered_at = datetime.utcnow()
                logger.info(f"Webhook sent successfully: {config.name}")
                return True
            else:
                delivery.attempts = 1
                delivery.last_attempt_at = datetime.utcnow()
                delivery.status = WebhookStatus.RETRYING
                delivery.next_retry_at = delivery.calculate_next_retry()
                logger.warning(f"Webhook failed, will retry: {config.name}")
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
        """Get webhook statistics including delivery tracking."""
        total_alerts = len(self.alert_history)
        
        # Count by severity
        severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for alert in self.alert_history:
            severity_counts[alert.severity] += 1
        
        # Count by type
        type_counts = {}
        for alert in self.alert_history:
            type_counts[alert.alert_type] = type_counts.get(alert.alert_type, 0) + 1
        
        # Delivery statistics
        delivery_stats = {
            "total_deliveries": len(self.deliveries),
            "delivered": len([d for d in self.deliveries.values() if d.status == WebhookStatus.DELIVERED]),
            "pending": len([d for d in self.deliveries.values() if d.status == WebhookStatus.PENDING]),
            "retrying": len([d for d in self.deliveries.values() if d.status == WebhookStatus.RETRYING]),
            "failed": len([d for d in self.deliveries.values() if d.status == WebhookStatus.FAILED]),
            "failed_queue_size": len(self.failed_queue)
        }
        
        # Calculate success rate
        if delivery_stats["total_deliveries"] > 0:
            delivery_stats["success_rate"] = delivery_stats["delivered"] / delivery_stats["total_deliveries"]
        else:
            delivery_stats["success_rate"] = 0.0
        
        return {
            "total_alerts": total_alerts,
            "total_webhooks": len(self.webhooks),
            "enabled_webhooks": len([w for w in self.webhooks.values() if w.enabled]),
            "severity_distribution": severity_counts,
            "alert_type_distribution": type_counts,
            "rate_limits": {wid: len(timestamps) for wid, timestamps in self.rate_limits.items()},
            "delivery_stats": delivery_stats
        }
    
    def get_delivery_status(self, delivery_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific delivery."""
        delivery = self.deliveries.get(delivery_id)
        if delivery:
            return asdict(delivery)
        return None
    
    def get_failed_deliveries(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get failed webhook deliveries."""
        recent_failed = self.failed_queue[-limit:] if limit else self.failed_queue
        return [asdict(delivery) for delivery in reversed(recent_failed)]
    
    def clear_old_deliveries(self, days: int = 7):
        """Clear delivery records older than specified days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Remove old deliveries
        old_ids = [
            delivery_id for delivery_id, delivery in self.deliveries.items()
            if delivery.created_at < cutoff and delivery.status in [WebhookStatus.DELIVERED, WebhookStatus.FAILED]
        ]
        
        for delivery_id in old_ids:
            del self.deliveries[delivery_id]
        
        logger.info(f"Cleared {len(old_ids)} old webhook deliveries")


# Global webhook service instance
_webhook_service: Optional[WebhookService] = None

def get_webhook_service() -> WebhookService:
    """Get or create webhook service instance."""
    global _webhook_service
    if _webhook_service is None:
        _webhook_service = WebhookService()
    return _webhook_service
