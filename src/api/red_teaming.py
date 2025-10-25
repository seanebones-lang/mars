"""
Red Teaming API Endpoints
FastAPI endpoints for automated adversarial testing.

Author: AgentGuard Engineering Team
Date: October 2025
Version: 1.0.0
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List
from pydantic import BaseModel
import logging

from src.services.red_team_simulator import (
    get_red_team_simulator,
    AttackType,
    AttackSeverity
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/redteam", tags=["red-teaming"])


class RedTeamSimulationRequest(BaseModel):
    """Request for red team simulation."""
    target_endpoint: Optional[str] = None
    attack_types: Optional[List[str]] = None
    severity_threshold: str = "low"
    max_attacks: int = 50


class RedTeamSimulationResponse(BaseModel):
    """Response from red team simulation."""
    total_attacks: int
    successful_attacks: int
    blocked_attacks: int
    detection_rate: float
    vulnerability_summary: dict
    risk_score: float
    recommendations: List[str]
    compliance_gaps: List[str]
    processing_time_ms: float


@router.post("/simulate", response_model=RedTeamSimulationResponse)
async def run_simulation(request: RedTeamSimulationRequest):
    """
    Run comprehensive red team simulation.
    
    Tests system against:
    - Prompt injection attacks
    - Jailbreak attempts
    - Data extraction attacks
    - Bias exploitation
    - RAG poisoning
    - PII leakage tests
    - Hallucination inducement
    - Context manipulation
    - Role confusion
    - Encoding obfuscation
    
    Returns comprehensive vulnerability assessment with OWASP LLM Top 10 coverage.
    """
    try:
        simulator = get_red_team_simulator()
        
        # Parse attack types
        attack_types = None
        if request.attack_types:
            attack_types = [AttackType(at) for at in request.attack_types]
        
        # Parse severity
        severity_threshold = AttackSeverity(request.severity_threshold)
        
        # Create mock target system (in production, this would be the actual system)
        class MockTarget:
            async def detect(self, prompt: str):
                class Result:
                    is_injection = any(w in prompt.lower() for w in ['ignore', 'bypass', 'reveal'])
                    confidence = 0.85 if is_injection else 0.15
                return Result()
        
        target_system = MockTarget()
        
        # Run simulation
        report = await simulator.run_simulation(
            target_system=target_system,
            attack_types=attack_types,
            severity_threshold=severity_threshold
        )
        
        return RedTeamSimulationResponse(
            total_attacks=report.total_attacks,
            successful_attacks=report.successful_attacks,
            blocked_attacks=report.blocked_attacks,
            detection_rate=report.detection_rate,
            vulnerability_summary={k.value: v for k, v in report.vulnerability_summary.items()},
            risk_score=report.risk_score,
            recommendations=report.recommendations,
            compliance_gaps=report.compliance_gaps,
            processing_time_ms=report.processing_time_ms
        )
    
    except Exception as e:
        logger.error(f"Red team simulation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@router.get("/attack-vectors")
async def get_attack_vectors():
    """Get list of available attack vectors."""
    simulator = get_red_team_simulator()
    
    return {
        "total_vectors": len(simulator.attack_vectors),
        "attack_types": [at.value for at in AttackType],
        "severity_levels": [sl.value for sl in AttackSeverity],
        "vectors": [
            {
                "attack_id": v.attack_id,
                "attack_type": v.attack_type.value,
                "severity": v.severity.value,
                "description": v.description,
                "owasp_category": v.owasp_category
            }
            for v in simulator.attack_vectors[:20]  # Return first 20
        ]
    }


@router.post("/test-single-attack")
async def test_single_attack(
    payload: str,
    attack_type: str = "prompt_injection"
):
    """
    Test a single attack payload.
    
    Useful for testing specific attack scenarios.
    """
    try:
        simulator = get_red_team_simulator()
        
        # Create mock target
        class MockTarget:
            async def detect(self, prompt: str):
                class Result:
                    is_injection = any(w in prompt.lower() for w in ['ignore', 'bypass', 'reveal'])
                    confidence = 0.85 if is_injection else 0.15
                return Result()
        
        target_system = MockTarget()
        
        # Create attack vector
        from src.services.red_team_simulator import AttackVector
        vector = AttackVector(
            attack_id="custom-001",
            attack_type=AttackType(attack_type),
            severity=AttackSeverity.MEDIUM,
            payload=payload,
            description="Custom test attack",
            expected_behavior="Should be detected",
            owasp_category="Custom"
        )
        
        # Execute attack
        result = await simulator._execute_attack(target_system, vector)
        
        return {
            "was_detected": result.was_detected,
            "success_status": result.success_status.value,
            "detection_confidence": result.detection_confidence,
            "vulnerabilities_found": result.vulnerabilities_found,
            "recommendations": result.recommendations,
            "response_time_ms": result.response_time_ms
        }
    
    except Exception as e:
        logger.error(f"Single attack test error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


@router.get("/health")
async def redteam_health():
    """Health check for red teaming service."""
    try:
        simulator = get_red_team_simulator()
        return {
            "status": "healthy",
            "service": "red_teaming",
            "total_simulations": simulator.total_simulations,
            "total_vulnerabilities_found": simulator.total_vulnerabilities_found,
            "attack_vectors_loaded": len(simulator.attack_vectors)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

