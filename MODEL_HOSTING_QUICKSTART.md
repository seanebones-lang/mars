# Model Hosting Platform - Quick Start Guide

**AgentGuard Model Hosting**  
Hugging Face-inspired platform for deploying and scaling AI safety models.

**Version**: 1.0.0  
**Date**: October 2025  
**Author**: AgentGuard Engineering Team

---

## Overview

The Model Hosting Platform provides a complete solution for deploying and scaling AI models:

- **Model Registration**: Register and version your models
- **One-Click Deployment**: Deploy models with a single API call
- **Auto-Scaling**: Automatic scaling based on demand
- **Usage Tracking**: Comprehensive metrics and analytics
- **Freemium Pricing**: Free tier with paid scaling options
- **Community Sharing**: Share models with the community

---

## Pricing Tiers

### Free Tier ($0/month)
- 10 requests/minute
- 2 concurrent requests
- 3 models
- 5GB storage
- Serverless only
- Community models
- Basic analytics

### Starter Tier ($29/month)
- 100 requests/minute
- 10 concurrent requests
- 10 models
- 50GB storage
- Private models
- Advanced analytics
- Dedicated instances
- Email support

### Pro Tier ($99/month)
- 1,000 requests/minute
- 50 concurrent requests
- 50 models
- 500GB storage
- Auto-scaling
- Edge deployment
- Priority support
- Custom domains

### Enterprise Tier (Custom)
- Unlimited requests
- Unlimited models
- Unlimited storage
- SLA guarantees
- Dedicated support
- On-premise deployment
- Custom integrations

---

## Quick Start

### 1. Register a Model

Register your AI safety model in the platform:

```python
import requests

# Register model
response = requests.post(
    "https://agentguard-api.onrender.com/models/register",
    json={
        "name": "HallucinationDetector-v1",
        "description": "Advanced hallucination detection model with 95% accuracy",
        "model_type": "hallucination_detector",
        "version": "1.0.0",
        "author": "your-username",
        "tags": ["hallucination", "safety", "detection"],
        "license": "MIT"
    }
)

model_id = response.json()["model_id"]
print(f"Model registered: {model_id}")
```

**Response**:
```json
{
  "model_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Model 'HallucinationDetector-v1' registered successfully"
}
```

### 2. Deploy the Model

Deploy your model with one click:

```python
# Deploy model
response = requests.post(
    f"https://agentguard-api.onrender.com/models/{model_id}/deploy",
    json={
        "deployment_type": "serverless",
        "pricing_tier": "free",
        "auto_scale": False
    }
)

deployment = response.json()
print(f"Deployed at: {deployment['endpoint_url']}")
```

**Response**:
```json
{
  "deployment_id": "660e8400-e29b-41d4-a716-446655440001",
  "model_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "endpoint_url": "https://api.agentguard.ai/models/550e8400-e29b-41d4-a716-446655440000/v1.0.0",
  "pricing_tier": "free",
  "message": "Model deployed successfully"
}
```

### 3. Use the Deployed Model

Make requests to your deployed model:

```python
# Use the model
response = requests.post(
    deployment['endpoint_url'],
    json={
        "text": "The AI agent claimed the sky is green.",
        "context": "General knowledge"
    }
)

result = response.json()
print(f"Hallucination detected: {result['is_hallucination']}")
```

---

## API Endpoints

### POST `/models/register`
Register a new model.

**Request**:
```json
{
  "name": "string",
  "description": "string",
  "model_type": "hallucination_detector|safety_classifier|bias_detector|content_filter|prompt_injection_detector|custom",
  "version": "string",
  "author": "string",
  "tags": ["string"],
  "license": "string"
}
```

**Response**: `ModelRegisterResponse`

---

### POST `/models/{model_id}/deploy`
Deploy a registered model.

**Request**:
```json
{
  "deployment_type": "serverless|dedicated|edge",
  "pricing_tier": "free|starter|pro|enterprise",
  "auto_scale": false
}
```

**Response**: `ModelDeploymentResponse`

---

### GET `/models/`
List all models with optional filtering.

**Query Parameters**:
- `model_type`: Filter by type
- `author`: Filter by author
- `tags`: Comma-separated tags
- `limit`: Max results (1-100)

**Response**: `ModelListResponse`

---

### GET `/models/{model_id}`
Get model details.

**Response**: Model metadata with stats

---

### GET `/models/{model_id}/deployments`
List all deployments for a model.

**Response**: `DeploymentListResponse`

---

### POST `/models/deployments/{deployment_id}/pause`
Pause a running deployment.

---

### POST `/models/deployments/{deployment_id}/resume`
Resume a paused deployment.

---

### DELETE `/models/deployments/{deployment_id}`
Delete a deployment.

