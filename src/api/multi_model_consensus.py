"""
Multi-Model Consensus API
REST API endpoints for multi-model ensemble hallucination detection.

Author: AgentGuard Engineering Team
Date: October 2025
Version: 1.0.0
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from datetime import datetime

from ..services.multi_model_consensus import (
    get_multi_model_consensus_service,
    MultiModelConsensusService,
    ModelName,
    ModelProvider,
    VotingStrategy,
    ModelConfig,
    ConsensusResult
)

router = APIRouter(
    prefix="/multi-model",
    tags=["multi_model_consensus"],
    responses={404: {"description": "Not found"}}
)


# Request/Response Models

class DetectHallucinationRequest(BaseModel):
    """Request model for multi-model hallucination detection."""
    agent_output: str = Field(..., description="The agent's output to check", min_length=1)
    agent_input: Optional[str] = Field(None, description="Optional input that led to the output")
    context: Optional[str] = Field(None, description="Optional additional context")
    strategy: Optional[VotingStrategy] = Field(None, description="Voting strategy")
    min_models: int = Field(2, description="Minimum models required", ge=1, le=10)
    confidence_threshold: float = Field(0.7, description="Confidence threshold for THRESHOLD strategy", ge=0.0, le=1.0)


class ModelResultResponse(BaseModel):
    """Response model for a single model result."""
    model_name: ModelName
    is_hallucination: bool
    confidence: float
    reasoning: str
    processing_time_ms: float
    tokens_used: int
    cost: float
    error: Optional[str]


class DetectHallucinationResponse(BaseModel):
    """Response model for multi-model detection."""
    is_hallucination: bool
    confidence: float
    agreement_score: float
    model_results: List[ModelResultResponse]
    voting_strategy: VotingStrategy
    models_voted: int
    models_agreed: int
    final_reasoning: str
    total_processing_time_ms: float
    total_cost: float
    timestamp: datetime

    @classmethod
    def from_consensus_result(cls, result: ConsensusResult):
        """Create response from consensus result."""
        return cls(
            is_hallucination=result.is_hallucination,
            confidence=result.confidence,
            agreement_score=result.agreement_score,
            model_results=[
                ModelResultResponse(
                    model_name=r.model_name,
                    is_hallucination=r.is_hallucination,
                    confidence=r.confidence,
                    reasoning=r.reasoning,
                    processing_time_ms=r.processing_time_ms,
                    tokens_used=r.tokens_used,
                    cost=r.cost,
                    error=r.error
                )
                for r in result.model_results
            ],
            voting_strategy=result.voting_strategy,
            models_voted=result.models_voted,
            models_agreed=result.models_agreed,
            final_reasoning=result.final_reasoning,
            total_processing_time_ms=result.total_processing_time_ms,
            total_cost=result.total_cost,
            timestamp=result.timestamp
        )


class ModelConfigRequest(BaseModel):
    """Request model for model configuration."""
    name: ModelName
    provider: ModelProvider
    enabled: bool = True
    weight: float = Field(1.0, ge=0.0, le=10.0)
    cost_per_1k_tokens: float = Field(0.01, ge=0.0)
    max_tokens: int = Field(4096, ge=1, le=100000)
    temperature: float = Field(0.0, ge=0.0, le=2.0)
    timeout_seconds: float = Field(30.0, ge=1.0, le=300.0)


class ModelConfigResponse(BaseModel):
    """Response model for model configuration."""
    name: ModelName
    provider: ModelProvider
    enabled: bool
    weight: float
    cost_per_1k_tokens: float
    max_tokens: int
    temperature: float
    timeout_seconds: float


class ModelPerformanceResponse(BaseModel):
    """Response model for model performance stats."""
    model_name: ModelName
    total_calls: int
    successful_calls: int
    failed_calls: int
    success_rate: float
    avg_latency_ms: float
    avg_confidence: float
    total_cost: float


class EnableModelRequest(BaseModel):
    """Request model for enabling/disabling a model."""
    model_name: ModelName
    enabled: bool


# Dependency
def get_consensus_service() -> MultiModelConsensusService:
    """Get multi-model consensus service instance."""
    return get_multi_model_consensus_service()


# API Endpoints

@router.post("/detect", response_model=DetectHallucinationResponse, status_code=status.HTTP_200_OK)
async def detect_hallucination(
    request: DetectHallucinationRequest,
    service: MultiModelConsensusService = Depends(get_consensus_service)
):
    """
    Detect hallucination using multi-model consensus.
    
    Uses ensemble voting across multiple LLM models for improved accuracy.
    Supports multiple voting strategies and cost optimization.
    
    **Example Request:**
    ```json
    {
        "agent_output": "The Eiffel Tower is located in London.",
        "agent_input": "Where is the Eiffel Tower?",
        "strategy": "weighted",
        "min_models": 2
    }
    ```
    
    **Example Response:**
    ```json
    {
        "is_hallucination": true,
        "confidence": 0.95,
        "agreement_score": 1.0,
        "model_results": [
            {
                "model_name": "claude-sonnet-4.5",
                "is_hallucination": true,
                "confidence": 0.98,
                "reasoning": "The Eiffel Tower is in Paris, not London"
            }
        ],
        "voting_strategy": "weighted",
        "models_voted": 3,
        "models_agreed": 3,
        "final_reasoning": "Weighted vote: 0.95 hallucination score",
        "total_processing_time_ms": 245.3,
        "total_cost": 0.0012
    }
    ```
    """
    try:
        result = await service.detect_hallucination(
            agent_output=request.agent_output,
            agent_input=request.agent_input,
            context=request.context,
            strategy=request.strategy,
            min_models=request.min_models,
            confidence_threshold=request.confidence_threshold
        )
        return DetectHallucinationResponse.from_consensus_result(result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in detect_hallucination: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect hallucination: {str(e)}"
        )


@router.get("/models", response_model=List[ModelConfigResponse], status_code=status.HTTP_200_OK)
async def list_models(
    service: MultiModelConsensusService = Depends(get_consensus_service)
):
    """
    List all available models and their configurations.
    
    Returns configuration details for all supported models including
    enabled status, weights, costs, and performance settings.
    
    **Example Response:**
    ```json
    [
        {
            "name": "claude-sonnet-4.5",
            "provider": "anthropic",
            "enabled": true,
            "weight": 1.2,
            "cost_per_1k_tokens": 0.003,
            "max_tokens": 4096,
            "temperature": 0.0,
            "timeout_seconds": 30.0
        }
    ]
    ```
    """
    try:
        models = []
        for model_name, config in service.models.items():
            models.append(ModelConfigResponse(
                name=config.name,
                provider=config.provider,
                enabled=config.enabled,
                weight=config.weight,
                cost_per_1k_tokens=config.cost_per_1k_tokens,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                timeout_seconds=config.timeout_seconds
            ))
        return models
    except Exception as e:
        logger.error(f"Error in list_models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}"
        )


@router.post("/models/configure", status_code=status.HTTP_200_OK)
async def configure_model(
    request: ModelConfigRequest,
    service: MultiModelConsensusService = Depends(get_consensus_service)
):
    """
    Configure a model's settings.
    
    Update model configuration including weights, costs, and performance settings.
    
    **Example Request:**
    ```json
    {
        "name": "claude-sonnet-4.5",
        "provider": "anthropic",
        "enabled": true,
        "weight": 1.5,
        "cost_per_1k_tokens": 0.003,
        "max_tokens": 4096,
        "temperature": 0.0,
        "timeout_seconds": 30.0
    }
    ```
    """
    try:
        config = ModelConfig(
            name=request.name,
            provider=request.provider,
            enabled=request.enabled,
            weight=request.weight,
            cost_per_1k_tokens=request.cost_per_1k_tokens,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            timeout_seconds=request.timeout_seconds
        )
        service.configure_model(request.name, config)
        return {
            "status": "success",
            "message": f"Model {request.name.value} configured successfully"
        }
    except Exception as e:
        logger.error(f"Error in configure_model: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to configure model: {str(e)}"
        )


@router.post("/models/enable", status_code=status.HTTP_200_OK)
async def enable_disable_model(
    request: EnableModelRequest,
    service: MultiModelConsensusService = Depends(get_consensus_service)
):
    """
    Enable or disable a model.
    
    **Example Request:**
    ```json
    {
        "model_name": "gpt-4-turbo",
        "enabled": true
    }
    ```
    """
    try:
        if request.enabled:
            service.enable_model(request.model_name)
        else:
            service.disable_model(request.model_name)
        
        action = "enabled" if request.enabled else "disabled"
        return {
            "status": "success",
            "message": f"Model {request.model_name.value} {action} successfully"
        }
    except Exception as e:
        logger.error(f"Error in enable_disable_model: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update model status: {str(e)}"
        )


@router.get("/performance", response_model=List[ModelPerformanceResponse], status_code=status.HTTP_200_OK)
async def get_performance_stats(
    service: MultiModelConsensusService = Depends(get_consensus_service)
):
    """
    Get performance statistics for all models.
    
    Returns detailed performance metrics including call counts, success rates,
    latency, confidence, and costs for each model.
    
    **Example Response:**
    ```json
    [
        {
            "model_name": "claude-sonnet-4.5",
            "total_calls": 1250,
            "successful_calls": 1248,
            "failed_calls": 2,
            "success_rate": 0.998,
            "avg_latency_ms": 245.3,
            "avg_confidence": 0.92,
            "total_cost": 3.75
        }
    ]
    ```
    """
    try:
        stats = service.get_performance_stats()
        performance = []
        
        for model_name, model_stats in stats.items():
            total = model_stats["total_calls"]
            success_rate = (
                model_stats["successful_calls"] / total if total > 0 else 0.0
            )
            
            performance.append(ModelPerformanceResponse(
                model_name=model_name,
                total_calls=model_stats["total_calls"],
                successful_calls=model_stats["successful_calls"],
                failed_calls=model_stats["failed_calls"],
                success_rate=success_rate,
                avg_latency_ms=model_stats["avg_latency_ms"],
                avg_confidence=model_stats["avg_confidence"],
                total_cost=model_stats["total_cost"]
            ))
        
        return performance
    except Exception as e:
        logger.error(f"Error in get_performance_stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance stats: {str(e)}"
        )


@router.get("/strategies", response_model=List[str], status_code=status.HTTP_200_OK)
async def list_voting_strategies():
    """
    List all available voting strategies.
    
    **Example Response:**
    ```json
    ["majority", "weighted", "unanimous", "threshold", "cascading"]
    ```
    """
    return [strategy.value for strategy in VotingStrategy]


@router.get("/providers", response_model=List[str], status_code=status.HTTP_200_OK)
async def list_providers():
    """
    List all supported model providers.
    
    **Example Response:**
    ```json
    ["anthropic", "openai", "google", "meta", "xai", "mistral"]
    ```
    """
    return [provider.value for provider in ModelProvider]


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint for multi-model consensus service.
    
    **Example Response:**
    ```json
    {
        "status": "healthy",
        "service": "multi_model_consensus",
        "version": "1.0.0",
        "models_available": 6
    }
    ```
    """
    service = get_consensus_service()
    enabled_models = sum(1 for m in service.models.values() if m.enabled)
    
    return {
        "status": "healthy",
        "service": "multi_model_consensus",
        "version": "1.0.0",
        "models_available": len(service.models),
        "models_enabled": enabled_models
    }


# Add logger import
import logging
logger = logging.getLogger(__name__)

