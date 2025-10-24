"""
AgentGuard Python SDK Client
Main client class for interacting with the AgentGuard API.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Union, AsyncGenerator
from urllib.parse import urljoin
import httpx
import websockets

from .models import (
    AgentTestRequest, HallucinationReport, Agent, AgentConfig, 
    TestResult, DeploymentRequest, SafetyRule
)
from .exceptions import (
    AgentGuardError, AuthenticationError, ValidationError, 
    DeploymentError, RateLimitError
)


class AgentGuardClient:
    """
    AgentGuard Python SDK Client
    
    Provides enterprise-grade Python integration for AI agent safety validation,
    agent management, deployment, and real-time monitoring.
    
    Example:
        ```python
        from agentguard_sdk import AgentGuardClient
        
        # Initialize client
        client = AgentGuardClient(
            api_key="your_api_key",
            base_url="https://api.agentguard.com"
        )
        
        # Test agent output for hallucinations
        result = await client.test_agent_output(
            agent_output="The capital of France is Paris.",
            context="Geography question",
            expected_behavior="Accurate factual response"
        )
        
        print(f"Safety Score: {result.confidence:.2f}")
        print(f"Risk Level: {result.hallucination_risk:.2f}")
        ```
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.agentguard.com",
        timeout: int = 30,
        max_retries: int = 3,
        enable_websockets: bool = True
    ):
        """
        Initialize AgentGuard client.
        
        Args:
            api_key: Your AgentGuard API key
            base_url: Base URL for the AgentGuard API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            enable_websockets: Enable WebSocket connections for real-time updates
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.enable_websockets = enable_websockets
        
        # HTTP client configuration
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": f"AgentGuard-SDK/1.0.0"
            }
        )
        
        # WebSocket connection
        self._ws_connection = None
        self._ws_callbacks = {}
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close all connections."""
        await self.client.aclose()
        if self._ws_connection:
            await self._ws_connection.close()
    
    # Core Detection Methods
    
    async def test_agent_output(
        self,
        agent_output: str,
        context: Optional[str] = None,
        expected_behavior: Optional[str] = None,
        custom_rules: Optional[List[str]] = None
    ) -> HallucinationReport:
        """
        Test agent output for hallucinations and safety issues.
        
        Args:
            agent_output: The AI agent's output to test
            context: Optional context about the query/conversation
            expected_behavior: Expected behavior description
            custom_rules: Custom safety rules to apply
            
        Returns:
            HallucinationReport with safety analysis results
        """
        request_data = AgentTestRequest(
            agent_output=agent_output,
            context=context or "",
            expected_behavior=expected_behavior or "",
            custom_rules=custom_rules or []
        )
        
        response = await self._make_request(
            "POST", 
            "/test-agent", 
            data=request_data.dict()
        )
        
        return HallucinationReport(**response)
    
    async def batch_test_agents(
        self,
        test_requests: List[AgentTestRequest],
        callback: Optional[callable] = None
    ) -> List[HallucinationReport]:
        """
        Test multiple agent outputs in batch.
        
        Args:
            test_requests: List of test requests
            callback: Optional callback for progress updates
            
        Returns:
            List of HallucinationReport results
        """
        # Upload batch job
        batch_data = {
            "tests": [req.dict() for req in test_requests],
            "callback_url": None  # Could be implemented for webhooks
        }
        
        job_response = await self._make_request(
            "POST",
            "/batch/upload",
            data=batch_data
        )
        
        job_id = job_response["job_id"]
        
        # Start processing
        await self._make_request("POST", f"/batch/{job_id}/start")
        
        # Poll for completion
        while True:
            status_response = await self._make_request("GET", f"/batch/{job_id}")
            
            if callback:
                callback(status_response)
            
            if status_response["status"] == "completed":
                break
            elif status_response["status"] == "failed":
                raise ValidationError(f"Batch job failed: {status_response.get('error')}")
            
            await asyncio.sleep(2)  # Poll every 2 seconds
        
        # Get results
        results_response = await self._make_request("GET", f"/batch/{job_id}/results")
        
        return [HallucinationReport(**result) for result in results_response["results"]]
    
    # Agent Management Methods
    
    async def create_agent(self, config: AgentConfig) -> Agent:
        """
        Create a new AI agent with safety validation.
        
        Args:
            config: Agent configuration
            
        Returns:
            Created Agent object
        """
        response = await self._make_request(
            "POST",
            "/console/agents",
            data=config.dict()
        )
        
        return Agent(**response)
    
    async def get_agent(self, agent_id: str) -> Agent:
        """
        Get agent details by ID.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent object
        """
        response = await self._make_request("GET", f"/console/agents/{agent_id}")
        return Agent(**response)
    
    async def list_agents(self) -> List[Agent]:
        """
        List all agents for the current user.
        
        Returns:
            List of Agent objects
        """
        response = await self._make_request("GET", "/console/agents")
        return [Agent(**agent) for agent in response]
    
    async def update_agent(self, agent_id: str, config: AgentConfig) -> Agent:
        """
        Update agent configuration.
        
        Args:
            agent_id: Agent identifier
            config: Updated configuration
            
        Returns:
            Updated Agent object
        """
        response = await self._make_request(
            "PUT",
            f"/console/agents/{agent_id}",
            data=config.dict()
        )
        
        return Agent(**response)
    
    async def test_agent(self, agent_id: str, test_input: str) -> TestResult:
        """
        Test an agent with specific input.
        
        Args:
            agent_id: Agent identifier
            test_input: Input to test the agent with
            
        Returns:
            TestResult object
        """
        response = await self._make_request(
            "POST",
            f"/console/agents/{agent_id}/test",
            data={"input": test_input}
        )
        
        return TestResult(**response)
    
    async def deploy_agent(
        self,
        agent_id: str,
        environment: str = "production",
        auto_scale: bool = True,
        max_instances: int = 10
    ) -> Dict[str, str]:
        """
        Deploy an agent to production.
        
        Args:
            agent_id: Agent identifier
            environment: Deployment environment
            auto_scale: Enable auto-scaling
            max_instances: Maximum number of instances
            
        Returns:
            Deployment information
        """
        deployment_request = DeploymentRequest(
            agent_id=agent_id,
            environment=environment,
            auto_scale=auto_scale,
            max_instances=max_instances
        )
        
        response = await self._make_request(
            "POST",
            f"/console/agents/{agent_id}/deploy",
            data=deployment_request.dict()
        )
        
        return response
    
    async def get_agent_metrics(
        self,
        agent_id: str,
        days: int = 7
    ) -> Dict[str, any]:
        """
        Get metrics for a deployed agent.
        
        Args:
            agent_id: Agent identifier
            days: Number of days of metrics to retrieve
            
        Returns:
            Agent metrics data
        """
        response = await self._make_request(
            "GET",
            f"/console/agents/{agent_id}/metrics",
            params={"days": days}
        )
        
        return response
    
    async def delete_agent(self, agent_id: str) -> Dict[str, str]:
        """
        Delete an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Deletion confirmation
        """
        response = await self._make_request("DELETE", f"/console/agents/{agent_id}")
        return response
    
    # Real-time Monitoring Methods
    
    async def monitor_agent_realtime(
        self,
        agent_id: str,
        callback: callable
    ) -> None:
        """
        Monitor agent in real-time via WebSocket.
        
        Args:
            agent_id: Agent identifier
            callback: Function to call with real-time updates
        """
        if not self.enable_websockets:
            raise AgentGuardError("WebSocket support is disabled")
        
        ws_url = self.base_url.replace('http', 'ws') + f"/ws/agents/{agent_id}"
        
        async with websockets.connect(
            ws_url,
            extra_headers={"Authorization": f"Bearer {self.api_key}"}
        ) as websocket:
            self._ws_connection = websocket
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await callback(data)
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"Callback error: {e}")
    
    async def stream_system_metrics(self) -> AsyncGenerator[Dict[str, any], None]:
        """
        Stream system metrics in real-time.
        
        Yields:
            System metrics data
        """
        if not self.enable_websockets:
            raise AgentGuardError("WebSocket support is disabled")
        
        ws_url = self.base_url.replace('http', 'ws') + "/ws/metrics"
        
        async with websockets.connect(
            ws_url,
            extra_headers={"Authorization": f"Bearer {self.api_key}"}
        ) as websocket:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    yield data
                except json.JSONDecodeError:
                    continue
    
    # Analytics Methods
    
    async def get_analytics_overview(self, days: int = 30) -> Dict[str, any]:
        """
        Get analytics overview.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Analytics data
        """
        response = await self._make_request(
            "GET",
            "/analytics/insights",
            params={"days": days}
        )
        
        return response
    
    async def get_workstation_insights(self) -> Dict[str, any]:
        """
        Get workstation fleet insights.
        
        Returns:
            Workstation insights data
        """
        response = await self._make_request("GET", "/workstations/fleet/insights")
        return response
    
    # Utility Methods
    
    async def health_check(self) -> Dict[str, any]:
        """
        Check API health status.
        
        Returns:
            Health status information
        """
        response = await self._make_request("GET", "/health")
        return response
    
    async def get_system_metrics(self) -> Dict[str, any]:
        """
        Get current system metrics.
        
        Returns:
            System performance metrics
        """
        response = await self._make_request("GET", "/metrics")
        return response
    
    # Private Methods
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """Make HTTP request with error handling and retries."""
        url = urljoin(self.base_url, endpoint)
        
        for attempt in range(self.max_retries + 1):
            try:
                if method.upper() == "GET":
                    response = await self.client.get(url, params=params)
                elif method.upper() == "POST":
                    response = await self.client.post(url, json=data, params=params)
                elif method.upper() == "PUT":
                    response = await self.client.put(url, json=data, params=params)
                elif method.upper() == "DELETE":
                    response = await self.client.delete(url, params=params)
                else:
                    raise AgentGuardError(f"Unsupported HTTP method: {method}")
                
                # Handle response
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    raise AuthenticationError("Invalid API key or authentication failed")
                elif response.status_code == 429:
                    if attempt < self.max_retries:
                        wait_time = 2 ** attempt  # Exponential backoff
                        await asyncio.sleep(wait_time)
                        continue
                    raise RateLimitError("Rate limit exceeded")
                elif response.status_code == 422:
                    raise ValidationError(f"Validation error: {response.text}")
                elif response.status_code >= 500:
                    if attempt < self.max_retries:
                        wait_time = 2 ** attempt
                        await asyncio.sleep(wait_time)
                        continue
                    raise AgentGuardError(f"Server error: {response.status_code}")
                else:
                    raise AgentGuardError(f"HTTP {response.status_code}: {response.text}")
                    
            except httpx.RequestError as e:
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                    continue
                raise AgentGuardError(f"Request failed: {e}")
        
        raise AgentGuardError("Max retries exceeded")