---

### GET `/models/{model_id}/metrics`
Get usage metrics for a model.

**Response**: `UsageMetricsResponse`

---

### POST `/models/{model_id}/star`
Add a star to a model.

---

### GET `/models/popular`
Get most popular models.

**Query Parameters**:
- `limit`: Max results (1-50)

---

### GET `/models/search`
Search models by name, description, or tags.

**Query Parameters**:
- `q`: Search query (required)
- `limit`: Max results (1-100)

---

### GET `/models/pricing`
Get pricing information for all tiers.

---

### POST `/models/pricing/estimate`
Estimate monthly cost.

**Request**:
```json
{
  "pricing_tier": "free|starter|pro|enterprise",
  "requests_per_month": 1000000,
  "storage_gb": 10
}
```

**Response**: `CostEstimateResponse`

---

### GET `/models/health`
Health check endpoint.

---

## Use Cases

### 1. Deploy Custom Hallucination Detector

```python
# Register your custom model
model_id = register_model(
    name="CustomHallucinationDetector",
    description="Fine-tuned on domain-specific data",
    model_type="hallucination_detector",
    version="2.0.0",
    author="research-team",
    tags=["custom", "fine-tuned", "medical"]
)

# Deploy with auto-scaling
deployment = deploy_model(
    model_id=model_id,
    deployment_type="dedicated",
    pricing_tier="pro",
    auto_scale=True
)

# Model automatically scales from 1-10 instances based on demand
```

### 2. Share Community Model

```python
# Register open-source model
model_id = register_model(
    name="OpenSafetyClassifier",
    description="Open-source safety classifier for the community",
    model_type="safety_classifier",
    version="1.0.0",
    author="community",
    tags=["open-source", "safety", "community"],
    license="Apache-2.0"
)

# Deploy on free tier for community access
deployment = deploy_model(
    model_id=model_id,
    deployment_type="serverless",
    pricing_tier="free"
)

# Community can now use your model!
```

### 3. Enterprise Deployment

```python
# Register enterprise model
model_id = register_model(
    name="EnterpriseContentFilter",
    description="Enterprise-grade content filtering with custom rules",
    model_type="content_filter",
    version="3.0.0",
    author="enterprise-team",
    tags=["enterprise", "custom", "compliance"]
)

# Deploy with enterprise tier
deployment = deploy_model(
    model_id=model_id,
    deployment_type="dedicated",
    pricing_tier="enterprise",
    auto_scale=True
)

# Unlimited requests, SLA guarantees, dedicated support
```

### 4. Edge Deployment for Low Latency

```python
# Register latency-sensitive model
model_id = register_model(
    name="FastPromptInjectionDetector",
    description="Ultra-fast prompt injection detection",
    model_type="prompt_injection_detector",
    version="1.5.0",
    author="performance-team",
    tags=["fast", "edge", "real-time"]
)

# Deploy to edge locations
deployment = deploy_model(
    model_id=model_id,
    deployment_type="edge",
    pricing_tier="pro",
    auto_scale=True
)

# <10ms latency from edge locations worldwide
```

---

## Model Types

### Hallucination Detector
Detect when AI agents generate false or ungrounded information.

**Use Cases**: Fact-checking, knowledge validation, RAG verification

### Safety Classifier
Classify content for safety risks and policy violations.

**Use Cases**: Content moderation, compliance, risk assessment

### Bias Detector
Detect and quantify bias in AI outputs.

**Use Cases**: Fairness auditing, EU AI Act compliance, ethical AI

### Content Filter
Filter inappropriate or harmful content.

**Use Cases**: Parental controls, workplace safety, brand protection

### Prompt Injection Detector
Detect prompt injection and jailbreak attempts.

**Use Cases**: Security, adversarial defense, red teaming

### Custom
Deploy your own custom AI safety models.

**Use Cases**: Domain-specific safety, proprietary algorithms, research

---

## Deployment Types

### Serverless
- Auto-scaling serverless deployment
- Pay only for what you use
- No infrastructure management
- Best for: Variable workloads, development, testing

### Dedicated
- Dedicated compute instances
- Predictable performance
- Reserved capacity
- Best for: Production, consistent workloads, SLA requirements

### Edge
- Deploy to edge locations worldwide
- Ultra-low latency (<10ms)
- Global distribution
- Best for: Real-time applications, global users, latency-sensitive

---

## Usage Metrics

Track comprehensive metrics for your deployments:

- **Requests**: Daily, monthly, and total request counts
- **Errors**: Error rates and counts
- **Latency**: Average, P95, P99 latency metrics
- **Uptime**: Uptime percentage
- **Cost**: Monthly cost tracking

```python
# Get usage metrics
response = requests.get(
    f"https://agentguard-api.onrender.com/models/{model_id}/metrics"
)

metrics = response.json()
print(f"Total requests: {metrics['total_requests']}")
print(f"Average latency: {metrics['avg_latency_ms']}ms")
print(f"Uptime: {metrics['uptime_percentage']}%")
print(f"Cost this month: ${metrics['cost_this_month']}")
```

---

## Cost Estimation

Estimate costs before deploying:

```python
# Estimate cost
response = requests.post(
    "https://agentguard-api.onrender.com/models/pricing/estimate",
    json={
        "pricing_tier": "pro",
        "requests_per_month": 1000000,
        "storage_gb": 50
    }
)

estimate = response.json()
print(f"Base cost: ${estimate['base_cost']}/month")
print(f"Estimated total: ${estimate['estimated_total_cost']}/month")
```

---

## Community Features

### Star Models
Show appreciation for community models:

```python
# Star a model
requests.post(f"https://agentguard-api.onrender.com/models/{model_id}/star")
```

### Search Models
Discover models from the community:

```python
# Search for hallucination detectors
response = requests.get(
    "https://agentguard-api.onrender.com/models/search",
    params={"q": "hallucination", "limit": 10}
)

models = response.json()["models"]
for model in models:
    print(f"{model['name']} by {model['author']} - ⭐ {model['stars']}")
```

### Popular Models
See what's trending:

```python
# Get popular models
response = requests.get(
    "https://agentguard-api.onrender.com/models/popular",
    params={"limit": 10}
)

popular = response.json()
for model in popular:
    print(f"{model['name']} - ⭐ {model['stars']}  {model['downloads']}")
```

---

## Integration Examples

### Python SDK

```python
from agentguard_sdk import AgentGuardClient

client = AgentGuardClient(api_key="your_api_key")

# Register model
model = client.models.register(
    name="MyModel",
    description="My custom model",
    model_type="hallucination_detector",
    version="1.0.0",
    author="me"
)

# Deploy model
deployment = client.models.deploy(
    model_id=model.model_id,
    deployment_type="serverless",
    pricing_tier="free"
)

# Get metrics
metrics = client.models.get_metrics(model.model_id)
print(f"Total requests: {metrics.total_requests}")
```

### JavaScript/TypeScript

```typescript
import { AgentGuardClient } from '@agentguard/sdk';

const client = new AgentGuardClient({ apiKey: 'your_api_key' });

// Register model
const model = await client.models.register({
  name: 'MyModel',
  description: 'My custom model',
  modelType: 'hallucination_detector',
  version: '1.0.0',
  author: 'me'
});

// Deploy model
const deployment = await client.models.deploy(model.modelId, {
  deploymentType: 'serverless',
  pricingTier: 'free'
});

// Get metrics
const metrics = await client.models.getMetrics(model.modelId);
console.log(`Total requests: ${metrics.totalRequests}`);
```

### cURL

```bash
# Register model
curl -X POST https://agentguard-api.onrender.com/models/register \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key" \
  -d '{
    "name": "MyModel",
    "description": "My custom model",
    "model_type": "hallucination_detector",
    "version": "1.0.0",
    "author": "me"
  }'

# Deploy model
curl -X POST https://agentguard-api.onrender.com/models/{model_id}/deploy \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key" \
  -d '{
    "deployment_type": "serverless",
    "pricing_tier": "free",
    "auto_scale": false
  }'
```

---

## Best Practices

1. **Versioning**: Use semantic versioning for models (1.0.0, 1.1.0, 2.0.0)
2. **Tagging**: Add descriptive tags for discoverability
3. **Documentation**: Provide clear descriptions and usage examples
4. **Testing**: Test models thoroughly before deploying to production
5. **Monitoring**: Monitor metrics regularly and set up alerts
6. **Scaling**: Use auto-scaling for variable workloads
7. **Cost Management**: Estimate costs before deploying
8. **Community**: Share open-source models to build reputation

---

## Roadmap

**Q4 2025**:
- Model versioning and rollback
- A/B testing support
- Custom domains for deployments
- Webhook notifications
- Team collaboration features

**Q1 2026**:
- Model marketplace with revenue sharing
- Pre-trained model library
- Model fine-tuning service
- Advanced monitoring dashboards
- Multi-region deployment

---

## Support

- **Documentation**: [docs.agentguard.ai/model-hosting](https://docs.agentguard.ai/model-hosting)
- **Email**: info@mothership-ai.com
- **GitHub**: [github.com/agentguard/model-hosting](https://github.com/agentguard/model-hosting)
- **Community**: [community.agentguard.ai](https://community.agentguard.ai)

---

*Build the future of AI safety together with AgentGuard Model Hosting.*  
*Deploy. Scale. Protect.*

