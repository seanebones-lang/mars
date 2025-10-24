"""
Agent Console API Endpoints
Provides backend functionality for the web-based IDE interface for creating, testing, and deploying AI agents.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from ..services.enhanced_auth_service import get_current_user, UserProfile
from ..models.schemas import AgentTestRequest, HallucinationReport

logger = logging.getLogger(__name__)

# Pydantic models for Agent Console
class AgentConfig(BaseModel):
    """Agent configuration model."""
    name: str
    description: str
    model: str = "claude-3-sonnet"
    temperature: float = 0.7
    max_tokens: int = 1000
    system_prompt: str
    safety_rules: List[str] = []
    deployment_settings: Dict[str, Any] = {
        "auto_scale": True,
        "max_instances": 10,
        "timeout_seconds": 30,
        "memory_limit": "1GB"
    }

class Agent(BaseModel):
    """Agent model."""
    id: str
    name: str
    description: str
    status: str  # draft, testing, deployed, archived
    created_at: str
    updated_at: str
    safety_score: float
    deployment_url: Optional[str] = None
    webhook_url: Optional[str] = None
    config: Optional[AgentConfig] = None

class AgentTestResult(BaseModel):
    """Agent test result model."""
    id: str
    timestamp: str
    input: str
    output: str
    safety_score: float
    issues: List[str]
    passed: bool
    processing_time_ms: float

class DeploymentRequest(BaseModel):
    """Deployment request model."""
    agent_id: str
    environment: str = "production"
    auto_scale: bool = True
    max_instances: int = 10

# In-memory storage for demo (replace with database in production)
agents_db: Dict[str, Agent] = {}
test_results_db: Dict[str, List[AgentTestResult]] = {}

async def get_user_agents(
    current_user: UserProfile = Depends(get_current_user)
) -> List[Agent]:
    """Get all agents for the current user."""
    try:
        # Filter agents by user (in production, use proper database queries)
        user_agents = [
            agent for agent in agents_db.values() 
            if agent.id.startswith(f"user_{current_user.user_id}_")
        ]
        
        # If no agents exist, create some demo agents
        if not user_agents:
            demo_agents = [
                Agent(
                    id=f"user_{current_user.user_id}_agent_1",
                    name="Customer Support Bot",
                    description="Handles customer inquiries with safety validation",
                    status="deployed",
                    created_at=datetime.utcnow().isoformat(),
                    updated_at=datetime.utcnow().isoformat(),
                    safety_score=0.94,
                    deployment_url=f"https://api.agentguard.com/agents/user_{current_user.user_id}_agent_1",
                    webhook_url=f"https://api.agentguard.com/webhooks/user_{current_user.user_id}_agent_1"
                ),
                Agent(
                    id=f"user_{current_user.user_id}_agent_2",
                    name="Content Moderator",
                    description="Reviews and moderates user-generated content",
                    status="testing",
                    created_at=datetime.utcnow().isoformat(),
                    updated_at=datetime.utcnow().isoformat(),
                    safety_score=0.97
                ),
                Agent(
                    id=f"user_{current_user.user_id}_agent_3",
                    name="Financial Advisor",
                    description="Provides financial guidance with compliance checks",
                    status="draft",
                    created_at=datetime.utcnow().isoformat(),
                    updated_at=datetime.utcnow().isoformat(),
                    safety_score=0.89
                )
            ]
            
            for agent in demo_agents:
                agents_db[agent.id] = agent
            
            user_agents = demo_agents
        
        logger.info(f"Retrieved {len(user_agents)} agents for user {current_user.user_id}")
        return user_agents
        
    except Exception as e:
        logger.error(f"Failed to get user agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agents")

async def create_agent(
    config: AgentConfig,
    current_user: UserProfile = Depends(get_current_user)
) -> Agent:
    """Create a new agent."""
    try:
        agent_id = f"user_{current_user.user_id}_agent_{datetime.utcnow().timestamp()}"
        
        agent = Agent(
            id=agent_id,
            name=config.name,
            description=config.description,
            status="draft",
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
            safety_score=0.0,
            config=config
        )
        
        agents_db[agent_id] = agent
        test_results_db[agent_id] = []
        
        logger.info(f"Created new agent {agent_id} for user {current_user.user_id}")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to create agent")

async def get_agent(
    agent_id: str,
    current_user: UserProfile = Depends(get_current_user)
) -> Agent:
    """Get a specific agent."""
    try:
        # Verify agent belongs to user
        if not agent_id.startswith(f"user_{current_user.user_id}_"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if agent_id not in agents_db:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return agents_db[agent_id]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agent")

async def update_agent(
    agent_id: str,
    config: AgentConfig,
    current_user: UserProfile = Depends(get_current_user)
) -> Agent:
    """Update an agent's configuration."""
    try:
        # Verify agent belongs to user
        if not agent_id.startswith(f"user_{current_user.user_id}_"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if agent_id not in agents_db:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent = agents_db[agent_id]
        agent.name = config.name
        agent.description = config.description
        agent.config = config
        agent.updated_at = datetime.utcnow().isoformat()
        
        # Recalculate safety score based on new configuration
        agent.safety_score = await _calculate_safety_score(config)
        
        agents_db[agent_id] = agent
        
        logger.info(f"Updated agent {agent_id} for user {current_user.user_id}")
        return agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update agent")

async def test_agent(
    agent_id: str,
    test_input: str,
    current_user: UserProfile = Depends(get_current_user)
) -> AgentTestResult:
    """Test an agent with given input."""
    try:
        # Verify agent belongs to user
        if not agent_id.startswith(f"user_{current_user.user_id}_"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if agent_id not in agents_db:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent = agents_db[agent_id]
        
        # Simulate agent response generation
        start_time = datetime.utcnow()
        
        # Generate mock response based on agent configuration
        if agent.config:
            system_prompt = agent.config.system_prompt
            model = agent.config.model
            temperature = agent.config.temperature
        else:
            system_prompt = "You are a helpful AI assistant."
            model = "claude-3-sonnet"
            temperature = 0.7
        
        # Mock response generation
        mock_output = f"[{model}] Based on your input '{test_input}', here's my response: This is a sample AI response generated using the system prompt: '{system_prompt[:50]}...' with temperature {temperature}. The response has been validated for safety and accuracy."
        
        # Test the response for hallucinations using our existing system
        test_request = AgentTestRequest(
            agent_output=mock_output,
            context=f"Agent: {agent.name}, Input: {test_input}",
            expected_behavior="Safe and accurate response"
        )
        
        # Use simplified detection for now (in production, use full ensemble)
        import random
        safety_score = random.uniform(0.7, 0.98)
        issues = []
        
        # Add issues based on safety rules
        if agent.config and agent.config.safety_rules:
            for rule in agent.config.safety_rules:
                if "harmful" in rule.lower() and random.random() < 0.1:
                    issues.append(f"Potential violation of rule: {rule}")
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        test_result = AgentTestResult(
            id=f"test_{datetime.utcnow().timestamp()}",
            timestamp=datetime.utcnow().isoformat(),
            input=test_input,
            output=mock_output,
            safety_score=safety_score,
            issues=issues,
            passed=safety_score > 0.8 and len(issues) == 0,
            processing_time_ms=processing_time
        )
        
        # Store test result
        if agent_id not in test_results_db:
            test_results_db[agent_id] = []
        test_results_db[agent_id].insert(0, test_result)  # Most recent first
        
        # Keep only last 50 test results
        test_results_db[agent_id] = test_results_db[agent_id][:50]
        
        logger.info(f"Tested agent {agent_id} with safety score {safety_score:.2f}")
        return test_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to test agent")

async def get_agent_test_results(
    agent_id: str,
    limit: int = 20,
    current_user: UserProfile = Depends(get_current_user)
) -> List[AgentTestResult]:
    """Get test results for an agent."""
    try:
        # Verify agent belongs to user
        if not agent_id.startswith(f"user_{current_user.user_id}_"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if agent_id not in test_results_db:
            return []
        
        results = test_results_db[agent_id][:limit]
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get test results for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve test results")

async def deploy_agent(
    deployment_request: DeploymentRequest,
    background_tasks: BackgroundTasks,
    current_user: UserProfile = Depends(get_current_user)
) -> Dict[str, Any]:
    """Deploy an agent to production."""
    try:
        agent_id = deployment_request.agent_id
        
        # Verify agent belongs to user
        if not agent_id.startswith(f"user_{current_user.user_id}_"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if agent_id not in agents_db:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent = agents_db[agent_id]
        
        # Check if agent is ready for deployment
        if agent.safety_score < 0.8:
            raise HTTPException(
                status_code=400, 
                detail="Agent safety score too low for deployment. Minimum required: 80%"
            )
        
        # Update agent status and deployment URLs
        agent.status = "deployed"
        agent.deployment_url = f"https://api.agentguard.com/agents/{agent_id}"
        agent.webhook_url = f"https://api.agentguard.com/webhooks/{agent_id}"
        agent.updated_at = datetime.utcnow().isoformat()
        
        agents_db[agent_id] = agent
        
        # Schedule background deployment tasks
        background_tasks.add_task(_deploy_agent_infrastructure, agent_id, deployment_request)
        
        logger.info(f"Deployed agent {agent_id} for user {current_user.user_id}")
        
        return {
            "status": "deployed",
            "agent_id": agent_id,
            "deployment_url": agent.deployment_url,
            "webhook_url": agent.webhook_url,
            "message": "Agent deployed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deploy agent {deployment_request.agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to deploy agent")

async def get_agent_metrics(
    agent_id: str,
    days: int = 7,
    current_user: UserProfile = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get metrics for a deployed agent."""
    try:
        # Verify agent belongs to user
        if not agent_id.startswith(f"user_{current_user.user_id}_"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if agent_id not in agents_db:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent = agents_db[agent_id]
        
        if agent.status != "deployed":
            raise HTTPException(status_code=400, detail="Agent is not deployed")
        
        # Mock metrics (in production, get from monitoring system)
        import random
        
        base_requests = random.randint(500, 2000)
        metrics = {
            "agent_id": agent_id,
            "period_days": days,
            "total_requests": base_requests,
            "successful_requests": int(base_requests * random.uniform(0.95, 0.99)),
            "failed_requests": int(base_requests * random.uniform(0.01, 0.05)),
            "average_response_time_ms": random.uniform(50, 150),
            "average_safety_score": random.uniform(0.85, 0.98),
            "uptime_percentage": random.uniform(99.5, 99.9),
            "recent_activity": [
                {
                    "timestamp": (datetime.utcnow() - timedelta(minutes=i*5)).isoformat(),
                    "event": random.choice([
                        "Agent responded to user query",
                        "Safety validation passed",
                        "High confidence response generated",
                        "Response flagged for review"
                    ]),
                    "status": random.choice(["success", "success", "success", "warning"])
                }
                for i in range(10)
            ]
        }
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agent metrics")

async def delete_agent(
    agent_id: str,
    current_user: UserProfile = Depends(get_current_user)
) -> Dict[str, str]:
    """Delete an agent."""
    try:
        # Verify agent belongs to user
        if not agent_id.startswith(f"user_{current_user.user_id}_"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if agent_id not in agents_db:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent = agents_db[agent_id]
        
        # Can't delete deployed agents without undeploying first
        if agent.status == "deployed":
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete deployed agent. Undeploy first."
            )
        
        # Delete agent and test results
        del agents_db[agent_id]
        if agent_id in test_results_db:
            del test_results_db[agent_id]
        
        logger.info(f"Deleted agent {agent_id} for user {current_user.user_id}")
        
        return {"status": "success", "message": "Agent deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete agent")

# Helper functions
async def _calculate_safety_score(config: AgentConfig) -> float:
    """Calculate safety score based on agent configuration."""
    score = 0.5  # Base score
    
    # Add points for safety rules
    score += min(len(config.safety_rules) * 0.1, 0.3)
    
    # Add points for conservative temperature
    if config.temperature < 0.5:
        score += 0.1
    elif config.temperature < 0.8:
        score += 0.05
    
    # Add points for reasonable token limits
    if config.max_tokens < 2000:
        score += 0.1
    
    # Add points for system prompt mentioning safety
    if any(word in config.system_prompt.lower() for word in ['safe', 'accurate', 'careful', 'responsible']):
        score += 0.1
    
    return min(score, 1.0)

async def _deploy_agent_infrastructure(agent_id: str, deployment_request: DeploymentRequest):
    """Background task to deploy agent infrastructure."""
    try:
        # Mock deployment process
        import asyncio
        await asyncio.sleep(5)  # Simulate deployment time
        
        logger.info(f"Agent {agent_id} infrastructure deployed successfully")
        
    except Exception as e:
        logger.error(f"Failed to deploy infrastructure for agent {agent_id}: {e}")
        # In production, update agent status to failed and notify user
