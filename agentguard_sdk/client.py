"""
AgentGuard Client
Main client class for interacting with the AgentGuard API.

Author: AgentGuard Engineering Team
Date: October 2025
Version: 2.0.0
"""

import requests
from typing import Optional, List, Dict, Any
from .models import (
    DetectionResult,
    MultimodalResult,
    BiasAuditResult,
    RedTeamReport,
    ComplianceReport
)
from .exceptions import (
    AgentGuardError,
    AuthenticationError,
    RateLimitError,
    ValidationError
)


class AgentGuardClient:
    """
    Official Python client for AgentGuard AI Safety Platform.
    
    Features:
    - Hallucination detection
    - Prompt injection prevention
    - PII protection
    - RAG security
    - Multimodal detection
    - Bias auditing
    - Red teaming
    - Compliance reporting
    
    Example:
        >>> from agentguard_sdk import AgentGuardClient
        >>> client = AgentGuardClient(api_key="your-api-key")
        >>> result = client.detect_hallucination("Agent output to check")
        >>> print(result.is_hallucination)
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://agentguard.onrender.com",
        timeout: int = 30
    ):
        """
        Initialize AgentGuard client.
        
        Args:
            api_key: Your AgentGuard API key
            base_url: Base URL for AgentGuard API
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "AgentGuard-Python-SDK/2.0.0"
        })
        
        # Service clients
        self.multimodal = MultimodalClient(self)
        self.bias = BiasClient(self)
        self.redteam = RedTeamClient(self)
        self.compliance = ComplianceClient(self)
        self.rag = RAGSecurityClient(self)
        self.pii = PIIProtectionClient(self)
        self.prompt_injection = PromptInjectionClient(self)
    
    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request to AgentGuard API."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            
            # Handle errors
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            elif response.status_code == 422:
                raise ValidationError(f"Validation error: {response.text}")
            elif response.status_code >= 400:
                raise AgentGuardError(f"API error: {response.status_code} - {response.text}")
            
            return response.json()
        
        except requests.exceptions.Timeout:
            raise AgentGuardError("Request timed out")
        except requests.exceptions.ConnectionError:
            raise AgentGuardError("Connection error")
        except requests.exceptions.RequestException as e:
            raise AgentGuardError(f"Request failed: {str(e)}")
    
    def detect_hallucination(
        self,
        agent_output: str,
        agent_input: Optional[str] = None,
        context: Optional[str] = None,
        strategy: str = "weighted"
    ) -> DetectionResult:
        """
        Detect hallucinations in agent output.
        
        Args:
            agent_output: The agent's output to check
            agent_input: Optional input that led to the output
            context: Optional additional context
            strategy: Voting strategy (weighted, majority, adaptive, etc.)
            
        Returns:
            DetectionResult with detection details
        """
        data = {
            "agent_output": agent_output,
            "agent_input": agent_input,
            "context": context,
            "strategy": strategy
        }
        
        response = self._request("POST", "/multi-model/detect", json=data)
        return DetectionResult(**response)
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        return self._request("GET", "/health")


class MultimodalClient:
    """Client for multimodal detection features."""
    
    def __init__(self, client: AgentGuardClient):
        self.client = client
    
    def detect(
        self,
        text_content: str,
        image_url: Optional[str] = None,
        video_url: Optional[str] = None,
        audio_url: Optional[str] = None
    ) -> MultimodalResult:
        """
        Detect hallucinations in multimodal content.
        
        Args:
            text_content: Text description to verify
            image_url: Optional image URL
            video_url: Optional video URL
            audio_url: Optional audio URL
            
        Returns:
            MultimodalResult with consistency analysis
        """
        data = {
            "text_content": text_content,
            "image_url": image_url,
            "video_url": video_url,
            "audio_url": audio_url
        }
        
        response = self.client._request("POST", "/multimodal/detect", json=data)
        return MultimodalResult(**response)


