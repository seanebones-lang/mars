"""
Model Hosting Platform Service
Hugging Face-inspired platform for deploying and scaling AI models.

Provides freemium model hosting with paid scaling for community growth
and developer adoption.

Author: AgentGuard Engineering Team
Date: October 2025
Version: 1.0.0
"""

import logging
import time
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """Types of models that can be hosted."""
    HALLUCINATION_DETECTOR = "hallucination_detector"
    SAFETY_CLASSIFIER = "safety_classifier"
    BIAS_DETECTOR = "bias_detector"
    CONTENT_FILTER = "content_filter"
    PROMPT_INJECTION_DETECTOR = "prompt_injection_detector"
    CUSTOM = "custom"


class ModelStatus(str, Enum):
    """Status of a hosted model."""
    DRAFT = "draft"
    BUILDING = "building"
    READY = "ready"
    DEPLOYING = "deploying"
    RUNNING = "running"
    PAUSED = "paused"
    FAILED = "failed"
    ARCHIVED = "archived"


class PricingTier(str, Enum):
    """Pricing tiers for model hosting."""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class DeploymentType(str, Enum):
    """Types of model deployments."""
    SERVERLESS = "serverless"
    DEDICATED = "dedicated"
    EDGE = "edge"


@dataclass
class ModelMetadata:
    """Metadata for a hosted model."""
    name: str
    description: str
    model_type: ModelType
    version: str
    author: str
    tags: List[str] = field(default_factory=list)
    license: str = "MIT"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    downloads: int = 0
    stars: int = 0


@dataclass
class ModelConfig:
    """Configuration for model deployment."""
    deployment_type: DeploymentType
    pricing_tier: PricingTier
    max_requests_per_minute: int
    max_concurrent_requests: int
    timeout_seconds: int
    auto_scale: bool
    min_instances: int
    max_instances: int
    memory_mb: int
    cpu_cores: float


@dataclass
class ModelDeployment:
    """Represents a deployed model instance."""
    deployment_id: str
    model_id: str
    status: ModelStatus
    endpoint_url: str
    config: ModelConfig
    created_at: datetime
    last_accessed: datetime
    total_requests: int = 0
    total_errors: int = 0
    avg_latency_ms: float = 0.0
    current_instances: int = 1


@dataclass
class UsageMetrics:
    """Usage metrics for a deployed model."""
    requests_today: int = 0
    requests_this_month: int = 0
    total_requests: int = 0
    errors_today: int = 0
    errors_this_month: int = 0
    total_errors: int = 0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    uptime_percentage: float = 100.0
    cost_this_month: float = 0.0


