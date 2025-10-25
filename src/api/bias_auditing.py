"""
Bias and Fairness Auditing API Endpoints
FastAPI endpoints for bias detection and fairness assessment.

Author: AgentGuard Engineering Team
Date: October 2025
Version: 1.0.0
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List
from pydantic import BaseModel
import logging

from src.services.bias_fairness_auditor import (
    get_bias_auditor,
    BiasType,
    BiasLevel,
    FairnessMetric
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bias", tags=["bias-fairness"])


class BiasAuditRequest(BaseModel):
    """Request for bias audit."""
    text: str
    context: Optional[str] = None
    check_compliance: bool = True


class BiasAuditResponse(BaseModel):
    """Response from bias audit."""
    has_bias: bool
    overall_bias_level: str
    bias_indicators: List[dict]
    fairness_scores: List[dict]
    detected_bias_types: List[str]
    overall_fairness_score: float
    recommendations: List[str]
    compliance_status: dict
    processing_time_ms: float


@router.post("/audit", response_model=BiasAuditResponse)
async def audit_bias(request: BiasAuditRequest):
    """
    Perform comprehensive bias and fairness audit.
    
    Detects:
    - Gender bias and stereotypes
    - Racial/ethnic bias
    - Age discrimination
    - Disability bias (ableist language)
    - Religious bias
    - Socioeconomic bias
    - LGBTQ+ discrimination
    - Geographic bias
    - Language inclusivity issues
    
    Returns detailed analysis with compliance status for:
    - EU AI Act
    - NIST AI RMF
    - IEEE 7000
    """
    try:
        auditor = get_bias_auditor()
        
        result = await auditor.audit(
            text=request.text,
            context=request.context,
            check_compliance=request.check_compliance
        )
        
        return BiasAuditResponse(
            has_bias=result.has_bias,
            overall_bias_level=result.overall_bias_level.value,
            bias_indicators=[
                {
                    "bias_type": ind.bias_type.value,
                    "indicator_text": ind.indicator_text,
                    "context": ind.context,
                    "severity": ind.severity.value,
                    "confidence": ind.confidence,
                    "explanation": ind.explanation,
                    "suggested_alternative": ind.suggested_alternative
                }
                for ind in result.bias_indicators
            ],
            fairness_scores=[
                {
                    "metric": score.metric.value,
                    "score": score.score,
                    "explanation": score.explanation,
                    "affected_groups": score.affected_groups
                }
                for score in result.fairness_scores
            ],
            detected_bias_types=[bt.value for bt in result.detected_bias_types],
            overall_fairness_score=result.overall_fairness_score,
            recommendations=result.recommendations,
            compliance_status=result.compliance_status,
            processing_time_ms=result.processing_time_ms
        )
    
    except Exception as e:
        logger.error(f"Bias audit error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Audit failed: {str(e)}")


@router.post("/check-inclusive-language")
async def check_inclusive_language(text: str):
    """
    Quick check for non-inclusive language.
    
    Returns suggestions for more inclusive alternatives.
    """
    try:
        auditor = get_bias_auditor()
        
        result = await auditor.audit(text=text, check_compliance=False)
        
        # Filter for language-specific issues
        language_issues = [
            ind for ind in result.bias_indicators
            if ind.bias_type == BiasType.LANGUAGE
        ]
        
        return {
            "has_issues": len(language_issues) > 0,
            "issues_found": len(language_issues),
            "suggestions": [
                {
                    "term": ind.indicator_text,
                    "alternative": ind.suggested_alternative,
                    "explanation": ind.explanation
                }
                for ind in language_issues
            ]
        }
    
    except Exception as e:
        logger.error(f"Language check error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Check failed: {str(e)}")


@router.get("/bias-types")
async def get_bias_types():
    """Get list of supported bias types."""
    return {
        "bias_types": [bt.value for bt in BiasType],
        "bias_levels": [bl.value for bl in BiasLevel],
        "fairness_metrics": [fm.value for fm in FairnessMetric]
    }


@router.get("/health")
async def bias_health():
    """Health check for bias auditing service."""
    try:
        auditor = get_bias_auditor()
        return {
            "status": "healthy",
            "service": "bias_auditing",
            "stereotype_detection": auditor.enable_stereotype_detection,
            "representation_analysis": auditor.enable_representation_analysis,
            "language_inclusivity": auditor.enable_language_inclusivity
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

