# AgentGuard API Documentation
**Version 1.0.0** | **Last Updated: October 2025**

## Overview

AgentGuard is an enterprise-grade AI agent safety platform that provides real-time hallucination detection, agent management, and deployment capabilities. Our API enables developers to integrate advanced AI safety validation into their applications with 99%+ accuracy.

## Base URL
```
Production: https://api.agentguard.com
Staging: https://staging-api.agentguard.com
```

## Authentication

All API requests require authentication using API keys or JWT tokens.

### API Key Authentication
```http
Authorization: Bearer your_api_key_here
```

### JWT Token Authentication
```http
Authorization: Bearer your_jwt_token_here
```

## Rate Limits

| Tier | Requests/Minute | Queries/Month | Burst Limit |
|------|----------------|---------------|-------------|
| Free | 10 | 3 | 20 |
| Pro | 1000 | 1,000 | 2000 |
| Enterprise | 10000 | 50,000 | 20000 |
| BYOK | 5000 | Unlimited | 10000 |

## Core Endpoints

### 1. Hallucination Detection

#### Test Agent Output
Analyze AI agent output for hallucinations and safety issues.

```http
POST /test-agent
```

**Request Body:**
```json
{
  "agent_output": "The capital of France is Paris, with a population of 2.1 million.",
  "context": "Geography question about France",
  "expected_behavior": "Accurate factual response",
  "custom_rules": ["No harmful content", "Verify facts"]
}
```

**Response:**
```json
{
  "hallucination_risk": 0.12,
  "confidence": 0.94,
  "explanation": "Response appears factually accurate with low hallucination risk.",
  "statistical_score": 0.89,
  "claude_score": 0.96,
  "uncertainty": 0.06,
  "requires_human_review": false,
  "processing_time_ms": 87.3,
  "model_consensus": 0.92,
  "detailed_analysis": "Multi-model analysis confirms factual accuracy...",
  "metadata": {
    "ensemble_type": "advanced_2025",
    "models_used": ["claude-3-sonnet", "gpt-4", "statistical"],
    "target_accuracy": "99%+"
  }
}
```

### 2. Agent Management

#### Create Agent
Create a new AI agent with safety validation.

```http
POST /console/agents
```

**Request Body:**
```json
{
  "name": "Customer Support Bot",
  "description": "Handles customer inquiries with safety validation",
  "model": "claude-3-sonnet",
  "temperature": 0.7,
  "max_tokens": 1000,
  "system_prompt": "You are a helpful customer support agent...",
  "safety_rules": [
    "No harmful content",
    "Verify factual claims",
    "Respect privacy"
  ],
  "deployment_settings": {
    "auto_scale": true,
    "max_instances": 10,
    "timeout_seconds": 30,
    "memory_limit": "1GB"
  }
}
```

**Response:**
```json
{
  "id": "agent_12345",
  "name": "Customer Support Bot",
  "description": "Handles customer inquiries with safety validation",
  "status": "draft",
  "created_at": "2025-10-24T14:30:00Z",
  "updated_at": "2025-10-24T14:30:00Z",
  "safety_score": 0.89,
  "deployment_url": null,
  "webhook_url": null
}
```

#### List Agents
Get all agents for the current user.

```http
GET /console/agents
```

**Response:**
```json
[
  {
    "id": "agent_12345",
    "name": "Customer Support Bot",
    "status": "deployed",
    "safety_score": 0.94,
    "deployment_url": "https://api.agentguard.com/agents/agent_12345"
  }
]
```

#### Test Agent
Test an agent with specific input.

```http
POST /console/agents/{agent_id}/test
```

**Request Body:**
```json
{
  "input": "What is your refund policy?"
}
```

**Response:**
```json
{
  "id": "test_67890",
  "timestamp": "2025-10-24T14:35:00Z",
  "input": "What is your refund policy?",
  "output": "Our refund policy allows returns within 30 days...",
  "safety_score": 0.96,
  "issues": [],
  "passed": true,
  "processing_time_ms": 142.7
}
```

#### Deploy Agent
Deploy an agent to production.

```http
POST /console/agents/{agent_id}/deploy
```

**Request Body:**
```json
{
  "agent_id": "agent_12345",
  "environment": "production",
  "auto_scale": true,
  "max_instances": 10
}
```

**Response:**
```json
{
  "status": "deployed",
  "agent_id": "agent_12345",
  "deployment_url": "https://api.agentguard.com/agents/agent_12345",
  "webhook_url": "https://api.agentguard.com/webhooks/agent_12345",
  "message": "Agent deployed successfully"
}
```

### 3. Batch Processing

#### Upload Batch Job
Upload multiple test cases for batch processing.

```http
POST /batch/upload
```

**Request Body:**
```json
{
  "tests": [
    {
      "agent_output": "Test output 1",
      "context": "Context 1"
    },
    {
      "agent_output": "Test output 2", 
      "context": "Context 2"
    }
  ]
}
```

**Response:**
```json
{
  "job_id": "batch_abc123",
  "status": "uploaded",
  "total_items": 2,
  "created_at": "2025-10-24T14:40:00Z"
}
```

