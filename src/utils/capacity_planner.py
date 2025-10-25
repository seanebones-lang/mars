"""
Capacity Planning and Forecasting
P1-5: Operational excellence through proactive capacity planning
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


class CapacityPlanner:
    """
    Capacity planning and resource forecasting.
    
    Features:
    - Traffic forecasting
    - Resource utilization tracking
    - Scaling recommendations
    - Cost forecasting
    """
    
    def __init__(self):
        """Initialize capacity planner."""
        self.traffic_data: List[Dict] = []
        self.resource_data: List[Dict] = []
        
        # Thresholds
        self.cpu_threshold = float(os.getenv("CPU_THRESHOLD", "0.80"))  # 80%
        self.memory_threshold = float(os.getenv("MEMORY_THRESHOLD", "0.80"))  # 80%
        self.request_rate_threshold = float(os.getenv("REQUEST_RATE_THRESHOLD", "800"))  # 80% of 1000 req/s
        
        logger.info("Capacity planner initialized")
    
    def record_traffic(self, timestamp: datetime, request_count: int, response_time: float):
        """
        Record traffic data point.
        
        Args:
            timestamp: Timestamp of measurement
            request_count: Number of requests in period
            response_time: Average response time
        """
        self.traffic_data.append({
            "timestamp": timestamp,
            "request_count": request_count,
            "response_time": response_time,
            "requests_per_second": request_count / 60  # Assuming 1-minute periods
        })
        
        # Keep only last 30 days
        cutoff = datetime.utcnow() - timedelta(days=30)
        self.traffic_data = [d for d in self.traffic_data if d["timestamp"] >= cutoff]
    
    def record_resources(self, timestamp: datetime, cpu: float, memory: float, connections: int):
        """
        Record resource utilization data point.
        
        Args:
            timestamp: Timestamp of measurement
            cpu: CPU utilization (0-1)
            memory: Memory utilization (0-1)
            connections: Number of active connections
        """
        self.resource_data.append({
            "timestamp": timestamp,
            "cpu": cpu,
            "memory": memory,
            "connections": connections
        })
        
        # Keep only last 30 days
        cutoff = datetime.utcnow() - timedelta(days=30)
        self.resource_data = [d for d in self.resource_data if d["timestamp"] >= cutoff]
    
    def forecast_traffic(self, days_ahead: int = 7) -> Dict:
        """
        Forecast traffic for next N days.
        
        Args:
            days_ahead: Number of days to forecast
            
        Returns:
            Traffic forecast
        """
        if len(self.traffic_data) < 7:
            return {
                "status": "insufficient_data",
                "message": "Need at least 7 days of data for forecasting"
            }
        
        # Simple linear regression forecast
        # Group by day
        daily_traffic = defaultdict(list)
        for data in self.traffic_data:
            date = data["timestamp"].date()
            daily_traffic[date].append(data["requests_per_second"])
        
        # Calculate daily averages
        daily_averages = {
            date: statistics.mean(values)
            for date, values in daily_traffic.items()
        }
        
        # Calculate trend
        dates = sorted(daily_averages.keys())
        values = [daily_averages[date] for date in dates]
        
        if len(values) < 2:
            return {
                "status": "insufficient_data",
                "message": "Need at least 2 days of data"
            }
        
        # Simple linear trend
        avg_daily_change = (values[-1] - values[0]) / len(values)
        
        # Forecast
        current_value = values[-1]
        forecast = []
        
        for i in range(1, days_ahead + 1):
            forecasted_value = current_value + (avg_daily_change * i)
            forecast_date = dates[-1] + timedelta(days=i)
            
            forecast.append({
                "date": forecast_date.isoformat(),
                "requests_per_second": max(0, forecasted_value),
                "confidence": "low" if i > 3 else "medium"
            })
        
        return {
            "status": "success",
            "forecast": forecast,
            "trend": "increasing" if avg_daily_change > 0 else "decreasing",
            "avg_daily_change": avg_daily_change
        }
    
    def get_scaling_recommendations(self) -> List[Dict]:
        """
        Get scaling recommendations based on current metrics.
        
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if not self.resource_data:
            return [{
                "type": "info",
                "message": "No resource data available for recommendations"
            }]
        
        # Get recent data (last hour)
        cutoff = datetime.utcnow() - timedelta(hours=1)
        recent_data = [d for d in self.resource_data if d["timestamp"] >= cutoff]
        
        if not recent_data:
            return [{
                "type": "info",
                "message": "No recent resource data available"
            }]
        
        # Calculate averages
        avg_cpu = statistics.mean([d["cpu"] for d in recent_data])
        avg_memory = statistics.mean([d["memory"] for d in recent_data])
        avg_connections = statistics.mean([d["connections"] for d in recent_data])
        
        # CPU recommendations
        if avg_cpu > self.cpu_threshold:
            recommendations.append({
                "type": "scale_up",
                "resource": "cpu",
                "current": f"{avg_cpu * 100:.1f}%",
                "threshold": f"{self.cpu_threshold * 100:.1f}%",
                "action": "Increase CPU allocation or add more instances",
                "priority": "high" if avg_cpu > 0.90 else "medium"
            })
        elif avg_cpu < 0.30:
            recommendations.append({
                "type": "scale_down",
                "resource": "cpu",
                "current": f"{avg_cpu * 100:.1f}%",
                "action": "Consider reducing CPU allocation to save costs",
                "priority": "low"
            })
        
        # Memory recommendations
        if avg_memory > self.memory_threshold:
            recommendations.append({
                "type": "scale_up",
                "resource": "memory",
                "current": f"{avg_memory * 100:.1f}%",
                "threshold": f"{self.memory_threshold * 100:.1f}%",
                "action": "Increase memory allocation or add more instances",
                "priority": "high" if avg_memory > 0.90 else "medium"
            })
        elif avg_memory < 0.30:
            recommendations.append({
                "type": "scale_down",
                "resource": "memory",
                "current": f"{avg_memory * 100:.1f}%",
                "action": "Consider reducing memory allocation to save costs",
                "priority": "low"
            })
        
        # Traffic recommendations
        if self.traffic_data:
            recent_traffic = [d for d in self.traffic_data if d["timestamp"] >= cutoff]
            if recent_traffic:
                avg_rps = statistics.mean([d["requests_per_second"] for d in recent_traffic])
                
                if avg_rps > self.request_rate_threshold:
                    recommendations.append({
                        "type": "scale_up",
                        "resource": "instances",
                        "current": f"{avg_rps:.1f} req/s",
                        "threshold": f"{self.request_rate_threshold:.1f} req/s",
                        "action": "Add more instances to handle increased traffic",
                        "priority": "high" if avg_rps > 900 else "medium"
                    })
        
        if not recommendations:
            recommendations.append({
                "type": "info",
                "message": "All resources within normal operating range"
            })
        
        return recommendations
    
    def forecast_costs(self, days_ahead: int = 30) -> Dict:
        """
        Forecast costs for next N days.
        
        Args:
            days_ahead: Number of days to forecast
            
        Returns:
            Cost forecast
        """
        # Get traffic forecast
        traffic_forecast = self.forecast_traffic(days_ahead)
        
        if traffic_forecast["status"] != "success":
            return traffic_forecast
        
        # Cost assumptions (adjust based on actual costs)
        cost_per_request = 0.0001  # $0.0001 per request
        base_infrastructure_cost = 200  # $200/month base cost
        
        daily_costs = []
        total_cost = 0
        
        for day in traffic_forecast["forecast"]:
            # Requests per day (assuming 24 hours)
            requests_per_day = day["requests_per_second"] * 60 * 60 * 24
            
            # Variable cost
            variable_cost = requests_per_day * cost_per_request
            
            # Daily infrastructure cost
            daily_infra_cost = base_infrastructure_cost / 30
            
            # Total daily cost
            daily_cost = variable_cost + daily_infra_cost
            total_cost += daily_cost
            
            daily_costs.append({
                "date": day["date"],
                "requests": int(requests_per_day),
                "variable_cost": variable_cost,
                "infrastructure_cost": daily_infra_cost,
                "total_cost": daily_cost
            })
        
        return {
            "status": "success",
            "period_days": days_ahead,
            "total_cost": total_cost,
            "average_daily_cost": total_cost / days_ahead,
            "daily_breakdown": daily_costs
        }
    
    def get_capacity_report(self) -> Dict:
        """
        Get comprehensive capacity report.
        
        Returns:
            Capacity report with metrics and recommendations
        """
        # Current metrics
        current_metrics = {}
        if self.resource_data:
            recent = self.resource_data[-10:]  # Last 10 data points
            current_metrics = {
                "cpu": f"{statistics.mean([d['cpu'] for d in recent]) * 100:.1f}%",
                "memory": f"{statistics.mean([d['memory'] for d in recent]) * 100:.1f}%",
                "connections": int(statistics.mean([d['connections'] for d in recent]))
            }
        
        if self.traffic_data:
            recent = self.traffic_data[-10:]
            current_metrics["requests_per_second"] = f"{statistics.mean([d['requests_per_second'] for d in recent]):.1f}"
            current_metrics["response_time"] = f"{statistics.mean([d['response_time'] for d in recent]):.2f}ms"
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "current_metrics": current_metrics,
            "traffic_forecast": self.forecast_traffic(7),
            "scaling_recommendations": self.get_scaling_recommendations(),
            "cost_forecast": self.forecast_costs(30)
        }


# Global capacity planner instance
_capacity_planner: Optional[CapacityPlanner] = None


def get_capacity_planner() -> CapacityPlanner:
    """Get the global capacity planner instance."""
    global _capacity_planner
    if _capacity_planner is None:
        _capacity_planner = CapacityPlanner()
    return _capacity_planner