class BiasClient:
    """Client for bias and fairness auditing."""
    
    def __init__(self, client: AgentGuardClient):
        self.client = client
    
    def audit(
        self,
        text: str,
        context: Optional[str] = None,
        check_compliance: bool = True
    ) -> BiasAuditResult:
        """
        Perform bias and fairness audit.
        
        Args:
            text: Text to audit for bias
            context: Optional context
            check_compliance: Whether to check regulatory compliance
            
        Returns:
            BiasAuditResult with audit findings
        """
        data = {
            "text": text,
            "context": context,
            "check_compliance": check_compliance
        }
        
        response = self.client._request("POST", "/bias/audit", json=data)
        return BiasAuditResult(**response)
    
    def check_inclusive_language(self, text: str) -> Dict[str, Any]:
        """Quick check for non-inclusive language."""
        response = self.client._request(
            "POST",
            "/bias/check-inclusive-language",
            params={"text": text}
        )
        return response


class RedTeamClient:
    """Client for red teaming and security testing."""
    
    def __init__(self, client: AgentGuardClient):
        self.client = client
    
    def simulate(
        self,
        attack_types: Optional[List[str]] = None,
        severity_threshold: str = "low",
        max_attacks: int = 50
    ) -> RedTeamReport:
        """
        Run red team simulation.
        
        Args:
            attack_types: Specific attack types to test
            severity_threshold: Minimum severity (low, medium, high, critical)
            max_attacks: Maximum number of attacks to execute
            
        Returns:
            RedTeamReport with vulnerability assessment
        """
        data = {
            "attack_types": attack_types,
            "severity_threshold": severity_threshold,
            "max_attacks": max_attacks
        }
        
        response = self.client._request("POST", "/redteam/simulate", json=data)
        return RedTeamReport(**response)
    
    def test_single_attack(
        self,
        payload: str,
        attack_type: str = "prompt_injection"
    ) -> Dict[str, Any]:
        """Test a single attack payload."""
        data = {
            "payload": payload,
            "attack_type": attack_type
        }
        
        return self.client._request("POST", "/redteam/test-single-attack", json=data)


class ComplianceClient:
    """Client for compliance reporting."""
    
    def __init__(self, client: AgentGuardClient):
        self.client = client
    
    def generate_report(
        self,
        framework: str = "all",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        include_details: bool = True
    ) -> ComplianceReport:
        """
        Generate compliance report.
        
        Args:
            framework: Framework to report on (all, eu_ai_act, nist, owasp, gdpr, ieee)
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)
            include_details: Whether to include detailed findings
            
        Returns:
            ComplianceReport with compliance assessment
        """
        data = {
            "framework": framework,
            "start_date": start_date,
            "end_date": end_date,
            "include_details": include_details
        }
        
        response = self.client._request("POST", "/compliance/report", json=data)
        return ComplianceReport(**response)
    
    def get_status(self) -> Dict[str, Any]:
        """Get quick compliance status."""
        return self.client._request("GET", "/compliance/status")


class RAGSecurityClient:
    """Client for RAG security features."""
    
    def __init__(self, client: AgentGuardClient):
        self.client = client
    
    def analyze(
        self,
        retrieved_contexts: List[Dict[str, Any]],
        query: str,
        user_id: Optional[str] = None,
        enable_sanitization: bool = True
    ) -> Dict[str, Any]:
        """Analyze retrieved contexts for security threats."""
        data = {
            "retrieved_contexts": retrieved_contexts,
            "query": query,
            "user_id": user_id,
            "enable_sanitization": enable_sanitization
        }
        
        return self.client._request("POST", "/rag-security/analyze", json=data)


class PIIProtectionClient:
    """Client for PII protection features."""
    
    def __init__(self, client: AgentGuardClient):
        self.client = client
    
    def detect(
        self,
        text: str,
        redact: bool = True
    ) -> Dict[str, Any]:
        """Detect and optionally redact PII."""
        data = {
            "text": text,
            "redact": redact
        }
        
        return self.client._request("POST", "/pii-protection/detect", json=data)


class PromptInjectionClient:
    """Client for prompt injection detection."""
    
    def __init__(self, client: AgentGuardClient):
        self.client = client
    
    def detect(
        self,
        prompt: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Detect prompt injection attacks."""
        data = {
            "prompt": prompt,
            "context": context
        }
        
        return self.client._request("POST", "/prompt-injection/detect", json=data)