#### Start Batch Processing
Start processing a batch job.

```http
POST /batch/{job_id}/start
```

#### Get Batch Status
Check the status of a batch job.

```http
GET /batch/{job_id}
```

**Response:**
```json
{
  "job_id": "batch_abc123",
  "status": "completed",
  "total_items": 2,
  "processed_items": 2,
  "failed_items": 0,
  "progress_percentage": 100,
  "results_url": "https://api.agentguard.com/batch/batch_abc123/results"
}
```

### 4. Analytics & Insights

#### Get Analytics Overview
Get comprehensive analytics and insights.

```http
GET /analytics/insights?days=30
```

**Response:**
```json
{
  "period_days": 30,
  "total_tests": 2847,
  "average_risk_score": 0.23,
  "high_risk_detections": 89,
  "accuracy_rate": 0.994,
  "trends": {
    "risk_trend": "decreasing",
    "volume_trend": "increasing",
    "accuracy_trend": "stable"
  },
  "top_risk_categories": [
    {"category": "Medical Claims", "count": 23},
    {"category": "Financial Advice", "count": 18}
  ]
}
```

#### Get Workstation Insights
Get fleet-level workstation insights.

```http
GET /workstations/fleet/insights
```

### 5. Real-time Monitoring

#### WebSocket Connection
Connect to real-time monitoring via WebSocket.

```javascript
const ws = new WebSocket('wss://api.agentguard.com/ws/monitor');
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Real-time update:', data);
};
```

#### System Metrics
Get current system performance metrics.

```http
GET /metrics
```

**Response:**
```json
{
  "timestamp": "2025-10-24T14:45:00Z",
  "requests_per_minute": 1247,
  "average_response_time_ms": 87.3,
  "error_rate": 0.002,
  "active_connections": 89,
  "system": {
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "disk_usage": 23.1
  }
}
```

## Error Handling

All errors follow a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "agent_output",
      "issue": "Required field missing"
    },
    "request_id": "req_abc123"
  }
}
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `AUTH_ERROR` | Authentication failed | 401 |
| `RATE_LIMIT_ERROR` | Rate limit exceeded | 429 |
| `VALIDATION_ERROR` | Request validation failed | 422 |
| `QUOTA_EXCEEDED` | API quota exceeded | 402 |
| `AGENT_NOT_FOUND` | Agent not found | 404 |
| `DEPLOYMENT_ERROR` | Agent deployment failed | 500 |

## SDKs and Libraries

### Python SDK
```bash
pip install agentguard-sdk
```

```python
from agentguard_sdk import AgentGuardClient

client = AgentGuardClient(api_key="your_api_key")
result = await client.test_agent_output(
    agent_output="Your AI response here",
    context="Context information"
)
print(f"Safety Score: {result.confidence:.2f}")
```

### JavaScript SDK (Coming Soon)
```bash
npm install @agentguard/sdk
```

### cURL Examples

#### Test Agent Output
```bash
curl -X POST https://api.agentguard.com/test-agent \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_output": "The capital of France is Paris.",
    "context": "Geography question"
  }'
```

#### Create Agent
```bash
curl -X POST https://api.agentguard.com/console/agents \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Agent",
    "model": "claude-3-sonnet",
    "system_prompt": "You are a helpful assistant."
  }'
```

## Webhooks

Configure webhooks to receive real-time notifications about agent events.

### Webhook Events

| Event | Description |
|-------|-------------|
| `agent.deployed` | Agent successfully deployed |
| `agent.test.completed` | Agent test completed |
| `safety.alert` | High-risk output detected |
| `quota.warning` | Approaching quota limit |
| `quota.exceeded` | Quota limit exceeded |

### Webhook Payload Example
```json
{
  "event": "safety.alert",
  "timestamp": "2025-10-24T14:50:00Z",
  "data": {
    "agent_id": "agent_12345",
    "risk_score": 0.89,
    "output": "Potentially problematic response...",
    "issues": ["Unverified medical claim"]
  },
  "signature": "sha256=abc123..."
}
```

## Compliance & Security

### Data Privacy
- All data encrypted in transit (TLS 1.3) and at rest (AES-256)
- GDPR compliant with data retention policies
- SOC2 Type II certified
- HIPAA compliant for healthcare applications

### Audit Trails
All API calls are logged with:
- Request timestamp and user ID
- Input/output data (configurable retention)
- Processing results and metadata
- Compliance framework adherence

## Support & Resources

### Documentation
- **API Reference**: https://docs.agentguard.com/api
- **SDK Documentation**: https://docs.agentguard.com/sdk
- **Integration Guides**: https://docs.agentguard.com/integrations

### Support Channels
- **Email**: support@agentguard.com
- **Community**: https://community.agentguard.com
- **Enterprise**: Dedicated support manager

### Status Page
Monitor API status and incidents: https://status.agentguard.com

## Changelog

### v1.0.0 (October 2025)
- Initial public release
- Core hallucination detection API
- Agent Console and management
- Python SDK
- Batch processing
- Real-time monitoring
- Enterprise authentication

---

**Need Help?** Contact our support team at support@agentguard.com or visit our documentation at https://docs.agentguard.com
