"""
Model Hosting Platform API Router
REST API endpoints for model deployment and management.

Author: AgentGuard Engineering Team
Date: October 2025
Version: 1.0.0
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

from ..services.model_hosting import (
    get_model_hosting_service,
    ModelType,
    ModelStatus,
    PricingTier,
    DeploymentType,
    ModelMetadata,
    ModelDeployment,
    UsageMetrics
)

router = APIRouter(
    prefix="/models",
    tags=["model_hosting"],
    responses={404: {"description": "Not found"}}
)


# Request/Response Models
class ModelRegisterRequest(BaseModel):
    name: str = Field(..., description="Model name")
    description: str = Field(..., description="Model description")
    model_type: str = Field(..., description="Type of model (hallucination_detector, safety_classifier, etc.)")
    version: str = Field(..., description="Model version (e.g., 1.0.0)")
    author: str = Field(..., description="Model author")
    tags: Optional[List[str]] = Field(None, description="Tags for discovery")
    license: str = Field("MIT", description="Model license")


class ModelRegisterResponse(BaseModel):
    model_id: str
    message: str


class ModelDeployRequest(BaseModel):
    deployment_type: str = Field("serverless", description="Deployment type (serverless, dedicated, edge)")
    pricing_tier: str = Field("free", description="Pricing tier (free, starter, pro, enterprise)")
    auto_scale: bool = Field(False, description="Enable auto-scaling")


class ModelDeploymentResponse(BaseModel):
    deployment_id: str
    model_id: str
    status: str
    endpoint_url: str
    pricing_tier: str
    message: str


class ModelListResponse(BaseModel):
    models: List[dict]
    total: int


class DeploymentListResponse(BaseModel):
    deployments: List[dict]
    total: int


class UsageMetricsResponse(BaseModel):
    requests_today: int
    requests_this_month: int
    total_requests: int
    errors_today: int
    errors_this_month: int
    total_errors: int
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    uptime_percentage: float
    cost_this_month: float


class CostEstimateRequest(BaseModel):
    pricing_tier: str = Field(..., description="Pricing tier")
    requests_per_month: int = Field(..., description="Expected requests per month")
    storage_gb: int = Field(0, description="Storage usage in GB")


class CostEstimateResponse(BaseModel):
    pricing_tier: str
    base_cost: float
    estimated_total_cost: float
    requests_per_month: int
    storage_gb: int


# API Endpoints
@router.post(
    "/register",
    response_model=ModelRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New Model",
    description="Register a new model in the hosting platform"
)
async def register_model(request: ModelRegisterRequest):
    """
    Register a new model for hosting.
    
    Models can be:
    - Hallucination detectors
    - Safety classifiers
    - Bias detectors
    - Content filters
    - Prompt injection detectors
    - Custom models
    """
    try:
        service = get_model_hosting_service()
        
        # Validate model type
        try:
            model_type = ModelType(request.model_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid model_type. Must be one of: {[e.value for e in ModelType]}"
            )
        
        model_id = service.register_model(
            name=request.name,
            description=request.description,
            model_type=model_type,
            version=request.version,
            author=request.author,
            tags=request.tags,
            license=request.license
        )
        
        return ModelRegisterResponse(
            model_id=model_id,
            message=f"Model '{request.name}' registered successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/{model_id}/deploy",
    response_model=ModelDeploymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Deploy Model",
    description="Deploy a registered model"
)
async def deploy_model(model_id: str, request: ModelDeployRequest):
    """
    Deploy a registered model.
    
    Deployment types:
    - serverless: Auto-scaling serverless deployment
    - dedicated: Dedicated instances
    - edge: Edge deployment for low latency
    
    Pricing tiers:
    - free: 10 req/min, 3 models, 5GB storage
    - starter: 100 req/min, 10 models, 50GB storage ($29/month)
    - pro: 1000 req/min, 50 models, 500GB storage ($99/month)
    - enterprise: Unlimited (custom pricing)
    """
    try:
        service = get_model_hosting_service()
        
        # Validate deployment type
        try:
            deployment_type = DeploymentType(request.deployment_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid deployment_type. Must be one of: {[e.value for e in DeploymentType]}"
            )
        
        # Validate pricing tier
        try:
            pricing_tier = PricingTier(request.pricing_tier)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid pricing_tier. Must be one of: {[e.value for e in PricingTier]}"
            )
        
        deployment = service.deploy_model(
            model_id=model_id,
            deployment_type=deployment_type,
            pricing_tier=pricing_tier,
            auto_scale=request.auto_scale
        )
        
        return ModelDeploymentResponse(
            deployment_id=deployment.deployment_id,
            model_id=deployment.model_id,
            status=deployment.status.value,
            endpoint_url=deployment.endpoint_url,
            pricing_tier=deployment.config.pricing_tier.value,
            message="Model deployed successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/",
    response_model=ModelListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Models",
    description="List all registered models with optional filtering"
)
async def list_models(
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    author: Optional[str] = Query(None, description="Filter by author"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results")
):
    """
    List models with optional filtering.
    
    Supports filtering by:
    - model_type: Type of model
    - author: Model author
    - tags: Comma-separated tags
    """
    try:
        service = get_model_hosting_service()
        
        # Parse model type
        model_type_enum = None
        if model_type:
            try:
                model_type_enum = ModelType(model_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid model_type. Must be one of: {[e.value for e in ModelType]}"
                )
        
        # Parse tags
        tags_list = tags.split(",") if tags else None
        
        models = service.list_models(
            model_type=model_type_enum,
            author=author,
            tags=tags_list,
            limit=limit
        )
        
        return ModelListResponse(
            models=models,
            total=len(models)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/{model_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get Model Details",
    description="Get detailed information about a specific model"
)
async def get_model(model_id: str):
    """Get model details by ID."""
    try:
        service = get_model_hosting_service()
        model = service.get_model(model_id)
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_id} not found"
            )
        
        return {
            "model_id": model_id,
            "name": model.name,
            "description": model.description,
            "model_type": model.model_type.value,
            "version": model.version,
            "author": model.author,
            "tags": model.tags,
            "license": model.license,
            "downloads": model.downloads,
            "stars": model.stars,
            "created_at": model.created_at.isoformat(),
            "updated_at": model.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/{model_id}/deployments",
    response_model=DeploymentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Model Deployments",
    description="List all deployments for a specific model"
)
async def list_model_deployments(model_id: str):
    """List all deployments for a model."""
    try:
        service = get_model_hosting_service()
        deployments = service.list_deployments(model_id=model_id)
        
        deployments_data = [
            {
                "deployment_id": d.deployment_id,
                "model_id": d.model_id,
                "status": d.status.value,
                "endpoint_url": d.endpoint_url,
                "pricing_tier": d.config.pricing_tier.value,
                "deployment_type": d.config.deployment_type.value,
                "total_requests": d.total_requests,
                "total_errors": d.total_errors,
                "avg_latency_ms": d.avg_latency_ms,
                "created_at": d.created_at.isoformat(),
                "last_accessed": d.last_accessed.isoformat()
            }
            for d in deployments
        ]
        
        return DeploymentListResponse(
            deployments=deployments_data,
            total=len(deployments_data)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/deployments/{deployment_id}/pause",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Pause Deployment",
    description="Pause a running deployment"
)
async def pause_deployment(deployment_id: str):
    """Pause a running deployment."""
    try:
        service = get_model_hosting_service()
        service.pause_deployment(deployment_id)
        return {"message": f"Deployment {deployment_id} paused successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/deployments/{deployment_id}/resume",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Resume Deployment",
    description="Resume a paused deployment"
)
async def resume_deployment(deployment_id: str):
    """Resume a paused deployment."""
    try:
        service = get_model_hosting_service()
        service.resume_deployment(deployment_id)
        return {"message": f"Deployment {deployment_id} resumed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete(
    "/deployments/{deployment_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Delete Deployment",
    description="Delete a deployment"
)
async def delete_deployment(deployment_id: str):
    """Delete a deployment."""
    try:
        service = get_model_hosting_service()
        service.delete_deployment(deployment_id)
        return {"message": f"Deployment {deployment_id} deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/{model_id}/metrics",
    response_model=UsageMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Usage Metrics",
    description="Get usage metrics for a model"
)
async def get_usage_metrics(model_id: str):
    """Get usage metrics for a model."""
    try:
        service = get_model_hosting_service()
        metrics = service.get_usage_metrics(model_id)
        
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_id} not found"
            )
        
        return UsageMetricsResponse(
            requests_today=metrics.requests_today,
            requests_this_month=metrics.requests_this_month,
            total_requests=metrics.total_requests,
            errors_today=metrics.errors_today,
            errors_this_month=metrics.errors_this_month,
            total_errors=metrics.total_errors,
            avg_latency_ms=metrics.avg_latency_ms,
            p95_latency_ms=metrics.p95_latency_ms,
            p99_latency_ms=metrics.p99_latency_ms,
            uptime_percentage=metrics.uptime_percentage,
            cost_this_month=metrics.cost_this_month
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/{model_id}/star",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Star Model",
    description="Add a star to a model"
)
async def star_model(model_id: str):
    """Star a model."""
    try:
        service = get_model_hosting_service()
        service.star_model(model_id)
        model = service.get_model(model_id)
        return {
            "message": f"Model starred successfully",
            "total_stars": model.stars if model else 0
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/popular",
    response_model=List[dict],
    status_code=status.HTTP_200_OK,
    summary="Get Popular Models",
    description="Get most popular models by stars and downloads"
)
async def get_popular_models(limit: int = Query(10, ge=1, le=50)):
    """Get popular models."""
    try:
        service = get_model_hosting_service()
        return service.get_popular_models(limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/search",
    response_model=ModelListResponse,
    status_code=status.HTTP_200_OK,
    summary="Search Models",
    description="Search models by name, description, or tags"
)
async def search_models(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100)
):
    """Search models."""
    try:
        service = get_model_hosting_service()
        results = service.search_models(query=q, limit=limit)
        return ModelListResponse(
            models=results,
            total=len(results)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/pricing",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get Pricing Information",
    description="Get pricing information for all tiers"
)
async def get_pricing():
    """Get pricing information."""
    try:
        service = get_model_hosting_service()
        return service.get_pricing_info()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/pricing/estimate",
    response_model=CostEstimateResponse,
    status_code=status.HTTP_200_OK,
    summary="Estimate Cost",
    description="Estimate monthly cost for a pricing tier"
)
async def estimate_cost(request: CostEstimateRequest):
    """Estimate monthly cost."""
    try:
        service = get_model_hosting_service()
        
        # Validate pricing tier
        try:
            pricing_tier = PricingTier(request.pricing_tier)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid pricing_tier. Must be one of: {[e.value for e in PricingTier]}"
            )
        
        estimated_cost = service.calculate_cost(
            pricing_tier=pricing_tier,
            requests_per_month=request.requests_per_month,
            storage_gb=request.storage_gb
        )
        
        tier_config = service.get_pricing_info()[pricing_tier]
        base_cost = tier_config["price"] if isinstance(tier_config["price"], (int, float)) else 0
        
        return CostEstimateResponse(
            pricing_tier=request.pricing_tier,
            base_cost=base_cost,
            estimated_total_cost=estimated_cost,
            requests_per_month=request.requests_per_month,
            storage_gb=request.storage_gb
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/health",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check model hosting service health"
)
async def health_check():
    """Health check endpoint."""
    try:
        service = get_model_hosting_service()
        return {
            "status": "healthy",
            "service": "model_hosting",
            "version": "1.0.0",
            "total_models": len(service.models),
            "total_deployments": len(service.deployments),
            "features": [
                "model_registration",
                "one_click_deployment",
                "auto_scaling",
                "usage_tracking",
                "freemium_pricing",
                "community_sharing"
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