# Synchronous wrapper for backwards compatibility
class AgentGuardSyncClient:
    """
    Synchronous wrapper for AgentGuardClient.
    
    Provides the same interface but with synchronous methods.
    """
    
    def __init__(self, *args, **kwargs):
        self._async_client = AgentGuardClient(*args, **kwargs)
    
    def test_agent_output(self, *args, **kwargs) -> HallucinationReport:
        """Synchronous version of test_agent_output."""
        return asyncio.run(self._async_client.test_agent_output(*args, **kwargs))
    
    def create_agent(self, *args, **kwargs) -> Agent:
        """Synchronous version of create_agent."""
        return asyncio.run(self._async_client.create_agent(*args, **kwargs))
    
    def get_agent(self, *args, **kwargs) -> Agent:
        """Synchronous version of get_agent."""
        return asyncio.run(self._async_client.get_agent(*args, **kwargs))
    
    def list_agents(self, *args, **kwargs) -> List[Agent]:
        """Synchronous version of list_agents."""
        return asyncio.run(self._async_client.list_agents(*args, **kwargs))
    
    def deploy_agent(self, *args, **kwargs) -> Dict[str, str]:
        """Synchronous version of deploy_agent."""
        return asyncio.run(self._async_client.deploy_agent(*args, **kwargs))
    
    def health_check(self, *args, **kwargs) -> Dict[str, any]:
        """Synchronous version of health_check."""
        return asyncio.run(self._async_client.health_check(*args, **kwargs))
    
    def close(self):
        """Close the client."""
        asyncio.run(self._async_client.close())
