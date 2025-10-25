"""
Monetization Service
Implements freemium model with query limits, Stripe integration, and BYOK pricing.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import hashlib
import secrets

logger = logging.getLogger(__name__)


class SubscriptionTier(Enum):
    """Subscription tier definitions."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    BYOK = "byok"  # Bring Your Own Key


class PricingModel(Enum):
    """Pricing model types."""
    SUBSCRIPTION = "subscription"
    PAY_PER_USE = "pay_per_use"
    BYOK_PLATFORM_FEE = "byok_platform_fee"


class MonetizationService:
    """
    Handles all monetization aspects including:
    - Freemium model with 3-query limit
    - Stripe payment processing
    - BYOK (Bring Your Own Key) pricing
    - Usage tracking and billing
    - Device fingerprinting for abuse prevention
    """
    
    def __init__(self):
        self.stripe_secret_key = None  # Set from environment
        self.pricing_config = self._load_pricing_config()
        self.usage_db = {}  # In production, use Redis/PostgreSQL
        self.subscription_db = {}
        self.device_fingerprints = {}
        
    def _load_pricing_config(self) -> Dict[str, Any]:
        """Load pricing configuration."""
        return {
            "tiers": {
                SubscriptionTier.FREE.value: {
                    "name": "Free",
                    "price_monthly": 0,
                    "queries_per_month": 100,
                    "agents_limit": 1,
                    "api_access": True,
                    "support_level": "community",
                    "features": [
                        "Basic hallucination detection",
                        "Web interface access",
                        "API access (rate limited)",
                        "100 queries per month",
                        "Community support",
                        "Prompt injection detection",
                        "Basic safety checks"
                    ]
                },
                SubscriptionTier.PRO.value: {
                    "name": "Pro",
                    "price_monthly": 29,
                    "queries_per_month": 1000,
                    "agents_limit": 10,
                    "api_access": True,
                    "support_level": "email",
                    "features": [
                        "Advanced multi-model detection",
                        "Agent Console & deployment",
                        "API access & webhooks",
                        "Real-time monitoring",
                        "Email support"
                    ]
                },
                SubscriptionTier.ENTERPRISE.value: {
                    "name": "Enterprise",
                    "price_monthly": 299,
                    "queries_per_month": 50000,
                    "agents_limit": 100,
                    "api_access": True,
                    "support_level": "priority",
                    "features": [
                        "All Pro features",
                        "Custom safety rules",
                        "SSO integration",
                        "Compliance reporting",
                        "Priority support",
                        "Custom deployment"
                    ]
                },
                SubscriptionTier.BYOK.value: {
                    "name": "Bring Your Own Key",
                    "price_monthly": 0,
                    "platform_fee_per_query": 0.01,  # $0.01 per query
                    "queries_per_month": -1,  # Unlimited
                    "agents_limit": -1,  # Unlimited
                    "api_access": True,
                    "support_level": "email",
                    "features": [
                        "Use your own API keys",
                        "Pay only platform fees",
                        "Unlimited queries",
                        "All Pro features",
                        "Cost transparency"
                    ]
                }
            },
            "stripe": {
                "price_ids": {
                    "pro_monthly": "price_pro_monthly_2025",
                    "enterprise_monthly": "price_enterprise_monthly_2025"
                }
            }
        }
    
    async def check_usage_limits(self, user_id: str, operation: str = "query") -> Dict[str, Any]:
        """
        Check if user has exceeded usage limits.
        
        Args:
            user_id: User identifier
            operation: Type of operation (query, agent_creation, api_call)
            
        Returns:
            Dict with limit check results
        """
        try:
            # Get user subscription
            subscription = await self.get_user_subscription(user_id)
            tier_config = self.pricing_config["tiers"][subscription["tier"]]
            
            # Get current usage
            usage = await self.get_user_usage(user_id)
            current_month = datetime.utcnow().strftime("%Y-%m")
            monthly_usage = usage.get(current_month, {})
            
            # Check specific limits
            if operation == "query":
                limit = tier_config["queries_per_month"]
                used = monthly_usage.get("queries", 0)
                
                if limit > 0 and used >= limit:
                    return {
                        "allowed": False,
                        "reason": "monthly_query_limit_exceeded",
                        "limit": limit,
                        "used": used,
                        "reset_date": self._get_next_month_start().isoformat()
                    }
            
            elif operation == "agent_creation":
                limit = tier_config["agents_limit"]
                used = len(await self.get_user_agents(user_id))
                
                if limit > 0 and used >= limit:
                    return {
                        "allowed": False,
                        "reason": "agent_limit_exceeded",
                        "limit": limit,
                        "used": used,
                        "upgrade_required": True
                    }
            
            elif operation == "api_call":
                if not tier_config["api_access"]:
                    return {
                        "allowed": False,
                        "reason": "api_access_not_included",
                        "upgrade_required": True
                    }
            
            return {
                "allowed": True,
                "tier": subscription["tier"],
                "usage": monthly_usage
            }
            
        except Exception as e:
            logger.error(f"Error checking usage limits for user {user_id}: {e}")
            # Fail open for now, but log the error
            return {"allowed": True, "error": str(e)}
    
    async def record_usage(self, user_id: str, operation: str, metadata: Dict = None) -> None:
        """
        Record usage for billing and limit tracking.
        
        Args:
            user_id: User identifier
            operation: Type of operation
            metadata: Additional metadata about the operation
        """
        try:
            current_month = datetime.utcnow().strftime("%Y-%m")
            
            if user_id not in self.usage_db:
                self.usage_db[user_id] = {}
            
            if current_month not in self.usage_db[user_id]:
                self.usage_db[user_id][current_month] = {
                    "queries": 0,
                    "api_calls": 0,
                    "agents_created": 0,
                    "processing_time_ms": 0,
                    "operations": []
                }
            
            month_usage = self.usage_db[user_id][current_month]
            
            # Record the operation
            operation_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "operation": operation,
                "metadata": metadata or {}
            }
            
            month_usage["operations"].append(operation_record)
            
            # Update counters
            if operation == "query":
                month_usage["queries"] += 1
                if metadata and "processing_time_ms" in metadata:
                    month_usage["processing_time_ms"] += metadata["processing_time_ms"]
            elif operation == "api_call":
                month_usage["api_calls"] += 1
            elif operation == "agent_creation":
                month_usage["agents_created"] += 1
            
            logger.info(f"Recorded usage for user {user_id}: {operation}")
            
        except Exception as e:
            logger.error(f"Error recording usage for user {user_id}: {e}")
    
    async def get_user_subscription(self, user_id: str) -> Dict[str, Any]:
        """Get user's current subscription details."""
        if user_id not in self.subscription_db:
            # Default to free tier
            self.subscription_db[user_id] = {
                "tier": SubscriptionTier.FREE.value,
                "status": "active",
                "created_at": datetime.utcnow().isoformat(),
                "stripe_subscription_id": None,
                "byok_keys": {}
            }
        
        return self.subscription_db[user_id]
    
    async def get_user_usage(self, user_id: str) -> Dict[str, Any]:
        """Get user's usage statistics."""
        return self.usage_db.get(user_id, {})
    
    async def get_user_agents(self, user_id: str) -> List[str]:
        """Get list of user's agent IDs."""
        # Mock implementation - in production, query from database
        return [f"agent_{i}" for i in range(3)]  # Mock 3 agents
    
    async def create_stripe_checkout_session(
        self,
        user_id: str,
        tier: SubscriptionTier,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, str]:
        """
        Create Stripe checkout session for subscription upgrade.
        
        Args:
            user_id: User identifier
            tier: Target subscription tier
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
            
        Returns:
            Stripe checkout session details
        """
        try:
            # Mock Stripe integration
            # In production, use actual Stripe API
            
            tier_config = self.pricing_config["tiers"][tier.value]
            
            if tier == SubscriptionTier.FREE:
                raise ValueError("Cannot create checkout for free tier")
            
            if tier == SubscriptionTier.BYOK:
                # BYOK doesn't use Stripe subscriptions
                return await self._setup_byok_billing(user_id)
            
            # Mock checkout session
            session_id = f"cs_{secrets.token_urlsafe(32)}"
            
            checkout_session = {
                "id": session_id,
                "url": f"https://checkout.stripe.com/pay/{session_id}",
                "success_url": success_url,
                "cancel_url": cancel_url,
                "customer_email": f"user_{user_id}@example.com",
                "line_items": [
                    {
                        "price": self.pricing_config["stripe"]["price_ids"][f"{tier.value}_monthly"],
                        "quantity": 1
                    }
                ],
                "mode": "subscription",
                "metadata": {
                    "user_id": user_id,
                    "tier": tier.value
                }
            }
            
            logger.info(f"Created Stripe checkout session for user {user_id}: {tier.value}")
            return checkout_session
            
        except Exception as e:
            logger.error(f"Error creating Stripe checkout session: {e}")
            raise
    
    async def _setup_byok_billing(self, user_id: str) -> Dict[str, str]:
        """Set up BYOK billing configuration."""
        return {
            "setup_required": True,
            "instructions": "Please provide your API keys in the settings",
            "billing_model": "pay_per_query",
            "platform_fee": self.pricing_config["tiers"]["byok"]["platform_fee_per_query"]
        }
    
    async def handle_stripe_webhook(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Stripe webhook events.
        
        Args:
            event_data: Stripe webhook event data
            
        Returns:
            Processing result
        """
        try:
            event_type = event_data.get("type")
            
            if event_type == "checkout.session.completed":
                return await self._handle_checkout_completed(event_data["data"]["object"])
            elif event_type == "customer.subscription.updated":
                return await self._handle_subscription_updated(event_data["data"]["object"])
            elif event_type == "customer.subscription.deleted":
                return await self._handle_subscription_cancelled(event_data["data"]["object"])
            elif event_type == "invoice.payment_succeeded":
                return await self._handle_payment_succeeded(event_data["data"]["object"])
            elif event_type == "invoice.payment_failed":
                return await self._handle_payment_failed(event_data["data"]["object"])
            
            return {"status": "ignored", "event_type": event_type}
            
        except Exception as e:
            logger.error(f"Error handling Stripe webhook: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _handle_checkout_completed(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful checkout completion."""
        user_id = session["metadata"]["user_id"]
        tier = session["metadata"]["tier"]
        
        # Update user subscription
        self.subscription_db[user_id] = {
            "tier": tier,
            "status": "active",
            "stripe_subscription_id": session.get("subscription"),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Upgraded user {user_id} to {tier}")
        return {"status": "success", "user_id": user_id, "tier": tier}
    
    async def _handle_subscription_updated(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription updates."""
        # Find user by subscription ID and update
        for user_id, sub_data in self.subscription_db.items():
            if sub_data.get("stripe_subscription_id") == subscription["id"]:
                sub_data["status"] = subscription["status"]
                sub_data["updated_at"] = datetime.utcnow().isoformat()
                break
        
        return {"status": "success"}
    
    async def _handle_subscription_cancelled(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription cancellation."""
        # Find user and downgrade to free tier
        for user_id, sub_data in self.subscription_db.items():
            if sub_data.get("stripe_subscription_id") == subscription["id"]:
                sub_data["tier"] = SubscriptionTier.FREE.value
                sub_data["status"] = "cancelled"
                sub_data["updated_at"] = datetime.utcnow().isoformat()
                break
        
        return {"status": "success"}
    
    async def _handle_payment_succeeded(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment."""
        logger.info(f"Payment succeeded for invoice {invoice['id']}")
        return {"status": "success"}
    
    async def _handle_payment_failed(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment."""
        logger.warning(f"Payment failed for invoice {invoice['id']}")
        # Could implement retry logic or account suspension here
        return {"status": "payment_failed"}
    
    async def calculate_byok_costs(
        self,
        user_id: str,
        usage_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate costs for BYOK users.
        
        Args:
            user_id: User identifier
            usage_data: Usage statistics
            
        Returns:
            Cost breakdown
        """
        try:
            platform_fee_per_query = self.pricing_config["tiers"]["byok"]["platform_fee_per_query"]
            
            total_queries = sum(
                month_data.get("queries", 0) 
                for month_data in usage_data.values()
            )
            
            platform_fees = total_queries * platform_fee_per_query
            
            # Estimate API costs (user's own keys)
            estimated_api_costs = total_queries * 0.002  # Rough estimate
            
            return {
                "total_queries": total_queries,
                "platform_fees": platform_fees,
                "estimated_api_costs": estimated_api_costs,
                "total_estimated_cost": platform_fees + estimated_api_costs,
                "cost_breakdown": {
                    "platform_fee_per_query": platform_fee_per_query,
                    "estimated_api_cost_per_query": 0.002
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating BYOK costs: {e}")
            return {"error": str(e)}
    
    async def generate_device_fingerprint(self, request_data: Dict[str, Any]) -> str:
        """
        Generate device fingerprint for abuse prevention.
        
        Args:
            request_data: Request metadata (IP, User-Agent, etc.)
            
        Returns:
            Device fingerprint hash
        """
        try:
            # Combine various request attributes
            fingerprint_data = {
                "ip_address": request_data.get("ip_address", ""),
                "user_agent": request_data.get("user_agent", ""),
                "accept_language": request_data.get("accept_language", ""),
                "timezone": request_data.get("timezone", ""),
                "screen_resolution": request_data.get("screen_resolution", "")
            }
            
            # Create hash
            fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
            fingerprint_hash = hashlib.sha256(fingerprint_string.encode()).hexdigest()
            
            return fingerprint_hash[:16]  # Use first 16 characters
            
        except Exception as e:
            logger.error(f"Error generating device fingerprint: {e}")
            return "unknown"
    
    async def check_abuse_patterns(self, user_id: str, device_fingerprint: str) -> Dict[str, Any]:
        """
        Check for potential abuse patterns.
        
        Args:
            user_id: User identifier
            device_fingerprint: Device fingerprint
            
        Returns:
            Abuse check results
        """
        try:
            # Check for multiple free accounts from same device
            if device_fingerprint in self.device_fingerprints:
                existing_users = self.device_fingerprints[device_fingerprint]
                
                # Count free tier users from this device
                free_users = 0
                for existing_user_id in existing_users:
                    subscription = await self.get_user_subscription(existing_user_id)
                    if subscription["tier"] == SubscriptionTier.FREE.value:
                        free_users += 1
                
                if free_users >= 3:  # Allow max 3 free accounts per device
                    return {
                        "abuse_detected": True,
                        "reason": "multiple_free_accounts_same_device",
                        "action": "require_payment_method"
                    }
            else:
                self.device_fingerprints[device_fingerprint] = []
            
            # Add user to device fingerprint
            if user_id not in self.device_fingerprints[device_fingerprint]:
                self.device_fingerprints[device_fingerprint].append(user_id)
            
            return {"abuse_detected": False}
            
        except Exception as e:
            logger.error(f"Error checking abuse patterns: {e}")
            return {"abuse_detected": False, "error": str(e)}
    
    def _get_next_month_start(self) -> datetime:
        """Get the start of next month."""
        now = datetime.utcnow()
        if now.month == 12:
            return datetime(now.year + 1, 1, 1)
        else:
            return datetime(now.year, now.month + 1, 1)
    
    async def get_pricing_info(self) -> Dict[str, Any]:
        """Get current pricing information."""
        return {
            "tiers": self.pricing_config["tiers"],
            "currency": "USD",
            "billing_cycle": "monthly",
            "free_trial": {
                "available": True,
                "duration_days": 14,
                "tier": "pro"
            }
        }


# Global instance
_monetization_service = None

def get_monetization_service() -> MonetizationService:
    """Get the global monetization service instance."""
    global _monetization_service
    if _monetization_service is None:
        _monetization_service = MonetizationService()
    return _monetization_service
