"""
Beta Testing Program Management
Handles beta user onboarding, feedback collection, and program management.

October 2025 Enhancement: Comprehensive beta program for production launch preparation.
"""

import logging
import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiohttp
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


class BetaUserStatus(Enum):
    """Beta user status levels."""
    APPLIED = "applied"
    APPROVED = "approved"
    ACTIVE = "active"
    INACTIVE = "inactive"
    GRADUATED = "graduated"
    SUSPENDED = "suspended"


class FeedbackType(Enum):
    """Types of feedback."""
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    PERFORMANCE_ISSUE = "performance_issue"
    USABILITY_FEEDBACK = "usability_feedback"
    GENERAL_FEEDBACK = "general_feedback"


class FeedbackPriority(Enum):
    """Feedback priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BetaUser:
    """Beta user profile."""
    user_id: str
    email: str
    name: str
    company: str
    use_case: str
    status: BetaUserStatus
    signup_date: datetime
    last_active: Optional[datetime] = None
    api_key: Optional[str] = None
    usage_stats: Dict[str, Any] = None
    feedback_count: int = 0
    satisfaction_score: Optional[float] = None
    notes: str = ""


@dataclass
class FeedbackItem:
    """User feedback item."""
    feedback_id: str
    user_id: str
    feedback_type: FeedbackType
    priority: FeedbackPriority
    title: str
    description: str
    steps_to_reproduce: Optional[str] = None
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    environment_info: Dict[str, Any] = None
    attachments: List[str] = None
    status: str = "open"  # open, in_progress, resolved, closed
    created_at: datetime = None
    updated_at: datetime = None
    assigned_to: Optional[str] = None
    resolution: Optional[str] = None


@dataclass
class BetaMetrics:
    """Beta program metrics."""
    total_users: int
    active_users: int
    feedback_items: int
    critical_issues: int
    average_satisfaction: float
    api_usage_total: int
    feature_adoption_rates: Dict[str, float]
    churn_rate: float
    graduation_rate: float


class BetaDatabase:
    """Database management for beta program."""
    
    def __init__(self, db_path: str = "beta_program.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Beta users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS beta_users (
                    user_id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    company TEXT,
                    use_case TEXT,
                    status TEXT NOT NULL,
                    signup_date TEXT NOT NULL,
                    last_active TEXT,
                    api_key TEXT,
                    usage_stats TEXT,
                    feedback_count INTEGER DEFAULT 0,
                    satisfaction_score REAL,
                    notes TEXT
                )
            """)
            
            # Feedback table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    feedback_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    feedback_type TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    steps_to_reproduce TEXT,
                    expected_behavior TEXT,
                    actual_behavior TEXT,
                    environment_info TEXT,
                    attachments TEXT,
                    status TEXT DEFAULT 'open',
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    assigned_to TEXT,
                    resolution TEXT,
                    FOREIGN KEY (user_id) REFERENCES beta_users (user_id)
                )
            """)
            
            # Usage tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    response_time_ms REAL,
                    status_code INTEGER,
                    error_message TEXT,
                    FOREIGN KEY (user_id) REFERENCES beta_users (user_id)
                )
            """)
            
            conn.commit()
            conn.close()
            
            logger.info("Beta program database initialized")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    def add_user(self, user: BetaUser) -> bool:
        """Add new beta user."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO beta_users (
                    user_id, email, name, company, use_case, status, 
                    signup_date, api_key, usage_stats, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user.user_id, user.email, user.name, user.company, user.use_case,
                user.status.value, user.signup_date.isoformat(), user.api_key,
                json.dumps(user.usage_stats or {}), user.notes
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error adding user {user.user_id}: {e}")
            return False
    
    def get_user(self, user_id: str) -> Optional[BetaUser]:
        """Get beta user by ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM beta_users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return BetaUser(
                    user_id=row[0],
                    email=row[1],
                    name=row[2],
                    company=row[3],
                    use_case=row[4],
                    status=BetaUserStatus(row[5]),
                    signup_date=datetime.fromisoformat(row[6]),
                    last_active=datetime.fromisoformat(row[7]) if row[7] else None,
                    api_key=row[8],
                    usage_stats=json.loads(row[9]) if row[9] else {},
                    feedback_count=row[10],
                    satisfaction_score=row[11],
                    notes=row[12] or ""
                )
            return None
            
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    def update_user(self, user: BetaUser) -> bool:
        """Update beta user."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE beta_users SET
                    email = ?, name = ?, company = ?, use_case = ?, status = ?,
                    last_active = ?, usage_stats = ?, feedback_count = ?,
                    satisfaction_score = ?, notes = ?
                WHERE user_id = ?
            """, (
                user.email, user.name, user.company, user.use_case, user.status.value,
                user.last_active.isoformat() if user.last_active else None,
                json.dumps(user.usage_stats or {}), user.feedback_count,
                user.satisfaction_score, user.notes, user.user_id
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating user {user.user_id}: {e}")
            return False
    
    def add_feedback(self, feedback: FeedbackItem) -> bool:
        """Add feedback item."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO feedback (
                    feedback_id, user_id, feedback_type, priority, title, description,
                    steps_to_reproduce, expected_behavior, actual_behavior,
                    environment_info, attachments, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                feedback.feedback_id, feedback.user_id, feedback.feedback_type.value,
                feedback.priority.value, feedback.title, feedback.description,
                feedback.steps_to_reproduce, feedback.expected_behavior,
                feedback.actual_behavior, json.dumps(feedback.environment_info or {}),
                json.dumps(feedback.attachments or []), feedback.status,
                feedback.created_at.isoformat()
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error adding feedback {feedback.feedback_id}: {e}")
            return False
    
    def get_metrics(self) -> BetaMetrics:
        """Get beta program metrics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total users
            cursor.execute("SELECT COUNT(*) FROM beta_users")
            total_users = cursor.fetchone()[0]
            
            # Active users (active in last 7 days)
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute("SELECT COUNT(*) FROM beta_users WHERE last_active > ?", (week_ago,))
            active_users = cursor.fetchone()[0]
            
            # Feedback items
            cursor.execute("SELECT COUNT(*) FROM feedback")
            feedback_items = cursor.fetchone()[0]
            
            # Critical issues
            cursor.execute("SELECT COUNT(*) FROM feedback WHERE priority = 'critical' AND status != 'resolved'")
            critical_issues = cursor.fetchone()[0]
            
            # Average satisfaction
            cursor.execute("SELECT AVG(satisfaction_score) FROM beta_users WHERE satisfaction_score IS NOT NULL")
            avg_satisfaction = cursor.fetchone()[0] or 0.0
            
            conn.close()
            
            return BetaMetrics(
                total_users=total_users,
                active_users=active_users,
                feedback_items=feedback_items,
                critical_issues=critical_issues,
                average_satisfaction=avg_satisfaction,
                api_usage_total=0,  # Would be calculated from usage_tracking
                feature_adoption_rates={},  # Would be calculated from usage patterns
                churn_rate=0.0,  # Would be calculated from inactive users
                graduation_rate=0.0  # Would be calculated from graduated users
            )
            
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return BetaMetrics(0, 0, 0, 0, 0.0, 0, {}, 0.0, 0.0)


class NotificationService:
    """Email and notification service for beta program."""
    
    def __init__(self, 
                 smtp_server: str = "smtp.gmail.com",
                 smtp_port: int = 587,
                 smtp_username: str = "",
                 smtp_password: str = "",
                 from_email: str = "beta@mothership-ai.com"):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.from_email = from_email
    
    async def send_welcome_email(self, user: BetaUser) -> bool:
        """Send welcome email to new beta user."""
        try:
            subject = "Welcome to AgentGuard Beta Program!"
            
            html_content = f"""
            <html>
            <body>
                <h2>Welcome to AgentGuard Beta, {user.name}!</h2>
                
                <p>Thank you for joining our beta program. We're excited to have you test our AI hallucination detection platform.</p>
                
                <h3>Getting Started</h3>
                <ul>
                    <li><strong>API Key:</strong> {user.api_key}</li>
                    <li><strong>Documentation:</strong> <a href="https://docs.agentguard.ai">docs.agentguard.ai</a></li>
                    <li><strong>Dashboard:</strong> <a href="https://watcher.mothership-ai.com">watcher.mothership-ai.com</a></li>
                </ul>
                
                <h3>What's Next?</h3>
                <ol>
                    <li>Explore the API documentation</li>
                    <li>Try the interactive examples</li>
                    <li>Integrate with your use case: {user.use_case}</li>
                    <li>Share your feedback with us</li>
                </ol>
                
                <h3>Support</h3>
                <p>Need help? We're here for you:</p>
                <ul>
                    <li>Email: beta-info@mothership-ai.com</li>
                    <li>Discord: <a href="https://discord.gg/agentguard">Join our community</a></li>
                    <li>Feedback: Use the feedback form in your dashboard</li>
                </ul>
                
                <p>Happy testing!</p>
                <p>The AgentGuard Team</p>
            </body>
            </html>
            """
            
            return await self._send_email(user.email, subject, html_content)
            
        except Exception as e:
            logger.error(f"Error sending welcome email to {user.email}: {e}")
            return False
    
    async def send_feedback_confirmation(self, user: BetaUser, feedback: FeedbackItem) -> bool:
        """Send feedback confirmation email."""
        try:
            subject = f"Feedback Received: {feedback.title}"
            
            html_content = f"""
            <html>
            <body>
                <h2>Thank you for your feedback, {user.name}!</h2>
                
                <p>We've received your feedback and our team will review it shortly.</p>
                
                <h3>Feedback Details</h3>
                <ul>
                    <li><strong>ID:</strong> {feedback.feedback_id}</li>
                    <li><strong>Type:</strong> {feedback.feedback_type.value.replace('_', ' ').title()}</li>
                    <li><strong>Priority:</strong> {feedback.priority.value.title()}</li>
                    <li><strong>Title:</strong> {feedback.title}</li>
                </ul>
                
                <p>You can track the status of your feedback in your dashboard.</p>
                
                <p>Thank you for helping us improve AgentGuard!</p>
                <p>The AgentGuard Team</p>
            </body>
            </html>
            """
            
            return await self._send_email(user.email, subject, html_content)
            
        except Exception as e:
            logger.error(f"Error sending feedback confirmation to {user.email}: {e}")
            return False
    
    async def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email using SMTP."""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False


class BetaProgramManager:
    """
    Main beta program management service.
    
    Handles user onboarding, feedback collection, metrics tracking,
    and program administration.
    """
    
    def __init__(self, 
                 db_path: str = "beta_program.db",
                 notification_config: Optional[Dict[str, str]] = None):
        """
        Initialize beta program manager.
        
        Args:
            db_path: Path to SQLite database
            notification_config: Email configuration
        """
        self.database = BetaDatabase(db_path)
        
        # Initialize notification service
        notification_config = notification_config or {}
        self.notifications = NotificationService(**notification_config)
        
        # Program configuration
        self.max_beta_users = 100
        self.auto_approval = False
        self.graduation_criteria = {
            'min_usage_days': 30,
            'min_api_calls': 1000,
            'min_satisfaction': 4.0
        }
        
        logger.info("Beta program manager initialized")
    
    async def apply_for_beta(self, 
                           email: str,
                           name: str,
                           company: str,
                           use_case: str) -> Dict[str, Any]:
        """
        Process beta program application.
        
        Args:
            email: User email
            name: User name
            company: User company
            use_case: Intended use case
            
        Returns:
            Application result
        """
        try:
            # Check if user already exists
            existing_users = self._get_users_by_email(email)
            if existing_users:
                return {
                    'success': False,
                    'message': 'Email already registered for beta program',
                    'user_id': existing_users[0].user_id
                }
            
            # Check capacity
            metrics = self.database.get_metrics()
            if metrics.total_users >= self.max_beta_users:
                return {
                    'success': False,
                    'message': 'Beta program is currently at capacity',
                    'waitlist': True
                }
            
            # Create new user
            user_id = str(uuid.uuid4())
            api_key = f"ag_beta_{uuid.uuid4().hex[:16]}"
            
            status = BetaUserStatus.APPROVED if self.auto_approval else BetaUserStatus.APPLIED
            
            user = BetaUser(
                user_id=user_id,
                email=email,
                name=name,
                company=company,
                use_case=use_case,
                status=status,
                signup_date=datetime.now(),
                api_key=api_key if status == BetaUserStatus.APPROVED else None
            )
            
            # Add to database
            if self.database.add_user(user):
                # Send welcome email if approved
                if status == BetaUserStatus.APPROVED:
                    await self.notifications.send_welcome_email(user)
                
                return {
                    'success': True,
                    'message': 'Application submitted successfully',
                    'user_id': user_id,
                    'status': status.value,
                    'api_key': api_key if status == BetaUserStatus.APPROVED else None
                }
            else:
                return {
                    'success': False,
                    'message': 'Error processing application'
                }
                
        except Exception as e:
            logger.error(f"Beta application error: {e}")
            return {
                'success': False,
                'message': 'Internal error processing application'
            }
    
    async def approve_user(self, user_id: str) -> Dict[str, Any]:
        """Approve beta user and send welcome email."""
        try:
            user = self.database.get_user(user_id)
            if not user:
                return {'success': False, 'message': 'User not found'}
            
            if user.status != BetaUserStatus.APPLIED:
                return {'success': False, 'message': 'User not in applied status'}
            
            # Update user status and generate API key
            user.status = BetaUserStatus.APPROVED
            user.api_key = f"ag_beta_{uuid.uuid4().hex[:16]}"
            
            if self.database.update_user(user):
                # Send welcome email
                await self.notifications.send_welcome_email(user)
                
                return {
                    'success': True,
                    'message': 'User approved successfully',
                    'api_key': user.api_key
                }
            else:
                return {'success': False, 'message': 'Error updating user'}
                
        except Exception as e:
            logger.error(f"User approval error: {e}")
            return {'success': False, 'message': 'Internal error'}
    
    async def submit_feedback(self, 
                            user_id: str,
                            feedback_type: str,
                            priority: str,
                            title: str,
                            description: str,
                            **kwargs) -> Dict[str, Any]:
        """
        Submit user feedback.
        
        Args:
            user_id: Beta user ID
            feedback_type: Type of feedback
            priority: Priority level
            title: Feedback title
            description: Detailed description
            **kwargs: Additional feedback fields
            
        Returns:
            Submission result
        """
        try:
            user = self.database.get_user(user_id)
            if not user:
                return {'success': False, 'message': 'User not found'}
            
            # Create feedback item
            feedback = FeedbackItem(
                feedback_id=str(uuid.uuid4()),
                user_id=user_id,
                feedback_type=FeedbackType(feedback_type),
                priority=FeedbackPriority(priority),
                title=title,
                description=description,
                steps_to_reproduce=kwargs.get('steps_to_reproduce'),
                expected_behavior=kwargs.get('expected_behavior'),
                actual_behavior=kwargs.get('actual_behavior'),
                environment_info=kwargs.get('environment_info', {}),
                created_at=datetime.now()
            )
            
            # Add to database
            if self.database.add_feedback(feedback):
                # Update user feedback count
                user.feedback_count += 1
                self.database.update_user(user)
                
                # Send confirmation email
                await self.notifications.send_feedback_confirmation(user, feedback)
                
                return {
                    'success': True,
                    'message': 'Feedback submitted successfully',
                    'feedback_id': feedback.feedback_id
                }
            else:
                return {'success': False, 'message': 'Error saving feedback'}
                
        except Exception as e:
            logger.error(f"Feedback submission error: {e}")
            return {'success': False, 'message': 'Internal error'}
    
    def get_program_metrics(self) -> Dict[str, Any]:
        """Get comprehensive beta program metrics."""
        try:
            metrics = self.database.get_metrics()
            
            return {
                'program_status': {
                    'total_users': metrics.total_users,
                    'active_users': metrics.active_users,
                    'capacity': self.max_beta_users,
                    'utilization': metrics.total_users / self.max_beta_users * 100
                },
                'engagement': {
                    'feedback_items': metrics.feedback_items,
                    'critical_issues': metrics.critical_issues,
                    'average_satisfaction': metrics.average_satisfaction,
                    'active_user_rate': metrics.active_users / metrics.total_users * 100 if metrics.total_users > 0 else 0
                },
                'usage': {
                    'api_usage_total': metrics.api_usage_total,
                    'feature_adoption_rates': metrics.feature_adoption_rates
                },
                'retention': {
                    'churn_rate': metrics.churn_rate,
                    'graduation_rate': metrics.graduation_rate
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Metrics error: {e}")
            return {'error': str(e)}
    
    def _get_users_by_email(self, email: str) -> List[BetaUser]:
        """Get users by email address."""
        try:
            conn = sqlite3.connect(self.database.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM beta_users WHERE email = ?", (email,))
            rows = cursor.fetchall()
            conn.close()
            
            users = []
            for row in rows:
                user = BetaUser(
                    user_id=row[0],
                    email=row[1],
                    name=row[2],
                    company=row[3],
                    use_case=row[4],
                    status=BetaUserStatus(row[5]),
                    signup_date=datetime.fromisoformat(row[6]),
                    last_active=datetime.fromisoformat(row[7]) if row[7] else None,
                    api_key=row[8],
                    usage_stats=json.loads(row[9]) if row[9] else {},
                    feedback_count=row[10],
                    satisfaction_score=row[11],
                    notes=row[12] or ""
                )
                users.append(user)
            
            return users
            
        except Exception as e:
            logger.error(f"Error getting users by email {email}: {e}")
            return []


# Global beta program manager instance
_beta_program_manager = None


def get_beta_program_manager() -> BetaProgramManager:
    """Get or create beta program manager instance."""
    global _beta_program_manager
    if _beta_program_manager is None:
        _beta_program_manager = BetaProgramManager()
    return _beta_program_manager


if __name__ == "__main__":
    # Example usage
    async def test_beta_program():
        manager = BetaProgramManager()
        
        # Test application
        result = await manager.apply_for_beta(
            email="test@example.com",
            name="Test User",
            company="Test Company",
            use_case="Testing hallucination detection"
        )
        print(f"Application result: {result}")
        
        # Get metrics
        metrics = manager.get_program_metrics()
        print(f"Program metrics: {json.dumps(metrics, indent=2)}")
    
    # Run test
    # asyncio.run(test_beta_program())
