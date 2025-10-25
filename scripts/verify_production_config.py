#!/usr/bin/env python3
"""
Verify Production Configuration
Checks that all required environment variables and services are properly configured
"""

import os
import sys
import asyncio
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass
import requests
from urllib.parse import urlparse

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ConfigCheck:
    """Configuration check result"""
    name: str
    status: str  # 'pass', 'fail', 'warn'
    message: str
    critical: bool = True


class ProductionConfigVerifier:
    """Verify production configuration"""
    
    def __init__(self):
        self.checks: List[ConfigCheck] = []
        self.critical_failures = 0
        self.warnings = 0
    
    def add_check(self, name: str, status: str, message: str, critical: bool = True):
        """Add a configuration check result"""
        check = ConfigCheck(name, status, message, critical)
        self.checks.append(check)
        
        if status == 'fail' and critical:
            self.critical_failures += 1
        elif status == 'warn':
            self.warnings += 1
    
    def check_env_var(self, var_name: str, required: bool = True, secret: bool = False) -> bool:
        """Check if environment variable is set"""
        value = os.getenv(var_name)
        
        if value:
            display_value = "***" if secret else value[:20] + "..." if len(value) > 20 else value
            self.add_check(
                var_name,
                'pass',
                f"Set: {display_value}",
                critical=required
            )
            return True
        else:
            status = 'fail' if required else 'warn'
            self.add_check(
                var_name,
                status,
                "Not set" + (" (REQUIRED)" if required else " (optional)"),
                critical=required
            )
            return False
    
    def check_database_connection(self) -> bool:
        """Check database connectivity"""
        try:
            from sqlalchemy import create_engine
            
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                self.add_check('Database', 'fail', 'DATABASE_URL not set', critical=True)
                return False
            
            engine = create_engine(db_url, pool_pre_ping=True)
            with engine.connect() as conn:
                result = conn.execute("SELECT 1")
                result.fetchone()
            
            self.add_check('Database', 'pass', 'Connection successful', critical=True)
            return True
            
        except Exception as e:
            self.add_check('Database', 'fail', f'Connection failed: {str(e)}', critical=True)
            return False
    
    def check_redis_connection(self) -> bool:
        """Check Redis connectivity"""
        try:
            import redis
            
            redis_url = os.getenv('REDIS_URL')
            if not redis_url:
                self.add_check('Redis', 'warn', 'REDIS_URL not set (caching disabled)', critical=False)
                return False
            
            r = redis.from_url(redis_url)
            r.ping()
            
            self.add_check('Redis', 'pass', 'Connection successful', critical=False)
            return True
            
        except Exception as e:
            self.add_check('Redis', 'warn', f'Connection failed: {str(e)}', critical=False)
            return False
    
    def check_api_keys(self) -> bool:
        """Check AI API keys"""
        all_valid = True
        
        # Check Claude API key
        claude_key = os.getenv('CLAUDE_API_KEY')
        if claude_key:
            try:
                # Simple validation - check format
                if claude_key.startswith('sk-ant-api'):
                    self.add_check('Claude API', 'pass', 'Key format valid', critical=True)
                else:
                    self.add_check('Claude API', 'warn', 'Key format unusual', critical=True)
                    all_valid = False
            except Exception as e:
                self.add_check('Claude API', 'fail', f'Validation failed: {str(e)}', critical=True)
                all_valid = False
        else:
            self.add_check('Claude API', 'fail', 'CLAUDE_API_KEY not set', critical=True)
            all_valid = False
        
        # Check OpenAI API key (optional)
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            if openai_key.startswith('sk-'):
                self.add_check('OpenAI API', 'pass', 'Key format valid', critical=False)
            else:
                self.add_check('OpenAI API', 'warn', 'Key format unusual', critical=False)
        else:
            self.add_check('OpenAI API', 'warn', 'Not set (optional)', critical=False)
        
        return all_valid
    
    def check_security_config(self) -> bool:
        """Check security configuration"""
        all_valid = True
        
        # Check JWT secret
        jwt_secret = os.getenv('JWT_SECRET_KEY')
        if jwt_secret:
            if len(jwt_secret) >= 32:
                self.add_check('JWT Secret', 'pass', f'Length: {len(jwt_secret)} chars', critical=True)
            else:
                self.add_check('JWT Secret', 'fail', 'Too short (min 32 chars)', critical=True)
                all_valid = False
        else:
            self.add_check('JWT Secret', 'fail', 'JWT_SECRET_KEY not set', critical=True)
            all_valid = False
        
        # Check API key salt
        api_salt = os.getenv('API_KEY_SALT')
        if api_salt:
            if len(api_salt) >= 32:
                self.add_check('API Key Salt', 'pass', f'Length: {len(api_salt)} chars', critical=True)
            else:
                self.add_check('API Key Salt', 'fail', 'Too short (min 32 chars)', critical=True)
                all_valid = False
        else:
            self.add_check('API Key Salt', 'fail', 'API_KEY_SALT not set', critical=True)
            all_valid = False
        
        # Check CORS origins
        cors_origins = os.getenv('CORS_ORIGINS')
        if cors_origins:
            origins = [o.strip() for o in cors_origins.split(',')]
            if all(o.startswith('https://') or o == 'http://localhost' for o in origins):
                self.add_check('CORS Origins', 'pass', f'{len(origins)} origins configured', critical=True)
            else:
                self.add_check('CORS Origins', 'warn', 'Some origins not HTTPS', critical=True)
        else:
            self.add_check('CORS Origins', 'fail', 'CORS_ORIGINS not set', critical=True)
            all_valid = False
        
        return all_valid
    
    def check_monitoring(self) -> bool:
        """Check monitoring configuration"""
        # Check Sentry
        sentry_dsn = os.getenv('SENTRY_DSN')
        if sentry_dsn:
            self.add_check('Sentry', 'pass', 'DSN configured', critical=False)
        else:
            self.add_check('Sentry', 'warn', 'Not configured (recommended)', critical=False)
        
        # Check environment
        env = os.getenv('PYTHON_ENV') or os.getenv('NODE_ENV')
        if env == 'production':
            self.add_check('Environment', 'pass', 'Set to production', critical=True)
        else:
            self.add_check('Environment', 'warn', f'Set to: {env or "not set"}', critical=True)
        
        return True
    
    def check_urls(self) -> bool:
        """Check URL configuration"""
        all_valid = True
        
        urls = {
            'APP_URL': True,
            'API_URL': True,
            'FRONTEND_URL': True
        }
        
        for url_var, required in urls.items():
            url = os.getenv(url_var)
            if url:
                parsed = urlparse(url)
                if parsed.scheme == 'https':
                    self.add_check(url_var, 'pass', url, critical=required)
                else:
                    self.add_check(url_var, 'warn', f'{url} (not HTTPS)', critical=required)
                    if required:
                        all_valid = False
            else:
                status = 'fail' if required else 'warn'
                self.add_check(url_var, status, 'Not set', critical=required)
                if required:
                    all_valid = False
        
        return all_valid
    
    def check_stripe(self) -> bool:
        """Check Stripe configuration"""
        stripe_secret = os.getenv('STRIPE_SECRET_KEY')
        stripe_publishable = os.getenv('STRIPE_PUBLISHABLE_KEY')
        
        if stripe_secret and stripe_publishable:
            # Check if using live keys
            is_live = stripe_secret.startswith('sk_live_')
            status = 'pass' if is_live else 'warn'
            message = 'Live keys configured' if is_live else 'Test keys (not production)'
            self.add_check('Stripe', status, message, critical=False)
        else:
            self.add_check('Stripe', 'warn', 'Not fully configured', critical=False)
        
        return True
    
    def check_email(self) -> bool:
        """Check email configuration"""
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_from = os.getenv('SMTP_FROM_EMAIL')
        
        if smtp_server and smtp_from:
            self.add_check('Email', 'pass', f'SMTP configured: {smtp_server}', critical=False)
        else:
            self.add_check('Email', 'warn', 'SMTP not fully configured', critical=False)
        
        return True
    
    def run_all_checks(self):
        """Run all configuration checks"""
        logger.info("=" * 70)
        logger.info("AGENTGUARD PRODUCTION CONFIGURATION VERIFICATION")
        logger.info("=" * 70)
        logger.info("")
        
        # Core configuration
        logger.info("📋 Checking Core Configuration...")
        self.check_env_var('PYTHON_ENV', required=True)
        self.check_env_var('LOG_LEVEL', required=False)
        
        # URLs
        logger.info("\n🌐 Checking URLs...")
        self.check_urls()
        
        # AI APIs
        logger.info("\n🤖 Checking AI API Keys...")
        self.check_api_keys()
        
        # Database
        logger.info("\n🗄️  Checking Database...")
        self.check_database_connection()
        
        # Redis
        logger.info("\n⚡ Checking Redis...")
        self.check_redis_connection()
        
        # Security
        logger.info("\n🔒 Checking Security Configuration...")
        self.check_security_config()
        
        # Monitoring
        logger.info("\n📊 Checking Monitoring...")
        self.check_monitoring()
        
        # Payments
        logger.info("\n💳 Checking Stripe...")
        self.check_stripe()
        
        # Email
        logger.info("\n📧 Checking Email...")
        self.check_email()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print verification summary"""
        logger.info("\n" + "=" * 70)
        logger.info("VERIFICATION SUMMARY")
        logger.info("=" * 70)
        
        # Group by status
        passed = [c for c in self.checks if c.status == 'pass']
        failed = [c for c in self.checks if c.status == 'fail']
        warned = [c for c in self.checks if c.status == 'warn']
        
        logger.info(f"\n✅ Passed: {len(passed)}")
        logger.info(f"❌ Failed: {len(failed)}")
        logger.info(f"⚠️  Warnings: {len(warned)}")
        
        # Show failures
        if failed:
            logger.info("\n❌ FAILURES:")
            for check in failed:
                critical_marker = " (CRITICAL)" if check.critical else ""
                logger.info(f"   • {check.name}: {check.message}{critical_marker}")
        
        # Show warnings
        if warned:
            logger.info("\n⚠️  WARNINGS:")
            for check in warned:
                logger.info(f"   • {check.name}: {check.message}")
        
        # Final verdict
        logger.info("\n" + "=" * 70)
        if self.critical_failures == 0:
            logger.info("✅ PRODUCTION READY - All critical checks passed!")
            if self.warnings > 0:
                logger.info(f"⚠️  Note: {self.warnings} warnings should be addressed")
            logger.info("=" * 70)
            return 0
        else:
            logger.info(f"❌ NOT PRODUCTION READY - {self.critical_failures} critical failures")
            logger.info("=" * 70)
            return 1


def main():
    """Main execution"""
    verifier = ProductionConfigVerifier()
    verifier.run_all_checks()
    sys.exit(verifier.critical_failures)


if __name__ == "__main__":
    main()

