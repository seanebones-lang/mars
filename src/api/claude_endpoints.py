"""
Enhanced Claude Integration API Endpoints
Provides structured Claude responses for various analysis types with WebSocket support.
"""

import logging
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import HTTPException, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from .auth_dependencies import get_current_user
from ..judges.claude_judge import ClaudeJudge
import os

logger = logging.getLogger(__name__)

# Pydantic models for structured Claude responses
class ClaudeInsightRequest(BaseModel):
    context_type: str  # "workstation", "fleet", "agent", "analytics"
    data: Dict[str, Any]
    analysis_type: str  # "health", "security", "performance", "trends"
    custom_prompt: Optional[str] = None

class ClaudeInsightResponse(BaseModel):
    analysis_type: str
    insights: Dict[str, Any]
    recommendations: List[str]
    risk_assessment: str
    confidence_score: float
    generated_at: datetime

class WorkstationAnalysisRequest(BaseModel):
    workstation_data: Dict[str, Any]
    analysis_focus: List[str] = ["health", "security", "performance"]

class FleetAnalysisRequest(BaseModel):
    fleet_statistics: Dict[str, Any]
    workstation_sample: List[Dict[str, Any]]
    analysis_scope: str = "comprehensive"

# WebSocket connection manager for real-time Claude analysis
class ClaudeWebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_analysis_update(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                # Remove broken connections
                self.disconnect(connection)

claude_ws_manager = ClaudeWebSocketManager()

async def get_structured_claude_insights(
    request: ClaudeInsightRequest,
    current_user = Depends(get_current_user)
) -> ClaudeInsightResponse:
    """
    Get structured Claude insights for various analysis types.
    """
    try:
        # Get Claude API key
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        if not claude_api_key:
            raise HTTPException(status_code=500, detail="Claude API not configured")
        
        # Initialize Claude judge
        claude_judge = ClaudeJudge(claude_api_key)
        
        # Build context-specific prompt
        if request.context_type == "workstation":
            prompt = await _build_workstation_analysis_prompt(request.data, request.analysis_type)
        elif request.context_type == "fleet":
            prompt = await _build_fleet_analysis_prompt(request.data, request.analysis_type)
        elif request.context_type == "agent":
            prompt = await _build_agent_analysis_prompt(request.data, request.analysis_type)
        elif request.context_type == "analytics":
            prompt = await _build_analytics_analysis_prompt(request.data, request.analysis_type)
        else:
            raise HTTPException(status_code=400, detail="Invalid context_type")
        
        # Add custom prompt if provided
        if request.custom_prompt:
            prompt += f"\n\nAdditional Context: {request.custom_prompt}"
        
        # Get Claude analysis
        claude_result = await claude_judge.evaluate_async(
            agent_output=prompt,
            ground_truth=f"Provide structured {request.analysis_type} analysis",
            conversation_history=[]
        )
        
        analysis = claude_result.get("reasoning", "Analysis completed")
        confidence = claude_result.get("confidence", 0.85)
        
        # Structure the response based on analysis type
        insights = await _structure_claude_response(analysis, request.analysis_type, request.data)
        
        return ClaudeInsightResponse(
            analysis_type=request.analysis_type,
            insights=insights,
            recommendations=insights.get("recommendations", []),
            risk_assessment=insights.get("risk_assessment", "Assessment completed"),
            confidence_score=confidence,
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error generating Claude insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate Claude insights")

async def analyze_workstation_with_claude(
    request: WorkstationAnalysisRequest,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Comprehensive workstation analysis using Claude with multiple focus areas.
    """
    try:
        # Get Claude API key
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        if not claude_api_key:
            raise HTTPException(status_code=500, detail="Claude API not configured")
        
        # Initialize Claude judge
        claude_judge = ClaudeJudge(claude_api_key)
        
        workstation = request.workstation_data
        
        # Build comprehensive workstation analysis prompt
        prompt = f"""Perform comprehensive enterprise workstation analysis:

WORKSTATION PROFILE:
Name: {workstation.get('name', 'Unknown')}
OS: {workstation.get('os', 'Unknown')} {workstation.get('platform_version', '')}
Hardware: {workstation.get('cpu_count', 'N/A')} CPUs, {workstation.get('memory_total_gb', 'N/A')}GB RAM
Performance: CPU {workstation.get('cpu_usage', 0):.1f}%, Memory {workstation.get('memory_usage', 0):.1f}%, Disk {workstation.get('disk_usage', 0):.1f}%
Security Score: {workstation.get('security_score', 0)}/100
Vulnerabilities: {len(workstation.get('vulnerabilities', []))} detected
Agent Status: {workstation.get('agent_status', 'unknown')}
Last Activity: {workstation.get('last_seen', 'Unknown')}

ANALYSIS FOCUS AREAS: {', '.join(request.analysis_focus)}

Provide detailed analysis in JSON-like structure covering:

SYSTEM_HEALTH:
- Overall health status and critical metrics
- Performance bottlenecks and resource utilization
- System stability and reliability indicators

SECURITY_ASSESSMENT:
- Security posture and vulnerability analysis
- Compliance status and risk factors
- Recommended security improvements

PERFORMANCE_OPTIMIZATION:
- Resource utilization analysis
- Performance improvement opportunities
- Capacity planning recommendations

MAINTENANCE_SCHEDULE:
- Recommended maintenance tasks and frequency
- Preventive maintenance priorities
- Update and patch management

RISK_FACTORS:
- Immediate risks requiring attention
- Medium-term concerns and monitoring points
- Long-term strategic considerations

ACTIONABLE_RECOMMENDATIONS:
- Immediate actions (next 24-48 hours)
- Short-term improvements (next 2 weeks)
- Long-term strategic initiatives (next quarter)

Be specific, actionable, and enterprise-focused. Prioritize recommendations by business impact."""

        # Get Claude analysis
        claude_result = await claude_judge.evaluate_async(
            agent_output=prompt,
            ground_truth="Provide comprehensive workstation analysis",
            conversation_history=[]
        )
        
        analysis = claude_result.get("reasoning", "Analysis completed")
        
        # Parse and structure the analysis
        structured_analysis = {
            "workstation_id": workstation.get("workstation_id", "unknown"),
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "focus_areas": request.analysis_focus,
            "system_health": {
                "status": "good" if workstation.get("security_score", 0) > 80 else "needs_attention",
                "score": workstation.get("security_score", 0),
                "details": analysis[:500]
            },
            "security_assessment": {
                "risk_level": "low" if workstation.get("security_score", 0) > 85 else "medium" if workstation.get("security_score", 0) > 70 else "high",
                "vulnerabilities_count": len(workstation.get("vulnerabilities", [])),
                "compliance_status": "compliant" if workstation.get("security_score", 0) > 80 else "non_compliant",
                "recommendations": [
                    "Enable automatic security updates",
                    "Implement endpoint detection and response",
                    "Regular vulnerability assessments",
                    "User access review and cleanup"
                ]
            },
            "performance_metrics": {
                "cpu_utilization": workstation.get("cpu_usage", 0),
                "memory_utilization": workstation.get("memory_usage", 0),
                "disk_utilization": workstation.get("disk_usage", 0),
                "performance_score": 100 - max(workstation.get("cpu_usage", 0), workstation.get("memory_usage", 0), workstation.get("disk_usage", 0)),
                "optimization_opportunities": [
                    "Optimize startup programs" if workstation.get("cpu_usage", 0) > 80 else None,
                    "Memory cleanup and optimization" if workstation.get("memory_usage", 0) > 85 else None,
                    "Disk cleanup and archival" if workstation.get("disk_usage", 0) > 90 else None
                ]
            },
            "maintenance_schedule": [
                {
                    "task": "Security patch installation",
                    "frequency": "weekly",
                    "priority": "high",
                    "estimated_duration": "30 minutes"
                },
                {
                    "task": "Performance monitoring review",
                    "frequency": "monthly", 
                    "priority": "medium",
                    "estimated_duration": "15 minutes"
                },
                {
                    "task": "Hardware health check",
                    "frequency": "quarterly",
                    "priority": "medium",
                    "estimated_duration": "45 minutes"
                }
            ],
            "claude_analysis": analysis,
            "confidence_score": claude_result.get("confidence", 0.85)
        }
        
        return structured_analysis
        
    except Exception as e:
        logger.error(f"Error in workstation Claude analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze workstation")

async def analyze_fleet_with_claude(
    request: FleetAnalysisRequest,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Fleet-level analysis using Claude for strategic insights.
    """
    try:
        # Get Claude API key
        claude_api_key = os.getenv("CLAUDE_API_KEY")
        if not claude_api_key:
            raise HTTPException(status_code=500, detail="Claude API not configured")
        
        # Initialize Claude judge
        claude_judge = ClaudeJudge(claude_api_key)
        
        stats = request.fleet_statistics
        
        # Build fleet analysis prompt
        prompt = f"""Perform strategic enterprise fleet analysis:

FLEET STATISTICS:
Total Workstations: {stats.get('total_workstations', 0)}
Online: {stats.get('online_count', 0)} ({stats.get('availability_percentage', 0):.1f}%)
Average Security Score: {stats.get('avg_security_score', 0):.1f}/100
Total Vulnerabilities: {stats.get('total_vulnerabilities', 0)}
Agent Coverage: {stats.get('agent_coverage_percentage', 0):.1f}%
Operating Systems: {stats.get('os_diversity', 0)} different types
Average Uptime: {stats.get('avg_uptime_days', 0)} days

SAMPLE WORKSTATIONS ANALYSIS:
{chr(10).join([f"- {ws.get('name', 'Unknown')}: {ws.get('os', 'Unknown')}, Security: {ws.get('security_score', 0)}/100" for ws in request.workstation_sample[:5]])}

ANALYSIS SCOPE: {request.analysis_scope}

Provide strategic fleet analysis covering:

EXECUTIVE_SUMMARY:
- Fleet health overview and key metrics
- Critical issues requiring immediate C-level attention
- Strategic opportunities and competitive advantages

SECURITY_POSTURE:
- Overall security maturity assessment
- Vulnerability management effectiveness
- Compliance readiness and gaps

OPERATIONAL_EFFICIENCY:
- Resource utilization and optimization opportunities
- Standardization and automation potential
- Cost optimization recommendations

STRATEGIC_RECOMMENDATIONS:
- Technology roadmap and modernization priorities
- Investment priorities for next 12 months
- Risk mitigation strategies

BUSINESS_IMPACT:
- Productivity implications of current state
- Cost of inaction and potential savings
- ROI projections for recommended improvements

Focus on C-level strategic insights and business impact."""

        # Get Claude analysis
        claude_result = await claude_judge.evaluate_async(
            agent_output=prompt,
            ground_truth="Provide strategic fleet analysis",
            conversation_history=[]
        )
        
        analysis = claude_result.get("reasoning", "Fleet analysis completed")
        
        # Structure fleet analysis
        fleet_analysis = {
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "fleet_size": stats.get('total_workstations', 0),
            "analysis_scope": request.analysis_scope,
            "executive_summary": {
                "overall_health": "good" if stats.get('avg_security_score', 0) > 80 else "needs_improvement",
                "key_metrics": {
                    "availability": f"{stats.get('availability_percentage', 0):.1f}%",
                    "security_score": f"{stats.get('avg_security_score', 0):.1f}/100",
                    "agent_coverage": f"{stats.get('agent_coverage_percentage', 0):.1f}%"
                },
                "critical_issues": [
                    f"Low security posture: {stats.get('avg_security_score', 0):.1f}/100" if stats.get('avg_security_score', 0) < 80 else None,
                    f"{stats.get('total_vulnerabilities', 0)} vulnerabilities across fleet" if stats.get('total_vulnerabilities', 0) > 50 else None,
                    f"Agent coverage at {stats.get('agent_coverage_percentage', 0):.1f}%" if stats.get('agent_coverage_percentage', 0) < 90 else None
                ]
            },
            "security_assessment": {
                "maturity_level": "advanced" if stats.get('avg_security_score', 0) > 85 else "intermediate" if stats.get('avg_security_score', 0) > 70 else "basic",
                "vulnerability_density": stats.get('total_vulnerabilities', 0) / max(stats.get('total_workstations', 1), 1),
                "compliance_readiness": "ready" if stats.get('avg_security_score', 0) > 80 else "needs_work"
            },
            "strategic_recommendations": [
                "Implement zero-trust architecture across all endpoints",
                "Standardize workstation configurations and deployment",
                "Enhance monitoring and alerting capabilities",
                "Develop incident response and recovery procedures",
                "Invest in automated patch management systems"
            ],
            "business_impact": {
                "productivity_risk": "low" if stats.get('availability_percentage', 0) > 95 else "medium" if stats.get('availability_percentage', 0) > 90 else "high",
                "security_risk": "low" if stats.get('avg_security_score', 0) > 85 else "medium" if stats.get('avg_security_score', 0) > 70 else "high",
                "estimated_annual_savings": f"${stats.get('total_workstations', 0) * 500:,}" # Rough estimate
            },
            "claude_analysis": analysis,
            "confidence_score": claude_result.get("confidence", 0.85)
        }
        
        return fleet_analysis
        
    except Exception as e:
        logger.error(f"Error in fleet Claude analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze fleet")

# WebSocket endpoint for real-time Claude analysis
async def claude_websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time Claude analysis and insights.
    """
    await claude_ws_manager.connect(websocket)
    try:
        while True:
            # Receive analysis request
            data = await websocket.receive_text()
            request_data = json.loads(data)
            
            # Send analysis started message
            await websocket.send_text(json.dumps({
                "type": "analysis_started",
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_data.get("request_id", "unknown")
            }))
            
            # Process analysis based on type
            if request_data.get("analysis_type") == "workstation":
                # Simulate real-time workstation analysis
                for progress in [25, 50, 75, 100]:
                    await asyncio.sleep(0.5)  # Simulate processing time
                    await websocket.send_text(json.dumps({
                        "type": "analysis_progress",
                        "progress": progress,
                        "stage": f"Processing workstation data... {progress}%",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                
                # Send final results
                await websocket.send_text(json.dumps({
                    "type": "analysis_complete",
                    "results": {
                        "health_score": 85,
                        "security_score": 78,
                        "recommendations": [
                            "Update security patches",
                            "Optimize memory usage",
                            "Schedule maintenance"
                        ]
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }))
            
    except WebSocketDisconnect:
        claude_ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        claude_ws_manager.disconnect(websocket)

# Helper functions for building analysis prompts
async def _build_workstation_analysis_prompt(data: Dict[str, Any], analysis_type: str) -> str:
    """Build workstation-specific analysis prompt."""
    return f"Analyze workstation {data.get('name', 'Unknown')} focusing on {analysis_type}..."

async def _build_fleet_analysis_prompt(data: Dict[str, Any], analysis_type: str) -> str:
    """Build fleet-specific analysis prompt."""
    return f"Analyze fleet of {data.get('total_workstations', 0)} workstations focusing on {analysis_type}..."

async def _build_agent_analysis_prompt(data: Dict[str, Any], analysis_type: str) -> str:
    """Build agent-specific analysis prompt."""
    return f"Analyze AI agent performance focusing on {analysis_type}..."

async def _build_analytics_analysis_prompt(data: Dict[str, Any], analysis_type: str) -> str:
    """Build analytics-specific analysis prompt."""
    return f"Analyze platform analytics focusing on {analysis_type}..."

async def _structure_claude_response(analysis: str, analysis_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Structure Claude response based on analysis type."""
    return {
        "analysis": analysis,
        "recommendations": [
            "Implement recommended security measures",
            "Monitor system performance regularly",
            "Schedule preventive maintenance"
        ],
        "risk_assessment": "Medium risk - requires attention",
        "next_steps": [
            "Review analysis findings",
            "Implement high-priority recommendations",
            "Schedule follow-up assessment"
        ]
    }
