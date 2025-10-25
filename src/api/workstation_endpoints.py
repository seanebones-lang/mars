"""
Workstation Management API Endpoints
Provides comprehensive workstation monitoring, discovery, and Claude-powered insights.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, Query
from pydantic import BaseModel

from ..services.workstation_discovery_service import get_discovery_service, NetworkRange, DiscoveryTask
from .auth_dependencies import get_current_user
from ..judges.claude_judge import ClaudeJudge
import os

logger = logging.getLogger(__name__)

# Pydantic models for workstation data
class WorkstationBase(BaseModel):
    name: str
    ip_address: str
    mac_address: Optional[str] = None
    os: str
    platform_version: Optional[str] = None
    status: str = "online"
    last_seen: datetime
    uptime: Optional[str] = None

class WorkstationDetails(WorkstationBase):
    workstation_id: str
    user: Optional[str] = None
    cpu_count: Optional[int] = None
    cpu_usage: Optional[float] = None
    memory_total_gb: Optional[float] = None
    memory_usage: Optional[float] = None
    disk_total_gb: Optional[float] = None
    disk_usage: Optional[float] = None
    python_version: Optional[str] = None
    watcher_client_version: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    open_ports: List[int] = []
    services: List[str] = []
    installed_software: List[str] = []
    running_processes: List[str] = []
    vulnerabilities: List[Dict[str, Any]] = []
    security_score: Optional[float] = None
    agent_installed: bool = False
    agent_version: Optional[str] = None
    agent_status: str = "inactive"
    discovery_method: Optional[str] = None
    tags: List[str] = []

class WorkstationInsights(BaseModel):
    system_health: str
    security_assessment: str
    performance_recommendations: List[str]
    anomaly_detection: str
    maintenance_schedule: List[str]
    risk_factors: List[str]
    optimization_tips: List[str]
    compliance_status: str

class FleetInsights(BaseModel):
    fleet_overview: str
    critical_issues: List[str]
    recommendations: List[str]
    trends: str
    risk_assessment: str

# Mock data generator for development
def generate_mock_workstations() -> List[WorkstationDetails]:
    """Generate realistic mock workstation data for development."""
    import random
    from datetime import datetime, timedelta
    
    workstations = []
    base_names = ["DEV-WS", "PROD-SRV", "TEST-LAB", "ADMIN-PC", "DB-SERVER", "WEB-NODE"]
    os_types = ["Windows 11", "Ubuntu 22.04", "macOS Sonoma", "CentOS 8", "Windows Server 2022"]
    
    for i in range(15):
        ws_id = f"ws-{i+1:03d}"
        name = f"{random.choice(base_names)}-{i+1:02d}"
        
        workstation = WorkstationDetails(
            workstation_id=ws_id,
            name=name,
            ip_address=f"192.168.1.{i+10}",
            mac_address=f"00:1B:44:11:3A:{i+10:02X}",
            os=random.choice(os_types),
            platform_version=f"{random.randint(10, 14)}.{random.randint(0, 9)}",
            status=random.choice(["online", "offline", "maintenance"]),
            last_seen=datetime.utcnow() - timedelta(minutes=random.randint(1, 120)),
            uptime=f"{random.randint(1, 30)} days",
            user=f"user{i+1}@company.com",
            cpu_count=random.choice([4, 8, 16, 32]),
            cpu_usage=random.uniform(10, 95),
            memory_total_gb=random.choice([8, 16, 32, 64]),
            memory_usage=random.uniform(20, 85),
            disk_total_gb=random.choice([256, 512, 1024, 2048]),
            disk_usage=random.uniform(30, 90),
            python_version=f"3.{random.randint(8, 12)}.{random.randint(0, 5)}",
            watcher_client_version=f"1.{random.randint(0, 5)}.{random.randint(0, 10)}",
            manufacturer=random.choice(["Dell", "HP", "Lenovo", "Apple", "Custom Build"]),
            model=f"Model-{random.randint(1000, 9999)}",
            serial_number=f"SN{random.randint(100000, 999999)}",
            open_ports=[22, 80, 443] + random.sample(range(8000, 9000), random.randint(0, 3)),
            services=random.sample(["SSH", "HTTP", "HTTPS", "MySQL", "PostgreSQL", "Redis", "Docker"], random.randint(2, 5)),
            installed_software=random.sample(["Chrome", "Firefox", "VSCode", "Docker", "Node.js", "Python", "Git"], random.randint(3, 6)),
            running_processes=random.sample(["chrome.exe", "python.exe", "node.exe", "docker.exe", "code.exe"], random.randint(2, 4)),
            vulnerabilities=[
                {"id": f"CVE-2024-{random.randint(1000, 9999)}", "severity": random.choice(["low", "medium", "high"]), "description": "Sample vulnerability"}
                for _ in range(random.randint(0, 3))
            ],
            security_score=random.uniform(60, 100),
            agent_installed=random.choice([True, False]),
            agent_version=f"2.{random.randint(0, 5)}.{random.randint(0, 10)}" if random.choice([True, False]) else None,
            agent_status=random.choice(["active", "inactive", "error", "updating"]),
            discovery_method=random.choice(["network_scan", "dhcp", "dns", "active_directory"]),
            tags=random.sample(["production", "development", "testing", "critical", "monitored"], random.randint(1, 3))
        )
        workstations.append(workstation)
    
    return workstations

# Workstation endpoints
async def get_workstations(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get list of all workstations with optional filtering.
    """
    try:
        # For now, return mock data - replace with actual database query
        workstations = generate_mock_workstations()
        
        # Apply status filter if provided
        if status:
            workstations = [ws for ws in workstations if ws.status == status]
        
        # Apply pagination
        total = len(workstations)
        workstations = workstations[offset:offset + limit]
        
        return {
            "workstations": [ws.dict() for ws in workstations],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
        
    except Exception as e:
        logger.error(f"Error fetching workstations: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch workstations")

async def get_workstation_by_id(
    workstation_id: str,
    current_user = Depends(get_current_user)
) -> WorkstationDetails:
    """
    Get detailed information about a specific workstation.
    """
    try:
        # For now, return mock data - replace with actual database query
        workstations = generate_mock_workstations()
        
        workstation = next((ws for ws in workstations if ws.workstation_id == workstation_id), None)
        if not workstation:
            raise HTTPException(status_code=404, detail="Workstation not found")
        
        return workstation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching workstation {workstation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch workstation details")

async def get_workstation_insights(
    workstation_id: str,
    current_user = Depends(get_current_user)
) -> WorkstationInsights:
    """
    Get Claude-powered insights for a specific workstation.
    """
    try:
        # Get workstation details
        workstation = await get_workstation_by_id(workstation_id, current_user)
        
        # Get Claude API key
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        if not claude_api_key:
            raise HTTPException(status_code=500, detail="Claude API not configured")
        
        # Initialize Claude judge
        claude_judge = ClaudeJudge(claude_api_key)
        
        # Create analysis prompt
        analysis_prompt = f"""Analyze this enterprise workstation and provide comprehensive insights:

Workstation: {workstation.name} ({workstation.workstation_id})
OS: {workstation.os} {workstation.platform_version}
Hardware: {workstation.cpu_count} CPUs, {workstation.memory_total_gb}GB RAM, {workstation.disk_total_gb}GB Storage
Performance: CPU {workstation.cpu_usage:.1f}%, Memory {workstation.memory_usage:.1f}%, Disk {workstation.disk_usage:.1f}%
Security Score: {workstation.security_score}/100
Vulnerabilities: {len(workstation.vulnerabilities)} found
Agent Status: {workstation.agent_status}
Last Seen: {workstation.last_seen}

Provide analysis in these areas:
1. System Health Assessment
2. Security Risk Evaluation  
3. Performance Optimization Recommendations
4. Anomaly Detection Insights
5. Maintenance Schedule Suggestions
6. Risk Factors to Monitor
7. Optimization Tips
8. Compliance Status

Be specific, actionable, and enterprise-focused."""

        # Get Claude analysis
        claude_result = await claude_judge.evaluate_async(
            agent_output=analysis_prompt,
            ground_truth="Provide comprehensive workstation analysis",
            conversation_history=[]
        )
        
        analysis = claude_result.get("reasoning", "Analysis completed successfully")
        
        # Parse and structure the response
        return WorkstationInsights(
            system_health=f"Overall Health: {'Good' if workstation.security_score > 80 else 'Needs Attention'}. {analysis[:200]}...",
            security_assessment=f"Security Score: {workstation.security_score}/100. {len(workstation.vulnerabilities)} vulnerabilities detected.",
            performance_recommendations=[
                "Monitor CPU usage during peak hours" if workstation.cpu_usage > 80 else "CPU performance is optimal",
                "Consider memory upgrade" if workstation.memory_usage > 85 else "Memory usage is acceptable",
                "Schedule disk cleanup" if workstation.disk_usage > 90 else "Disk space is adequate",
                "Review running processes for optimization"
            ],
            anomaly_detection=analysis[:300] if analysis else "No anomalies detected in current monitoring period",
            maintenance_schedule=[
                "Weekly security scan and updates",
                "Monthly performance review and optimization",
                "Quarterly hardware assessment",
                "Annual compliance audit and certification"
            ],
            risk_factors=[
                factor for factor in [
                    "High CPU usage" if workstation.cpu_usage > 80 else None,
                    "High memory usage" if workstation.memory_usage > 85 else None,
                    "Low disk space" if workstation.disk_usage > 90 else None,
                    "Low security score" if workstation.security_score < 70 else None,
                    f"{len(workstation.vulnerabilities)} vulnerabilities" if workstation.vulnerabilities else None
                ] if factor
            ],
            optimization_tips=[
                "Enable automatic security updates",
                "Implement resource monitoring alerts",
                "Regular cleanup of temporary files and logs",
                "Optimize startup programs and services",
                "Configure proper backup schedules"
            ],
            compliance_status="Compliant" if workstation.security_score > 80 else "Requires attention for compliance"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating workstation insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate workstation insights")

async def get_discovery_ranges(
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get configured network discovery ranges.
    """
    try:
        # Mock discovery ranges - replace with actual service
        ranges = [
            {
                "id": "range-001",
                "cidr": "192.168.1.0/24",
                "name": "Main Office Network",
                "description": "Primary office network range",
                "enabled": True,
                "last_scan": "2024-10-24T10:30:00Z",
                "devices_found": 45
            },
            {
                "id": "range-002", 
                "cidr": "10.0.0.0/16",
                "name": "Data Center Network",
                "description": "Production server network",
                "enabled": True,
                "last_scan": "2024-10-24T09:15:00Z",
                "devices_found": 128
            }
        ]
        
        return {
            "ranges": ranges,
            "total": len(ranges)
        }
        
    except Exception as e:
        logger.error(f"Error fetching discovery ranges: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch discovery ranges")

async def start_discovery_task(
    range_ids: List[str],
    methods: List[str] = ["network_scan", "dhcp"],
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Start a new workstation discovery task.
    """
    try:
        # Create mock discovery task - replace with actual service
        task_id = f"task-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        task = {
            "task_id": task_id,
            "status": "running",
            "range_ids": range_ids,
            "methods": methods,
            "started_at": datetime.utcnow().isoformat(),
            "progress": 0,
            "devices_found": 0,
            "estimated_completion": (datetime.utcnow() + timedelta(minutes=15)).isoformat()
        }
        
        return {
            "task": task,
            "message": f"Discovery task {task_id} started successfully"
        }
        
    except Exception as e:
        logger.error(f"Error starting discovery task: {e}")
        raise HTTPException(status_code=500, detail="Failed to start discovery task")

async def get_fleet_insights(
    current_user = Depends(get_current_user)
) -> FleetInsights:
    """
    Get Claude-powered insights for the entire workstation fleet.
    """
    try:
        # Get fleet statistics
        workstations = generate_mock_workstations()
        
        total_workstations = len(workstations)
        online_count = len([ws for ws in workstations if ws.status == "online"])
        avg_security_score = sum(ws.security_score or 0 for ws in workstations) / total_workstations
        total_vulnerabilities = sum(len(ws.vulnerabilities) for ws in workstations)
        
        # Get Claude API key
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        if not claude_api_key:
            raise HTTPException(status_code=500, detail="Claude API not configured")
        
        # Initialize Claude judge
        claude_judge = ClaudeJudge(claude_api_key)
        
        # Create fleet analysis prompt
        fleet_prompt = f"""Analyze this enterprise workstation fleet and provide strategic insights:

Fleet Statistics:
- Total Workstations: {total_workstations}
- Online: {online_count} ({online_count/total_workstations*100:.1f}%)
- Average Security Score: {avg_security_score:.1f}/100
- Total Vulnerabilities: {total_vulnerabilities}
- Operating Systems: {len(set(ws.os for ws in workstations))} different OS types
- Agent Coverage: {len([ws for ws in workstations if ws.agent_installed])}/{total_workstations} workstations

Provide strategic analysis covering:
1. Fleet Overview and Health Status
2. Critical Issues Requiring Immediate Attention
3. Strategic Recommendations for IT Management
4. Security and Compliance Trends
5. Risk Assessment and Mitigation Strategies

Focus on actionable insights for enterprise IT decision-making."""

        # Get Claude analysis
        claude_result = await claude_judge.evaluate_async(
            agent_output=fleet_prompt,
            ground_truth="Provide comprehensive fleet analysis",
            conversation_history=[]
        )
        
        analysis = claude_result.get("reasoning", "Fleet analysis completed")
        
        return FleetInsights(
            fleet_overview=f"Fleet of {total_workstations} workstations with {online_count/total_workstations*100:.1f}% availability. {analysis[:300]}",
            critical_issues=[
                issue for issue in [
                    f"Low security score: {avg_security_score:.1f}/100" if avg_security_score < 80 else None,
                    f"{total_vulnerabilities} total vulnerabilities across fleet" if total_vulnerabilities > 10 else None,
                    f"{total_workstations - online_count} workstations offline" if online_count < total_workstations else None,
                    f"Agent coverage: {len([ws for ws in workstations if ws.agent_installed])}/{total_workstations}" if len([ws for ws in workstations if ws.agent_installed]) < total_workstations * 0.8 else None
                ] if issue
            ],
            recommendations=[
                "Implement automated patch management across all workstations",
                "Deploy monitoring agents to all systems for better visibility",
                "Establish regular security scanning schedules",
                "Create standardized workstation configurations",
                "Implement zero-trust network access controls"
            ],
            trends=f"Security posture trending {'positive' if avg_security_score > 75 else 'concerning'}. Agent adoption at {len([ws for ws in workstations if ws.agent_installed])/total_workstations*100:.1f}%.",
            risk_assessment=f"Overall fleet risk: {'Low' if avg_security_score > 85 else 'Medium' if avg_security_score > 70 else 'High'}. Primary concerns: vulnerability management and agent deployment."
        )
        
    except Exception as e:
        logger.error(f"Error generating fleet insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate fleet insights")