class ModelHostingService:
    """
    Model hosting platform service for deploying and scaling AI models.
    
    Provides:
    - Model registration and versioning
    - One-click deployment
    - Auto-scaling
    - Usage tracking and billing
    - Community model sharing
    - Freemium pricing model
    
    Inspired by Hugging Face's model hosting platform.
    """
    
    # Pricing configuration (per month)
    PRICING = {
        PricingTier.FREE: {
            "price": 0,
            "max_requests_per_minute": 10,
            "max_concurrent_requests": 2,
            "max_models": 3,
            "storage_gb": 5,
            "features": ["Community models", "Basic analytics", "Serverless only"]
        },
        PricingTier.STARTER: {
            "price": 29,
            "max_requests_per_minute": 100,
            "max_concurrent_requests": 10,
            "max_models": 10,
            "storage_gb": 50,
            "features": ["Private models", "Advanced analytics", "Dedicated instances", "Email support"]
        },
        PricingTier.PRO: {
            "price": 99,
            "max_requests_per_minute": 1000,
            "max_concurrent_requests": 50,
            "max_models": 50,
            "storage_gb": 500,
            "features": ["All Starter features", "Auto-scaling", "Edge deployment", "Priority support", "Custom domains"]
        },
        PricingTier.ENTERPRISE: {
            "price": "custom",
            "max_requests_per_minute": "unlimited",
            "max_concurrent_requests": "unlimited",
            "max_models": "unlimited",
            "storage_gb": "unlimited",
            "features": ["All Pro features", "SLA guarantees", "Dedicated support", "On-premise deployment", "Custom integrations"]
        }
    }
    
    def __init__(self):
        """Initialize model hosting service."""
        self.models: Dict[str, ModelMetadata] = {}
        self.deployments: Dict[str, ModelDeployment] = {}
        self.usage_metrics: Dict[str, UsageMetrics] = {}
        logger.info("Model hosting service initialized")
    
    def register_model(
        self,
        name: str,
        description: str,
        model_type: ModelType,
        version: str,
        author: str,
        tags: Optional[List[str]] = None,
        license: str = "MIT"
    ) -> str:
        """
        Register a new model in the platform.
        
        Args:
            name: Model name
            description: Model description
            model_type: Type of model
            version: Model version
            author: Model author
            tags: Optional tags for discovery
            license: Model license
            
        Returns:
            model_id: Unique identifier for the model
        """
        model_id = str(uuid.uuid4())
        
        metadata = ModelMetadata(
            name=name,
            description=description,
            model_type=model_type,
            version=version,
            author=author,
            tags=tags or [],
            license=license
        )
        
        self.models[model_id] = metadata
        self.usage_metrics[model_id] = UsageMetrics()
        
        logger.info(f"Registered model '{name}' (ID: {model_id}) by {author}")
        return model_id
    
    def deploy_model(
        self,
        model_id: str,
        deployment_type: DeploymentType = DeploymentType.SERVERLESS,
        pricing_tier: PricingTier = PricingTier.FREE,
        auto_scale: bool = False
    ) -> ModelDeployment:
        """
        Deploy a registered model.
        
        Args:
            model_id: ID of model to deploy
            deployment_type: Type of deployment
            pricing_tier: Pricing tier for deployment
            auto_scale: Enable auto-scaling
            
        Returns:
            ModelDeployment: Deployment information
        """
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
        
        model = self.models[model_id]
        
        # Get tier limits
        tier_config = self.PRICING[pricing_tier]
        
        # Create deployment configuration
        config = ModelConfig(
            deployment_type=deployment_type,
            pricing_tier=pricing_tier,
            max_requests_per_minute=tier_config["max_requests_per_minute"] if isinstance(tier_config["max_requests_per_minute"], int) else 1000,
            max_concurrent_requests=tier_config["max_concurrent_requests"] if isinstance(tier_config["max_concurrent_requests"], int) else 50,
            timeout_seconds=30,
            auto_scale=auto_scale and pricing_tier in [PricingTier.PRO, PricingTier.ENTERPRISE],
            min_instances=1,
            max_instances=10 if auto_scale else 1,
            memory_mb=2048,
            cpu_cores=1.0
        )
        
        # Create deployment
        deployment_id = str(uuid.uuid4())
        endpoint_url = f"https://api.agentguard.ai/models/{model_id}/v{model.version}"
        
        deployment = ModelDeployment(
            deployment_id=deployment_id,
            model_id=model_id,
            status=ModelStatus.DEPLOYING,
            endpoint_url=endpoint_url,
            config=config,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow()
        )
        
        self.deployments[deployment_id] = deployment
        
        # Simulate deployment process
        logger.info(f"Deploying model '{model.name}' (deployment: {deployment_id})")
        
        # In production, this would trigger actual deployment
        # For now, we'll mark it as RUNNING
        deployment.status = ModelStatus.RUNNING
        
        return deployment
    
    def get_model(self, model_id: str) -> Optional[ModelMetadata]:
        """Get model metadata by ID."""
        return self.models.get(model_id)
    
    def list_models(
        self,
        model_type: Optional[ModelType] = None,
        author: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List models with optional filtering.
        
        Args:
            model_type: Filter by model type
            author: Filter by author
            tags: Filter by tags
            limit: Maximum number of results
            
        Returns:
            List of model metadata
        """
        results = []
        
        for model_id, metadata in self.models.items():
            # Apply filters
            if model_type and metadata.model_type != model_type:
                continue
            if author and metadata.author != author:
                continue
            if tags and not any(tag in metadata.tags for tag in tags):
                continue
            
            results.append({
                "model_id": model_id,
                "name": metadata.name,
                "description": metadata.description,
                "model_type": metadata.model_type.value,
                "version": metadata.version,
                "author": metadata.author,
                "tags": metadata.tags,
                "license": metadata.license,
                "downloads": metadata.downloads,
                "stars": metadata.stars,
                "created_at": metadata.created_at.isoformat()
            })
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_deployment(self, deployment_id: str) -> Optional[ModelDeployment]:
        """Get deployment by ID."""
        return self.deployments.get(deployment_id)
    
    def list_deployments(self, model_id: Optional[str] = None) -> List[ModelDeployment]:
        """List all deployments, optionally filtered by model_id."""
        if model_id:
            return [d for d in self.deployments.values() if d.model_id == model_id]
        return list(self.deployments.values())
    
    def pause_deployment(self, deployment_id: str):
        """Pause a running deployment."""
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            raise ValueError(f"Deployment {deployment_id} not found")
        
        if deployment.status != ModelStatus.RUNNING:
            raise ValueError(f"Deployment is not running (status: {deployment.status})")
        
        deployment.status = ModelStatus.PAUSED
        logger.info(f"Paused deployment {deployment_id}")
    
    def resume_deployment(self, deployment_id: str):
        """Resume a paused deployment."""
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            raise ValueError(f"Deployment {deployment_id} not found")
        
        if deployment.status != ModelStatus.PAUSED:
            raise ValueError(f"Deployment is not paused (status: {deployment.status})")
        
        deployment.status = ModelStatus.RUNNING
        logger.info(f"Resumed deployment {deployment_id}")
    
    def delete_deployment(self, deployment_id: str):
        """Delete a deployment."""
        if deployment_id not in self.deployments:
            raise ValueError(f"Deployment {deployment_id} not found")
        
        del self.deployments[deployment_id]
        logger.info(f"Deleted deployment {deployment_id}")
    
    def record_request(
        self,
        deployment_id: str,
        latency_ms: float,
        success: bool = True
    ):
        """
        Record a request to a deployed model.
        
        Args:
            deployment_id: Deployment ID
            latency_ms: Request latency in milliseconds
            success: Whether request was successful
        """
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            return
        
        # Update deployment stats
        deployment.total_requests += 1
        if not success:
            deployment.total_errors += 1
        
        # Update average latency (simple moving average)
        deployment.avg_latency_ms = (
            (deployment.avg_latency_ms * (deployment.total_requests - 1) + latency_ms)
            / deployment.total_requests
        )
        deployment.last_accessed = datetime.utcnow()
        
        # Update usage metrics
        metrics = self.usage_metrics.get(deployment.model_id)
        if metrics:
            metrics.requests_today += 1
            metrics.requests_this_month += 1
            metrics.total_requests += 1
            
            if not success:
                metrics.errors_today += 1
                metrics.errors_this_month += 1
                metrics.total_errors += 1
            
            # Update latency metrics (simplified)
            metrics.avg_latency_ms = deployment.avg_latency_ms
            metrics.p95_latency_ms = deployment.avg_latency_ms * 1.5
            metrics.p99_latency_ms = deployment.avg_latency_ms * 2.0
            
            # Calculate cost (simplified: $0.001 per request for paid tiers)
            if deployment.config.pricing_tier != PricingTier.FREE:
                metrics.cost_this_month += 0.001
    
    def get_usage_metrics(self, model_id: str) -> Optional[UsageMetrics]:
        """Get usage metrics for a model."""
        return self.usage_metrics.get(model_id)
    
    def star_model(self, model_id: str):
        """Add a star to a model."""
        model = self.models.get(model_id)
        if model:
            model.stars += 1
            logger.info(f"Model {model_id} starred (total: {model.stars})")
    
    def increment_downloads(self, model_id: str):
        """Increment download count for a model."""
        model = self.models.get(model_id)
        if model:
            model.downloads += 1
            logger.info(f"Model {model_id} downloaded (total: {model.downloads})")
    
    def get_pricing_info(self) -> Dict[str, Any]:
        """Get pricing information for all tiers."""
        return self.PRICING
    
    def calculate_cost(
        self,
        pricing_tier: PricingTier,
        requests_per_month: int,
        storage_gb: int = 0
    ) -> float:
        """
        Calculate estimated monthly cost.
        
        Args:
            pricing_tier: Pricing tier
            requests_per_month: Expected requests per month
            storage_gb: Storage usage in GB
            
        Returns:
            Estimated monthly cost in USD
        """
        tier_config = self.PRICING[pricing_tier]
        base_cost = tier_config["price"] if isinstance(tier_config["price"], (int, float)) else 0
        
        # Additional costs for overages
        overage_cost = 0.0
        
        # Request overage ($0.001 per request over limit)
        if pricing_tier != PricingTier.ENTERPRISE:
            max_requests = tier_config["max_requests_per_minute"] * 60 * 24 * 30  # Monthly limit
            if isinstance(max_requests, int) and requests_per_month > max_requests:
                overage_cost += (requests_per_month - max_requests) * 0.001
        
        # Storage overage ($0.10 per GB over limit)
        if pricing_tier != PricingTier.ENTERPRISE:
            max_storage = tier_config["storage_gb"]
            if isinstance(max_storage, int) and storage_gb > max_storage:
                overage_cost += (storage_gb - max_storage) * 0.10
        
        return base_cost + overage_cost
    
    def get_popular_models(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular models by stars and downloads."""
        models_list = []
        
        for model_id, metadata in self.models.items():
            popularity_score = metadata.stars * 2 + metadata.downloads
            models_list.append({
                "model_id": model_id,
                "name": metadata.name,
                "description": metadata.description,
                "author": metadata.author,
                "stars": metadata.stars,
                "downloads": metadata.downloads,
                "popularity_score": popularity_score
            })
        
        # Sort by popularity
        models_list.sort(key=lambda x: x["popularity_score"], reverse=True)
        
        return models_list[:limit]
    
    def search_models(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search models by name, description, or tags.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching models
        """
        results = []
        query_lower = query.lower()
        
        for model_id, metadata in self.models.items():
            # Check if query matches name, description, or tags
            if (query_lower in metadata.name.lower() or
                query_lower in metadata.description.lower() or
                any(query_lower in tag.lower() for tag in metadata.tags)):
                
                results.append({
                    "model_id": model_id,
                    "name": metadata.name,
                    "description": metadata.description,
                    "model_type": metadata.model_type.value,
                    "author": metadata.author,
                    "tags": metadata.tags,
                    "stars": metadata.stars,
                    "downloads": metadata.downloads
                })
            
            if len(results) >= limit:
                break
        
        return results


# Global instance
_model_hosting_service: Optional[ModelHostingService] = None


def get_model_hosting_service() -> ModelHostingService:
    """Get or create the global model hosting service instance."""
    global _model_hosting_service
    if _model_hosting_service is None:
        _model_hosting_service = ModelHostingService()
    return _model_hosting_service

