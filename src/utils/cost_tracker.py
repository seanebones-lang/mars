"""
Cost Tracking and Monitoring
P1-1: Track external API costs and usage patterns
"""

import os
import time
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)


@dataclass
class APIUsage:
    """Track API usage and costs."""
    service: str
    endpoint: str
    tokens_used: int
    cost: float
    timestamp: datetime
    response_time: float
    success: bool
    customer_id: Optional[str] = None


class CostTracker:
    """
    Track costs for external API services.
    
    Services tracked:
    - Claude API (Anthropic)
    - OpenAI API (if used)
    - Stripe API
    """
    
    # Pricing (as of 2025)
    CLAUDE_PRICING = {
        "claude-sonnet-4-5-20250929": {
            "input": 0.003,   # $3 per million tokens
            "output": 0.015,  # $15 per million tokens
        },
        "claude-3-5-sonnet-20241022": {
            "input": 0.003,
            "output": 0.015,
        },
        "claude-3-opus-20240229": {
            "input": 0.015,
            "output": 0.075,
        },
    }
    
    OPENAI_PRICING = {
        "gpt-4": {
            "input": 0.03,
            "output": 0.06,
        },
        "gpt-3.5-turbo": {
            "input": 0.0005,
            "output": 0.0015,
        },
    }
    
    def __init__(self):
        """Initialize cost tracker."""
        self.usage_data: List[APIUsage] = []
        self.daily_totals: Dict[str, Dict] = defaultdict(lambda: {
            "requests": 0,
            "tokens": 0,
            "cost": 0.0,
            "errors": 0,
        })
        
        # Budget alerts
        self.daily_budget = float(os.getenv("DAILY_API_BUDGET", "100.0"))
        self.monthly_budget = float(os.getenv("MONTHLY_API_BUDGET", "3000.0"))
        
        # Alert thresholds
        self.alert_threshold = 0.8  # Alert at 80% of budget
        
        logger.info(f"Cost tracker initialized: Daily budget ${self.daily_budget}, Monthly budget ${self.monthly_budget}")
    
    def track_claude_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        response_time: float,
        success: bool = True,
        customer_id: Optional[str] = None
    ) -> float:
        """
        Track Claude API usage and calculate cost.
        
        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            response_time: Response time in seconds
            success: Whether the request succeeded
            customer_id: Optional customer ID
            
        Returns:
            Cost in USD
        """
        # Get pricing for model
        pricing = self.CLAUDE_PRICING.get(model, self.CLAUDE_PRICING["claude-sonnet-4-5-20250929"])
        
        # Calculate cost
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        # Record usage
        usage = APIUsage(
            service="claude",
            endpoint=model,
            tokens_used=input_tokens + output_tokens,
            cost=total_cost,
            timestamp=datetime.utcnow(),
            response_time=response_time,
            success=success,
            customer_id=customer_id
        )
        
        self.usage_data.append(usage)
        
        # Update daily totals
        today = datetime.utcnow().date().isoformat()
        self.daily_totals[today]["requests"] += 1
        self.daily_totals[today]["tokens"] += input_tokens + output_tokens
        self.daily_totals[today]["cost"] += total_cost
        if not success:
            self.daily_totals[today]["errors"] += 1
        
        # Check budget alerts
        self._check_budget_alerts(today)
        
        logger.info(f"Claude API usage: {input_tokens} in + {output_tokens} out = ${total_cost:.4f}")
        
        return total_cost
    
    def track_openai_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        response_time: float,
        success: bool = True,
        customer_id: Optional[str] = None
    ) -> float:
        """Track OpenAI API usage and calculate cost."""
        pricing = self.OPENAI_PRICING.get(model, self.OPENAI_PRICING["gpt-3.5-turbo"])
        
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        usage = APIUsage(
            service="openai",
            endpoint=model,
            tokens_used=input_tokens + output_tokens,
            cost=total_cost,
            timestamp=datetime.utcnow(),
            response_time=response_time,
            success=success,
            customer_id=customer_id
        )
        
        self.usage_data.append(usage)
        
        today = datetime.utcnow().date().isoformat()
        self.daily_totals[today]["requests"] += 1
        self.daily_totals[today]["tokens"] += input_tokens + output_tokens
        self.daily_totals[today]["cost"] += total_cost
        if not success:
            self.daily_totals[today]["errors"] += 1
        
        self._check_budget_alerts(today)
        
        return total_cost
    
    def track_stripe_usage(
        self,
        endpoint: str,
        response_time: float,
        success: bool = True,
        customer_id: Optional[str] = None
    ):
        """Track Stripe API usage (no direct cost, but track for monitoring)."""
        usage = APIUsage(
            service="stripe",
            endpoint=endpoint,
            tokens_used=0,
            cost=0.0,
            timestamp=datetime.utcnow(),
            response_time=response_time,
            success=success,
            customer_id=customer_id
        )
        
        self.usage_data.append(usage)
        
        today = datetime.utcnow().date().isoformat()
        self.daily_totals[today]["requests"] += 1
        if not success:
            self.daily_totals[today]["errors"] += 1
    
    def _check_budget_alerts(self, date: str):
        """Check if budget thresholds are exceeded."""
        daily_cost = self.daily_totals[date]["cost"]
        
        # Daily budget alert
        if daily_cost >= self.daily_budget * self.alert_threshold:
            from .alert_manager import get_alert_manager
            alert_manager = get_alert_manager()
            
            if daily_cost >= self.daily_budget:
                # Budget exceeded
                alert_manager.alert_security_incident(
                    "Daily API Budget Exceeded",
                    f"Daily API costs (${daily_cost:.2f}) exceeded budget (${self.daily_budget:.2f})"
                )
            else:
                # Approaching budget
                percentage = (daily_cost / self.daily_budget) * 100
                logger.warning(f"Daily API costs at {percentage:.1f}% of budget: ${daily_cost:.2f} / ${self.daily_budget:.2f}")
    
    def get_daily_summary(self, date: Optional[str] = None) -> Dict:
        """
        Get daily cost summary.
        
        Args:
            date: Date in YYYY-MM-DD format (default: today)
            
        Returns:
            Dictionary with daily summary
        """
        if date is None:
            date = datetime.utcnow().date().isoformat()
        
        summary = self.daily_totals.get(date, {
            "requests": 0,
            "tokens": 0,
            "cost": 0.0,
            "errors": 0,
        })
        
        summary["date"] = date
        summary["budget"] = self.daily_budget
        summary["budget_used_percentage"] = (summary["cost"] / self.daily_budget) * 100 if self.daily_budget > 0 else 0
        
        return summary
    
    def get_monthly_summary(self, year: Optional[int] = None, month: Optional[int] = None) -> Dict:
        """
        Get monthly cost summary.
        
        Args:
            year: Year (default: current year)
            month: Month (default: current month)
            
        Returns:
            Dictionary with monthly summary
        """
        now = datetime.utcnow()
        year = year or now.year
        month = month or now.month
        
        # Get all days in month
        month_prefix = f"{year:04d}-{month:02d}"
        
        monthly_data = {
            "year": year,
            "month": month,
            "requests": 0,
            "tokens": 0,
            "cost": 0.0,
            "errors": 0,
            "days": []
        }
        
        for date, data in self.daily_totals.items():
            if date.startswith(month_prefix):
                monthly_data["requests"] += data["requests"]
                monthly_data["tokens"] += data["tokens"]
                monthly_data["cost"] += data["cost"]
                monthly_data["errors"] += data["errors"]
                monthly_data["days"].append({"date": date, **data})
        
        monthly_data["budget"] = self.monthly_budget
        monthly_data["budget_used_percentage"] = (monthly_data["cost"] / self.monthly_budget) * 100 if self.monthly_budget > 0 else 0
        monthly_data["average_daily_cost"] = monthly_data["cost"] / len(monthly_data["days"]) if monthly_data["days"] else 0
        
        return monthly_data
    
    def get_customer_usage(self, customer_id: str, days: int = 30) -> Dict:
        """
        Get usage summary for a specific customer.
        
        Args:
            customer_id: Customer ID
            days: Number of days to look back
            
        Returns:
            Dictionary with customer usage summary
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        customer_data = {
            "customer_id": customer_id,
            "period_days": days,
            "requests": 0,
            "tokens": 0,
            "cost": 0.0,
            "errors": 0,
            "services": defaultdict(lambda: {"requests": 0, "cost": 0.0})
        }
        
        for usage in self.usage_data:
            if usage.customer_id == customer_id and usage.timestamp >= cutoff:
                customer_data["requests"] += 1
                customer_data["tokens"] += usage.tokens_used
                customer_data["cost"] += usage.cost
                if not usage.success:
                    customer_data["errors"] += 1
                
                customer_data["services"][usage.service]["requests"] += 1
                customer_data["services"][usage.service]["cost"] += usage.cost
        
        customer_data["services"] = dict(customer_data["services"])
        
        return customer_data
    
    def get_service_breakdown(self, days: int = 7) -> Dict:
        """
        Get cost breakdown by service.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with service breakdown
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        breakdown = {
            "period_days": days,
            "total_cost": 0.0,
            "services": defaultdict(lambda: {
                "requests": 0,
                "cost": 0.0,
                "tokens": 0,
                "errors": 0,
                "avg_response_time": 0.0,
                "response_times": []
            })
        }
        
        for usage in self.usage_data:
            if usage.timestamp >= cutoff:
                service = usage.service
                breakdown["services"][service]["requests"] += 1
                breakdown["services"][service]["cost"] += usage.cost
                breakdown["services"][service]["tokens"] += usage.tokens_used
                if not usage.success:
                    breakdown["services"][service]["errors"] += 1
                breakdown["services"][service]["response_times"].append(usage.response_time)
                breakdown["total_cost"] += usage.cost
        
        # Calculate average response times
        for service, data in breakdown["services"].items():
            if data["response_times"]:
                data["avg_response_time"] = sum(data["response_times"]) / len(data["response_times"])
                del data["response_times"]
        
        breakdown["services"] = dict(breakdown["services"])
        
        return breakdown
    
    def export_usage_data(self, filepath: str, days: int = 30):
        """
        Export usage data to JSON file.
        
        Args:
            filepath: Path to export file
            days: Number of days to export
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        export_data = [
            {
                **asdict(usage),
                "timestamp": usage.timestamp.isoformat()
            }
            for usage in self.usage_data
            if usage.timestamp >= cutoff
        ]
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported {len(export_data)} usage records to {filepath}")


# Global cost tracker instance
_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """Get the global cost tracker instance."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker

