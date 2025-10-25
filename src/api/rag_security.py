"""
RAG Security API
REST API endpoints for securing Retrieval-Augmented Generation systems.

Author: AgentGuard Engineering Team
Date: October 2025
Version: 1.0.0
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from datetime import datetime

from ..services.rag_security import (
    get_rag_security_service,
    RAGSecurityService,
    ThreatType,
    RiskLevel,
    KnowledgeBaseType,
    KnowledgeBaseConfig,
    RetrievedContext,
    SecurityThreat,
    RAGSecurityResult
)

router = APIRouter(
    prefix="/rag-security",
    tags=["rag_security"],
    responses={404: {"description": "Not found"}}
)


# Request/Response Models

class RetrievedContextRequest(BaseModel):
    """Request model for retrieved context."""
    kb_id: str = Field(..., description="Knowledge base ID")
    content: str = Field(..., description="Retrieved content")
    source: str = Field(..., description="Source of the content")
    relevance_score: float = Field(..., description="Relevance score", ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AnalyzeRAGContextRequest(BaseModel):
    """Request model for RAG context analysis."""
    retrieved_contexts: List[RetrievedContextRequest] = Field(..., description="List of retrieved contexts")
    query: str = Field(..., description="Original user query")
    user_id: Optional[str] = Field(None, description="Optional user ID for access control")
    enable_sanitization: bool = Field(True, description="Whether to sanitize detected threats")


class SecurityThreatResponse(BaseModel):
    """Response model for a security threat."""
    threat_type: ThreatType
    risk_level: RiskLevel
    confidence: float
    description: str
    affected_context: Optional[str]
    recommendation: str
    evidence: Dict[str, Any]


class RAGSecurityResponse(BaseModel):
    """Response model for RAG security analysis."""
    is_safe: bool
    risk_level: RiskLevel
    threats_detected: List[SecurityThreatResponse]
    sanitized_context: str
    original_context: str
    hallucination_score: float
    trust_score: float
    processing_time_ms: float
    recommendations: List[str]
    timestamp: datetime

    @classmethod
    def from_service_result(cls, result: RAGSecurityResult):
        """Create response from service result."""
        return cls(
            is_safe=result.is_safe,
            risk_level=result.risk_level,
            threats_detected=[
                SecurityThreatResponse(
                    threat_type=t.threat_type,
                    risk_level=t.risk_level,
                    confidence=t.confidence,
                    description=t.description,
                    affected_context=t.affected_context,
                    recommendation=t.recommendation,
                    evidence=t.evidence
                )
                for t in result.threats_detected
            ],
            sanitized_context=result.sanitized_context,
            original_context=result.original_context,
            hallucination_score=result.hallucination_score,
            trust_score=result.trust_score,
            processing_time_ms=result.processing_time_ms,
            recommendations=result.recommendations,
            timestamp=result.timestamp
        )


class KnowledgeBaseConfigRequest(BaseModel):
    """Request model for knowledge base configuration."""
    kb_id: str = Field(..., description="Unique knowledge base ID")
    kb_type: KnowledgeBaseType = Field(..., description="Type of knowledge base")
    name: str = Field(..., description="Knowledge base name")
    description: str = Field(..., description="Description")
    enabled: bool = Field(True, description="Whether KB is enabled")
    requires_auth: bool = Field(True, description="Whether KB requires authentication")
    allowed_users: List[str] = Field(default_factory=list, description="List of allowed user IDs")
    max_context_length: int = Field(4096, description="Maximum context length", ge=1, le=100000)
    enable_pii_filtering: bool = Field(True, description="Enable PII filtering")
    enable_hallucination_check: bool = Field(True, description="Enable hallucination checking")
    trust_score: float = Field(1.0, description="Trust score for this KB", ge=0.0, le=1.0)


class KnowledgeBaseConfigResponse(BaseModel):
    """Response model for knowledge base configuration."""
    kb_id: str
    kb_type: KnowledgeBaseType
    name: str
    description: str
    enabled: bool
    requires_auth: bool
    allowed_users: List[str]
    max_context_length: int
    enable_pii_filtering: bool
    enable_hallucination_check: bool
    trust_score: float


class AccessLogResponse(BaseModel):
    """Response model for access log entry."""
    timestamp: str
    user_id: Optional[str]
    kb_ids: List[str]
    threats_count: int
    is_safe: bool
    threat_types: List[str]


# Dependency
def get_rag_service() -> RAGSecurityService:
    """Get RAG security service instance."""
    return get_rag_security_service()


# API Endpoints

@router.post("/analyze", response_model=RAGSecurityResponse, status_code=status.HTTP_200_OK)
async def analyze_rag_context(
    request: AnalyzeRAGContextRequest,
    service: RAGSecurityService = Depends(get_rag_service)
):
    """
    Analyze retrieved RAG context for security threats.
    
    Detects:
    - Context poisoning attacks
    - Data leakage (PII, credentials)
    - Injection attacks (SQL, XSS, code)
    - Supply chain vulnerabilities
    - Hallucinations
    - Unauthorized access
    
    **Example Request:**
    ```json
    {
        "retrieved_contexts": [
            {
                "kb_id": "kb-001",
                "content": "Paris is the capital of France.",
                "source": "geography_db",
                "relevance_score": 0.95
            }
        ],
        "query": "What is the capital of France?",
        "user_id": "user-123",
        "enable_sanitization": true
    }
    ```
    
    **Example Response:**
    ```json
    {
        "is_safe": true,
        "risk_level": "low",
        "threats_detected": [],
        "sanitized_context": "Paris is the capital of France.",
        "hallucination_score": 0.1,
        "trust_score": 0.95,
        "processing_time_ms": 45.2,
        "recommendations": ["Context appears safe for use"]
    }
    ```
    """
    try:
        # Convert request contexts to service format
        contexts = [
            RetrievedContext(
                kb_id=ctx.kb_id,
                content=ctx.content,
                source=ctx.source,
                relevance_score=ctx.relevance_score,
                timestamp=datetime.utcnow(),
                metadata=ctx.metadata
            )
            for ctx in request.retrieved_contexts
        ]
        
        result = await service.analyze_rag_context(
            retrieved_contexts=contexts,
            query=request.query,
            user_id=request.user_id,
            enable_sanitization=request.enable_sanitization
        )
        
        return RAGSecurityResponse.from_service_result(result)
    
    except Exception as e:
        logger.error(f"Error in analyze_rag_context: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze RAG context: {str(e)}"
        )


@router.post("/knowledge-bases", status_code=status.HTTP_201_CREATED)
async def register_knowledge_base(
    request: KnowledgeBaseConfigRequest,
    service: RAGSecurityService = Depends(get_rag_service)
):
    """
    Register a knowledge base for security monitoring.
    
    **Example Request:**
    ```json
    {
        "kb_id": "kb-001",
        "kb_type": "vector_db",
        "name": "Company Documentation",
        "description": "Internal company docs and policies",
        "enabled": true,
        "requires_auth": true,
        "allowed_users": ["user-123", "user-456"],
        "trust_score": 0.95
    }
    ```
    """
    try:
        config = KnowledgeBaseConfig(
            kb_id=request.kb_id,
            kb_type=request.kb_type,
            name=request.name,
            description=request.description,
            enabled=request.enabled,
            requires_auth=request.requires_auth,
            allowed_users=request.allowed_users,
            max_context_length=request.max_context_length,
            enable_pii_filtering=request.enable_pii_filtering,
            enable_hallucination_check=request.enable_hallucination_check,
            trust_score=request.trust_score
        )
        
        service.register_knowledge_base(config)
        
        return {
            "status": "success",
            "message": f"Knowledge base {request.name} registered successfully",
            "kb_id": request.kb_id
        }
    
    except Exception as e:
        logger.error(f"Error in register_knowledge_base: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register knowledge base: {str(e)}"
        )


@router.get("/knowledge-bases", response_model=List[KnowledgeBaseConfigResponse], status_code=status.HTTP_200_OK)
async def list_knowledge_bases(
    service: RAGSecurityService = Depends(get_rag_service)
):
    """
    List all registered knowledge bases.
    
    **Example Response:**
    ```json
    [
        {
            "kb_id": "kb-001",
            "kb_type": "vector_db",
            "name": "Company Documentation",
            "description": "Internal company docs",
            "enabled": true,
            "requires_auth": true,
            "allowed_users": ["user-123"],
            "trust_score": 0.95
        }
    ]
    ```
    """
    try:
        kbs = service.get_knowledge_bases()
        return [
            KnowledgeBaseConfigResponse(
                kb_id=kb.kb_id,
                kb_type=kb.kb_type,
                name=kb.name,
                description=kb.description,
                enabled=kb.enabled,
                requires_auth=kb.requires_auth,
                allowed_users=kb.allowed_users,
                max_context_length=kb.max_context_length,
                enable_pii_filtering=kb.enable_pii_filtering,
                enable_hallucination_check=kb.enable_hallucination_check,
                trust_score=kb.trust_score
            )
            for kb in kbs
        ]
    
    except Exception as e:
        logger.error(f"Error in list_knowledge_bases: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list knowledge bases: {str(e)}"
        )


@router.delete("/knowledge-bases/{kb_id}", status_code=status.HTTP_200_OK)
async def unregister_knowledge_base(
    kb_id: str,
    service: RAGSecurityService = Depends(get_rag_service)
):
    """
    Unregister a knowledge base.
    
    **Example Response:**
    ```json
    {
        "status": "success",
        "message": "Knowledge base kb-001 unregistered successfully"
    }
    ```
    """
    try:
        service.unregister_knowledge_base(kb_id)
        return {
            "status": "success",
            "message": f"Knowledge base {kb_id} unregistered successfully"
        }
    
    except Exception as e:
        logger.error(f"Error in unregister_knowledge_base: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unregister knowledge base: {str(e)}"
        )


@router.get("/access-logs", response_model=List[AccessLogResponse], status_code=status.HTTP_200_OK)
async def get_access_logs(
    limit: int = 100,
    service: RAGSecurityService = Depends(get_rag_service)
):
    """
    Get recent access logs for audit trail.
    
    **Example Response:**
    ```json
    [
        {
            "timestamp": "2025-10-25T12:34:56",
            "user_id": "user-123",
            "kb_ids": ["kb-001", "kb-002"],
            "threats_count": 0,
            "is_safe": true,
            "threat_types": []
        }
    ]
    ```
    """
    try:
        logs = service.get_access_logs(limit=limit)
        return [AccessLogResponse(**log) for log in logs]
    
    except Exception as e:
        logger.error(f"Error in get_access_logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get access logs: {str(e)}"
        )


@router.get("/threat-types", response_model=List[str], status_code=status.HTTP_200_OK)
async def list_threat_types():
    """
    List all supported threat types.
    
    **Example Response:**
    ```json
    [
        "context_poisoning",
        "data_leakage",
        "unauthorized_access",
        "supply_chain_attack",
        "hallucination",
        "injection_attack"
    ]
    ```
    """
    return [threat_type.value for threat_type in ThreatType]


@router.get("/risk-levels", response_model=List[str], status_code=status.HTTP_200_OK)
async def list_risk_levels():
    """
    List all risk levels.
    
    **Example Response:**
    ```json
    ["low", "medium", "high", "critical"]
    ```
    """
    return [risk_level.value for risk_level in RiskLevel]


@router.get("/kb-types", response_model=List[str], status_code=status.HTTP_200_OK)
async def list_kb_types():
    """
    List all supported knowledge base types.
    
    **Example Response:**
    ```json
    [
        "vector_db",
        "sql_database",
        "document_store",
        "api_endpoint",
        "file_system"
    ]
    ```
    """
    return [kb_type.value for kb_type in KnowledgeBaseType]


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint for RAG security service.
    
    **Example Response:**
    ```json
    {
        "status": "healthy",
        "service": "rag_security",
        "version": "1.0.0",
        "knowledge_bases_registered": 5
    }
    ```
    """
    service = get_rag_service()
    kbs = service.get_knowledge_bases()
    
    return {
        "status": "healthy",
        "service": "rag_security",
        "version": "1.0.0",
        "knowledge_bases_registered": len(kbs)
    }


# Add logger import
import logging
logger = logging.getLogger(__name__)

