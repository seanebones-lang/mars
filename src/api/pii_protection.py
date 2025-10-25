"""
PII Protection API
REST API endpoints for PII detection and redaction.

Author: AgentGuard Engineering Team
Date: October 2025
Version: 1.0.0
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from datetime import datetime

from ..services.pii_protection import (
    get_pii_protection_service,
    PIIProtectionService,
    PIIType,
    RedactionStrategy,
    ComplianceStandard,
    RedactionResult
)

router = APIRouter(
    prefix="/pii-protection",
    tags=["pii_protection"],
    responses={404: {"description": "Not found"}}
)


# Request/Response Models

class DetectPIIRequest(BaseModel):
    """Request model for PII detection."""
    text: str = Field(..., description="Text to scan for PII", min_length=1)
    compliance_standard: Optional[ComplianceStandard] = Field(
        None,
        description="Filter by compliance standard (HIPAA, GDPR, etc.)"
    )


class PIIDetectionResponse(BaseModel):
    """Response model for a single PII detection."""
    pii_type: PIIType
    pattern_id: str
    value: str
    start_pos: int
    end_pos: int
    confidence: float
    compliance_standards: List[ComplianceStandard]


class DetectPIIResponse(BaseModel):
    """Response model for PII detection."""
    text: str
    detections: List[PIIDetectionResponse]
    total_detections: int
    pii_types_found: List[PIIType]
    compliance_violations: List[ComplianceStandard]


class RedactPIIRequest(BaseModel):
    """Request model for PII redaction."""
    text: str = Field(..., description="Text to redact", min_length=1)
    strategy: Optional[Dict[PIIType, RedactionStrategy]] = Field(
        None,
        description="Custom redaction strategies per PII type"
    )
    compliance_standard: Optional[ComplianceStandard] = Field(
        None,
        description="Compliance standard to enforce"
    )


class RedactPIIResponse(BaseModel):
    """Response model for PII redaction."""
    original_text: str
    redacted_text: str
    detections: List[PIIDetectionResponse]
    redaction_map: Dict[str, str]
    compliance_violations: List[ComplianceStandard]
    processing_time_ms: float
    timestamp: datetime


class BatchRedactRequest(BaseModel):
    """Request model for batch PII redaction."""
    texts: List[str] = Field(..., description="List of texts to redact", min_items=1, max_items=100)
    strategy: Optional[Dict[PIIType, RedactionStrategy]] = Field(None, description="Redaction strategies")
    compliance_standard: Optional[ComplianceStandard] = Field(None, description="Compliance standard")


class BatchRedactResponse(BaseModel):
    """Response model for batch PII redaction."""
    results: List[RedactPIIResponse]
    total_texts: int
    total_detections: int
    total_processing_time_ms: float


class AddCustomPatternRequest(BaseModel):
    """Request model for adding custom PII pattern."""
    pattern_id: str = Field(..., description="Unique pattern identifier")
    pii_type: PIIType = Field(..., description="Type of PII")
    name: str = Field(..., description="Pattern name")
    regex: str = Field(..., description="Regular expression pattern")
    description: str = Field(..., description="Pattern description")
    compliance_standards: List[ComplianceStandard] = Field(..., description="Applicable compliance standards")
    default_strategy: RedactionStrategy = Field(RedactionStrategy.MASK, description="Default redaction strategy")


class PatternInfo(BaseModel):
    """Information about a PII detection pattern."""
    pattern_id: str
    pii_type: PIIType
    name: str
    description: str
    compliance_standards: List[ComplianceStandard]
    default_strategy: RedactionStrategy
    examples: List[str]


# Dependency
def get_pii_service() -> PIIProtectionService:
    """Get PII protection service instance."""
    return get_pii_protection_service()


# API Endpoints

@router.post("/detect", response_model=DetectPIIResponse, status_code=status.HTTP_200_OK)
async def detect_pii(
    request: DetectPIIRequest,
    service: PIIProtectionService = Depends(get_pii_service)
):
    """
    Detect PII in text without redaction.
    
    Scans text for personally identifiable information and returns
    all detections with their positions and types.
    
    **Example Request:**
    ```json
    {
        "text": "Contact John at john@example.com or 555-123-4567",
        "compliance_standard": "gdpr"
    }
    ```
    
    **Example Response:**
    ```json
    {
        "text": "Contact John at john@example.com or 555-123-4567",
        "detections": [
            {
                "pii_type": "email",
                "pattern_id": "pii-email",
                "value": "john@example.com",
                "start_pos": 16,
                "end_pos": 33,
                "confidence": 0.95,
                "compliance_standards": ["gdpr", "ccpa", "hipaa"]
            }
        ],
        "total_detections": 2,
        "pii_types_found": ["email", "phone"],
        "compliance_violations": ["gdpr"]
    }
    ```
    """
    try:
        detections = service.detect_pii(
            text=request.text,
            compliance_standard=request.compliance_standard
        )
        
        # Convert to response model
        detection_responses = [
            PIIDetectionResponse(
                pii_type=d.pii_type,
                pattern_id=d.pattern_id,
                value=d.value,
                start_pos=d.start_pos,
                end_pos=d.end_pos,
                confidence=d.confidence,
                compliance_standards=d.compliance_standards
            )
            for d in detections
        ]
        
        # Get unique PII types
        pii_types_found = list(set(d.pii_type for d in detections))
        
        # Get compliance violations
        compliance_violations = []
        if request.compliance_standard:
            compliance_violations = [
                request.compliance_standard
                for d in detections
                if request.compliance_standard in d.compliance_standards
            ]
            compliance_violations = list(set(compliance_violations))
        
        return DetectPIIResponse(
            text=request.text,
            detections=detection_responses,
            total_detections=len(detections),
            pii_types_found=pii_types_found,
            compliance_violations=compliance_violations
        )
    except Exception as e:
        logger.error(f"Error in detect_pii: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect PII: {str(e)}"
        )


@router.post("/redact", response_model=RedactPIIResponse, status_code=status.HTTP_200_OK)
async def redact_pii(
    request: RedactPIIRequest,
    service: PIIProtectionService = Depends(get_pii_service)
):
    """
    Detect and redact PII in text.
    
    Scans text for PII and returns redacted version with metadata.
    Supports multiple redaction strategies and compliance standards.
    
    **Example Request:**
    ```json
    {
        "text": "My email is john@example.com and SSN is 123-45-6789",
        "strategy": {
            "email": "mask",
            "ssn": "partial"
        },
        "compliance_standard": "hipaa"
    }
    ```
    
    **Example Response:**
    ```json
    {
        "original_text": "My email is john@example.com and SSN is 123-45-6789",
        "redacted_text": "My email is ***REDACTED*** and SSN is ***6789",
        "detections": [...],
        "redaction_map": {
            "john@example.com": "***REDACTED***",
            "123-45-6789": "***6789"
        },
        "compliance_violations": ["hipaa"],
        "processing_time_ms": 5.2
    }
    ```
    """
    try:
        result = service.redact_pii(
            text=request.text,
            strategy=request.strategy,
            compliance_standard=request.compliance_standard
        )
        
        # Convert to response model
        detection_responses = [
            PIIDetectionResponse(
                pii_type=d.pii_type,
                pattern_id=d.pattern_id,
                value=d.value,
                start_pos=d.start_pos,
                end_pos=d.end_pos,
                confidence=d.confidence,
                compliance_standards=d.compliance_standards
            )
            for d in result.detections
        ]
        
        return RedactPIIResponse(
            original_text=result.original_text,
            redacted_text=result.redacted_text,
            detections=detection_responses,
            redaction_map=result.redaction_map,
            compliance_violations=result.compliance_violations,
            processing_time_ms=result.processing_time_ms,
            timestamp=result.timestamp
        )
    except Exception as e:
        logger.error(f"Error in redact_pii: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to redact PII: {str(e)}"
        )


@router.post("/batch-redact", response_model=BatchRedactResponse, status_code=status.HTTP_200_OK)
async def batch_redact_pii(
    request: BatchRedactRequest,
    service: PIIProtectionService = Depends(get_pii_service)
):
    """
    Redact PII in multiple texts (batch processing).
    
    Processes up to 100 texts in a single request for efficient bulk redaction.
    
    **Example Request:**
    ```json
    {
        "texts": [
            "Email: john@example.com",
            "Phone: 555-123-4567",
            "SSN: 123-45-6789"
        ],
        "compliance_standard": "hipaa"
    }
    ```
    """
    try:
        import time
        start_time = time.perf_counter()
        
        results = []
        total_detections = 0
        
        for text in request.texts:
            result = service.redact_pii(
                text=text,
                strategy=request.strategy,
                compliance_standard=request.compliance_standard
            )
            
            detection_responses = [
                PIIDetectionResponse(
                    pii_type=d.pii_type,
                    pattern_id=d.pattern_id,
                    value=d.value,
                    start_pos=d.start_pos,
                    end_pos=d.end_pos,
                    confidence=d.confidence,
                    compliance_standards=d.compliance_standards
                )
                for d in result.detections
            ]
            
            results.append(RedactPIIResponse(
                original_text=result.original_text,
                redacted_text=result.redacted_text,
                detections=detection_responses,
                redaction_map=result.redaction_map,
                compliance_violations=result.compliance_violations,
                processing_time_ms=result.processing_time_ms,
                timestamp=result.timestamp
            ))
            
            total_detections += len(result.detections)
        
        end_time = time.perf_counter()
        total_processing_time_ms = (end_time - start_time) * 1000
        
        return BatchRedactResponse(
            results=results,
            total_texts=len(request.texts),
            total_detections=total_detections,
            total_processing_time_ms=total_processing_time_ms
        )
    except Exception as e:
        logger.error(f"Error in batch_redact_pii: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process batch: {str(e)}"
        )


@router.post("/add-pattern", status_code=status.HTTP_201_CREATED)
async def add_custom_pattern(
    request: AddCustomPatternRequest,
    service: PIIProtectionService = Depends(get_pii_service)
):
    """
    Add a custom PII detection pattern.
    
    Allows adding organization-specific PII patterns for detection.
    
    **Example Request:**
    ```json
    {
        "pattern_id": "pii-employee-id",
        "pii_type": "custom",
        "name": "Employee ID",
        "regex": "\\bEMP[0-9]{6}\\b",
        "description": "Company employee IDs",
        "compliance_standards": ["soc2"],
        "default_strategy": "mask"
    }
    ```
    """
    try:
        service.add_custom_pattern(
            pattern_id=request.pattern_id,
            pii_type=request.pii_type,
            name=request.name,
            regex=request.regex,
            description=request.description,
            compliance_standards=request.compliance_standards,
            default_strategy=request.default_strategy
        )
        return {
            "status": "success",
            "message": f"Custom pattern '{request.pattern_id}' added successfully"
        }
    except Exception as e:
        logger.error(f"Error in add_custom_pattern: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add custom pattern: {str(e)}"
        )


@router.get("/patterns", response_model=List[PatternInfo], status_code=status.HTTP_200_OK)
async def get_patterns(
    service: PIIProtectionService = Depends(get_pii_service)
):
    """
    Get list of all PII detection patterns.
    
    Returns information about all available patterns including
    built-in and custom patterns.
    """
    try:
        patterns = []
        for pattern in service.patterns:
            patterns.append(PatternInfo(
                pattern_id=pattern.pattern_id,
                pii_type=pattern.pii_type,
                name=pattern.name,
                description=pattern.description,
                compliance_standards=pattern.compliance_standards,
                default_strategy=pattern.default_strategy,
                examples=pattern.examples
            ))
        return patterns
    except Exception as e:
        logger.error(f"Error in get_patterns: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve patterns: {str(e)}"
        )


@router.get("/pii-types", response_model=List[str], status_code=status.HTTP_200_OK)
async def get_pii_types():
    """Get list of all supported PII types."""
    return [pii_type.value for pii_type in PIIType]


@router.get("/redaction-strategies", response_model=List[str], status_code=status.HTTP_200_OK)
async def get_redaction_strategies():
    """Get list of all redaction strategies."""
    return [strategy.value for strategy in RedactionStrategy]


@router.get("/compliance-standards", response_model=List[str], status_code=status.HTTP_200_OK)
async def get_compliance_standards():
    """Get list of all supported compliance standards."""
    return [standard.value for standard in ComplianceStandard]


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint for PII protection service."""
    return {
        "status": "healthy",
        "service": "pii_protection",
        "version": "1.0.0"
    }


# Add logger import
import logging
logger = logging.getLogger(__name__)

