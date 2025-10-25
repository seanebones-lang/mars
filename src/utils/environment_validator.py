"""
Environment Variable Validator
Ensures all required environment variables are set and valid before system startup.
Part of P0-Critical production readiness requirements.
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class EnvironmentLevel(Enum):
    """Environment levels with different requirements."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class EnvVarRequirement:
    """Defines requirements for an environment variable."""
    name: str
    required: bool
    description: str
    validator: Optional[callable] = None
    default: Optional[str] = None
    sensitive: bool = False


class EnvironmentValidator:
    """Validates environment variables for production readiness."""
    
    # Critical environment variables (P0)
    CRITICAL_VARS = [
        EnvVarRequirement(
            name="CLAUDE_API_KEY",
            required=True,
            description="Anthropic Claude API key (required for all AI operations)",
            validator=lambda x: x.startswith("sk-ant-api03-"),
            sensitive=True
        ),
        EnvVarRequirement(
            name="ENVIRONMENT",
            required=True,
            description="Environment level (development, staging, production)",
            validator=lambda x: x in ["development", "staging", "production"],
            default="development"
        ),
    ]
    
    # High priority environment variables (P1)
    HIGH_PRIORITY_VARS = [
        EnvVarRequirement(
            name="DATABASE_URL",
            required=False,
            description="PostgreSQL connection URL (falls back to SQLite if not set)",
            validator=lambda x: x.startswith("postgresql://") or x.startswith("postgres://")
        ),
        EnvVarRequirement(
            name="REDIS_URL",
            required=False,
            description="Redis connection URL (falls back to in-memory cache if not set)",
            validator=lambda x: x.startswith("redis://") or x.startswith("rediss://")
        ),
        EnvVarRequirement(
            name="STRIPE_SECRET_KEY",
            required=False,
            description="Stripe secret key for payment processing",
            validator=lambda x: x.startswith("sk_"),
            sensitive=True
        ),
    ]
    
    # Optional environment variables (P2)
    OPTIONAL_VARS = [
        EnvVarRequirement(
            name="OPENAI_API_KEY",
            required=False,
            description="OpenAI API key for multi-model consensus",
            validator=lambda x: x.startswith("sk-"),
            sensitive=True
        ),
        EnvVarRequirement(
            name="GOOGLE_API_KEY",
            required=False,
            description="Google Gemini API key for multimodal detection",
            sensitive=True
        ),
        EnvVarRequirement(
            name="SENTRY_DSN",
            required=False,
            description="Sentry DSN for error tracking",
            validator=lambda x: x.startswith("https://")
        ),
        EnvVarRequirement(
            name="LOG_LEVEL",
            required=False,
            description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
            validator=lambda x: x.upper() in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            default="INFO"
        ),
    ]
    
    def __init__(self, environment: Optional[str] = None):
        """Initialize validator with environment level."""
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        
    def validate_var(self, requirement: EnvVarRequirement) -> Tuple[bool, Optional[str]]:
        """
        Validate a single environment variable.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        value = os.getenv(requirement.name)
        
        # Check if required variable is missing
        if requirement.required and not value:
            if requirement.default:
                os.environ[requirement.name] = requirement.default
                return True, None
            return False, f"Required environment variable '{requirement.name}' is not set"
        
        # If not required and not set, that's okay
        if not value:
            return True, None
        
        # Validate value if validator provided
        if requirement.validator:
            try:
                if not requirement.validator(value):
                    return False, f"Environment variable '{requirement.name}' has invalid format"
            except Exception as e:
                return False, f"Error validating '{requirement.name}': {str(e)}"
        
        return True, None
    
    def validate_all(self) -> bool:
        """
        Validate all environment variables.
        
        Returns:
            True if all validations pass, False otherwise
        """
        all_valid = True
        
        logger.info(f"Validating environment variables for {self.environment} environment")
        
        # Validate critical variables
        logger.info("Checking critical environment variables (P0)...")
        for req in self.CRITICAL_VARS:
            is_valid, error = self.validate_var(req)
            if not is_valid:
                self.errors.append(f"[CRITICAL] {error}: {req.description}")
                all_valid = False
            else:
                value = os.getenv(req.name)
                if value:
                    display_value = "***" if req.sensitive else value
                    self.info.append(f"✓ {req.name}: {display_value}")
        
        # Validate high priority variables
        logger.info("Checking high priority environment variables (P1)...")
        for req in self.HIGH_PRIORITY_VARS:
            is_valid, error = self.validate_var(req)
            value = os.getenv(req.name)
            if not is_valid:
                self.warnings.append(f"[WARNING] {error}: {req.description}")
            elif value:
                display_value = "***" if req.sensitive else value[:50]
                self.info.append(f"✓ {req.name}: {display_value}")
            else:
                self.warnings.append(f"[OPTIONAL] {req.name} not set: {req.description}")
        
        # Validate optional variables
        logger.info("Checking optional environment variables (P2)...")
        for req in self.OPTIONAL_VARS:
            is_valid, error = self.validate_var(req)
            value = os.getenv(req.name)
            if not is_valid:
                self.warnings.append(f"[WARNING] {error}: {req.description}")
            elif value:
                display_value = "***" if req.sensitive else value
                self.info.append(f"✓ {req.name}: {display_value}")
        
        return all_valid
    
    def print_report(self):
        """Print validation report."""
        print("\n" + "=" * 80)
        print("ENVIRONMENT VALIDATION REPORT")
        print("=" * 80)
        print(f"Environment: {self.environment}")
        print(f"Timestamp: {os.popen('date').read().strip()}")
        print("=" * 80)
        
        if self.errors:
            print("\n❌ CRITICAL ERRORS (Must fix before startup):")
            for error in self.errors:
                print(f"  {error}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS (Recommended to fix):")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if self.info:
            print("\n✓ CONFIGURED:")
            for info in self.info:
                print(f"  {info}")
        
        print("\n" + "=" * 80)
        
        if self.errors:
            print("❌ VALIDATION FAILED - Cannot start system")
            print("=" * 80)
            return False
        elif self.warnings:
            print("⚠️  VALIDATION PASSED WITH WARNINGS")
            print("=" * 80)
            return True
        else:
            print("✅ VALIDATION PASSED - All systems go!")
            print("=" * 80)
            return True
    
    def validate_and_exit_on_failure(self):
        """Validate environment and exit if critical errors found."""
        is_valid = self.validate_all()
        success = self.print_report()
        
        if not success:
            logger.critical("Environment validation failed - exiting")
            sys.exit(1)
        
        return success


def validate_environment() -> bool:
    """
    Convenience function to validate environment.
    
    Returns:
        True if validation passes, exits with code 1 if critical errors
    """
    validator = EnvironmentValidator()
    return validator.validate_and_exit_on_failure()


if __name__ == "__main__":
    # Allow running as standalone script
    validate_environment()

