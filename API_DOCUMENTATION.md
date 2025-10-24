# AgentGuard API Documentation

**Version:** 2.0.0  
**Base URL:** `https://watcher-api.onrender.com`  
**Authentication:** API Key (Header: `X-API-Key`)

---

## 🚀 Quick Start

### Authentication

All API requests require an API key in the header:

```bash
curl -H "X-API-Key: your_api_key_here" \
     -H "Content-Type: application/json" \
     https://watcher-api.onrender.com/health
```

### Basic Detection

```bash
curl -X POST https://watcher-api.onrender.com/test-agent \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_output": "The Eiffel Tower is 500 meters tall and made of gold.",
    "ground_truth": "The Eiffel Tower is 330 meters tall and made of iron."
  }'
```

---

## 📋 Table of Contents

1. [Core Detection APIs](#core-detection-apis)
2. [Real-time Streaming](#real-time-streaming)
3. [Agent Pipeline](#agent-pipeline)
4. [Multilingual Detection](#multilingual-detection)
5. [Multimodal Detection](#multimodal-detection)
6. [Analytics & Monitoring](#analytics--monitoring)
7. [Beta Program](#beta-program)
8. [Error Handling](#error-handling)
9. [Rate Limits](#rate-limits)
10. [SDKs & Examples](#sdks--examples)

---

## 🎯 Core Detection APIs

### POST `/test-agent`

**Primary hallucination detection endpoint**

Analyzes text for hallucination indicators using ensemble of judges.

#### Request Body

```json
{
  "agent_output": "string (required) - Text to analyze",
  "ground_truth": "string (optional) - Reference text for comparison",
  "context": "string (optional) - Additional context",
  "model_type": "string (optional) - Model identifier",
  "domain": "string (optional) - Content domain (general, technical, creative)",
  "language": "string (optional) - Content language (default: en)"
}
```

#### Response

```json
{
  "hallucination_score": 0.23,
  "confidence": 0.87,
  "explanation": "Low hallucination risk detected...",
  "judge_results": {
    "claude_judge": {
      "score": 0.15,
      "confidence": 0.92,
      "reasoning": "Content appears factually accurate..."
    },
    "statistical_judge": {
      "score": 0.31,
      "confidence": 0.82,
      "attention_metrics": {...}
    }
  },
  "recommendations": [
    "Content appears reliable",
    "Consider additional verification for critical use cases"
  ],
  "processing_time_ms": 145.7,
  "timestamp": "2025-10-24T12:00:00Z"
}
```

#### Example Usage

```python
import requests

response = requests.post(
    "https://watcher-api.onrender.com/test-agent",
    headers={"X-API-Key": "your_api_key"},
    json={
        "agent_output": "Paris is the capital of France with 2.1 million people.",
        "ground_truth": "Paris is the capital of France.",
        "domain": "general"
    }
)

result = response.json()
print(f"Hallucination Score: {result['hallucination_score']:.3f}")
```

### GET `/health`

**System health check**

Returns system status and performance metrics.

#### Response

```json
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime_seconds": 86400,
  "judges_available": ["claude", "statistical", "ensemble"],
  "performance": {
    "avg_response_time_ms": 142.3,
    "requests_per_minute": 45,
    "success_rate": 99.7
  }
}
```

---

## ⚡ Real-time Streaming

### GET `/stream-detect`

**Server-Sent Events for real-time detection**

Streams hallucination detection results in real-time with <100ms latency.

#### Query Parameters

- `text` (required): Text to analyze
- `context` (optional): Reference context
- `threshold` (optional): Alert threshold (default: 0.7)

#### Response Stream

```
data: {"type": "analysis_start", "timestamp": "2025-10-24T12:00:00Z"}

data: {"type": "token_analysis", "token": "Paris", "uncertainty": 0.12}

data: {"type": "final_result", "hallucination_score": 0.23, "confidence": 0.87}

data: {"type": "analysis_complete", "processing_time_ms": 89.4}
```

#### Example Usage

```javascript
const eventSource = new EventSource(
  'https://watcher-api.onrender.com/stream-detect?text=Your text here&threshold=0.6'
);

eventSource.onmessage = function(event) {
  const data = JSON.parse(event.data);
  
  if (data.type === 'final_result') {
    console.log(`Hallucination Score: ${data.hallucination_score}`);
  }
};
```

### WebSocket `/ws/monitor`

**WebSocket connection for real-time monitoring**

Provides bidirectional real-time communication for continuous monitoring.

#### Connection

```javascript
const ws = new WebSocket('wss://watcher-api.onrender.com/ws/monitor');

ws.onopen = function() {
  // Send configuration
  ws.send(JSON.stringify({
    type: 'configure',
    threshold: 0.7,
    domains: ['general', 'technical']
  }));
};

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Real-time result:', data);
};
```

---

## 🤖 Agent Pipeline

### POST `/agent-pipeline/process`

**4-agent fact-checking pipeline with auto-correction**

Processes text through Generate → Review → Clarify → Score workflow.

#### Request Body

```json
{
  "agent_output": "string (required) - Text to process",
  "ground_truth": "string (optional) - Reference text",
  "domain": "string (optional) - Content domain",
  "enable_auto_correction": true
}
```

#### Response

```json
{
  "status": "success",
  "pipeline_result": {
    "original_text": "Original input text",
    "corrected_text": "Auto-corrected text if needed",
    "hallucination_score": 0.15,
    "correction_applied": true,
    "pipeline_confidence": 0.92,
    "improvement_metrics": {
      "accuracy_improvement": 0.23,
      "confidence_boost": 0.18
    },
    "processing_time_ms": 234.5
  },
  "agent_analysis": [
    {
      "agent_role": "generator",
      "stage": "generate",
      "confidence": 0.85,
      "reasoning": "Generated alternative phrasing...",
      "processing_time_ms": 45.2
    }
  ],
  "recommendations": {
    "use_corrected_text": true,
    "requires_human_review": false,
    "confidence_level": "high"
  }
}
```

### GET `/agent-pipeline/stats`

**Pipeline performance statistics**

Returns performance metrics for the 4-agent pipeline.

#### Response

```json
{
  "total_processed": 1247,
  "correction_rate": 0.23,
  "average_improvement": 0.31,
  "processing_time_stats": {
    "mean_ms": 198.4,
    "p95_ms": 312.1,
    "p99_ms": 445.7
  },
  "agent_performance": {
    "generator": {"avg_time_ms": 45.2, "success_rate": 0.98},
    "reviewer": {"avg_time_ms": 52.1, "success_rate": 0.96},
    "clarifier": {"avg_time_ms": 48.7, "success_rate": 0.97},
    "scorer": {"avg_time_ms": 41.3, "success_rate": 0.99}
  }
}
```

---

## 🌍 Multilingual Detection

### POST `/multilingual/detect`

**Multilingual hallucination detection with span-level analysis**

Supports 14 languages with automatic language detection.

#### Request Body

```json
{
  "text": "string (required) - Text in any supported language",
  "context": "string (optional) - Reference context",
  "target_language": "string (optional) - Force specific language"
}
```

#### Response

```json
{
  "status": "success",
  "multilingual_result": {
    "text": "Input text",
    "detected_language": "es",
    "language_confidence": 0.94,
    "hallucination_score": 0.18,
    "model_used": "multilingual_v2",
    "processing_time_ms": 167.3
  },
  "language_analysis": {
    "language_code": "es",
    "language_name": "Spanish",
    "confidence_threshold": 0.7,
    "detection_confidence": 0.94
  },
  "span_analysis": {
    "total_spans": 12,
    "flagged_spans": 1,
    "spans": [
      {
        "text": "Madrid",
        "start": 0,
        "end": 6,
        "is_flagged": false,
        "confidence": 0.92
      }
    ]
  }
}
```

### GET `/multilingual/languages`

**Supported languages list**

Returns list of supported languages and their capabilities.

#### Response

```json
{
  "supported_languages": {
    "en": {"name": "English", "accuracy": 0.95, "span_detection": true},
    "es": {"name": "Spanish", "accuracy": 0.92, "span_detection": true},
    "fr": {"name": "French", "accuracy": 0.91, "span_detection": true}
  },
  "total_languages": 14,
  "default_language": "en"
}
```

---

## 🖼️ Multimodal Detection

### POST `/multimodal/detect-image`

**Image hallucination detection with text alignment**

Analyzes images for fake objects, impossible scenes, and text-image alignment.

#### Request (Multipart Form)

```
Content-Type: multipart/form-data

image: [image file]
text_description: "A red car in front of a blue building" (optional)
content_type: "image" (optional)
```

#### Response

```json
{
  "status": "success",
  "multimodal_result": {
    "content_type": "image_text",
    "hallucination_score": 0.12,
    "confidence": 0.89,
    "text_image_alignment": 0.87,
    "processing_time_ms": 178.4
  },
  "object_detection": {
    "detected_objects": [
      {
        "label": "car",
        "confidence": 0.94,
        "bounding_box": {"x": 120, "y": 80, "width": 200, "height": 150}
      }
    ],
    "object_count": 3
  },
  "visual_analysis": {
    "inconsistencies": [],
    "inconsistency_count": 0,
    "high_severity_issues": 0
  },
  "recommendations": {
    "requires_review": false,
    "confidence_level": "high",
    "text_alignment_good": true
  }
}
```

### POST `/multimodal/detect-video`

**Video hallucination detection with temporal consistency**

Analyzes videos for temporal inconsistencies and impossible movements.

#### Request (Multipart Form)

```
Content-Type: multipart/form-data

video: [video file]
text_description: "A person walking in a park" (optional)
max_duration_seconds: 30 (optional)
```

#### Response

```json
{
  "status": "success",
  "multimodal_result": {
    "content_type": "video",
    "hallucination_score": 0.08,
    "confidence": 0.91,
    "processing_time_ms": 2341.7
  },
  "video_analysis": {
    "frame_count": 150,
    "analyzed_frames": 30,
    "temporal_consistency_score": 0.94,
    "average_objects_per_frame": 2.3
  },
  "temporal_analysis": {
    "inconsistencies": [],
    "scene_changes": 2
  }
}
```

### GET `/multimodal/capabilities`

**Multimodal detection capabilities**

Returns supported formats and performance metrics.

#### Response

```json
{
  "capabilities": {
    "supported_formats": {
      "images": ["JPEG", "PNG", "GIF", "BMP", "TIFF"],
      "videos": ["MP4", "AVI", "MOV", "MKV", "WEBM"],
      "max_image_size_mb": 10,
      "max_video_size_mb": 100
    },
    "detection_features": [
      "Object detection and verification",
      "Scene consistency analysis",
      "Adversarial content detection",
      "Text-image semantic alignment"
    ],
    "performance_targets": {
      "image_processing_ms": 200,
      "video_processing_per_second": 2,
      "accuracy_target": 0.90
    }
  }
}
```

---

## 📊 Analytics & Monitoring

### GET `/analytics/overview`

**Analytics dashboard overview**

Returns comprehensive analytics and trend analysis.

#### Query Parameters

- `time_window_hours` (optional): Analysis window (default: 24)
- `group_by` (optional): Grouping granularity (hour, day, week)

#### Response

```json
{
  "report_timestamp": "2025-10-24T12:00:00Z",
  "time_window_hours": 24,
  "summary": {
    "total_insights": 12,
    "critical_insights": 1,
    "high_priority_insights": 3,
    "data_points_analyzed": 1247
  },
  "trend_analysis": {
    "trend_direction": "stable",
    "trend_magnitude": 0.02,
    "overall_stats": {
      "avg_hallucination_score": 0.23,
      "high_risk_percentage": 8.4
    },
    "model_breakdown": {
      "claude": {"mean": 0.18, "count": 523},
      "statistical": {"mean": 0.28, "count": 724}
    }
  },
  "recommendations": [
    "System performance appears normal",
    "Monitor domain 'technical' for elevated scores"
  ]
}
```

### GET `/metrics`

**System performance metrics**

Returns detailed system performance and usage metrics.

#### Response

```json
{
  "system_health": {
    "status": "healthy",
    "uptime_hours": 168.3,
    "memory_usage_mb": 2048,
    "cpu_usage_percent": 23.4
  },
  "api_metrics": {
    "total_requests": 15247,
    "requests_per_minute": 42.3,
    "average_response_time_ms": 156.7,
    "success_rate": 99.8,
    "error_rate": 0.2
  },
  "detection_metrics": {
    "total_detections": 12834,
    "high_risk_detections": 1076,
    "average_hallucination_score": 0.24,
    "judge_performance": {
      "claude": {"accuracy": 0.94, "avg_time_ms": 89.2},
      "statistical": {"accuracy": 0.87, "avg_time_ms": 45.1}
    }
  }
}
```

---

## 🧪 Beta Program

### POST `/beta/apply`

**Apply for beta program**

Submit application for beta testing program.

#### Request Body

```json
{
  "email": "user@company.com",
  "name": "John Doe",
  "company": "Acme Corp",
  "use_case": "Chatbot response validation"
}
```

#### Response

```json
{
  "success": true,
  "message": "Application submitted successfully",
  "user_id": "uuid-here",
  "status": "approved",
  "api_key": "ag_beta_abc123def456"
}
```

### POST `/beta/feedback`

**Submit beta feedback**

Submit feedback during beta testing.

#### Request Body

```json
{
  "user_id": "uuid-here",
  "feedback_type": "bug_report",
  "priority": "high",
  "title": "API timeout on large requests",
  "description": "Detailed description...",
  "steps_to_reproduce": "1. Send large request...",
  "environment_info": {"browser": "Chrome", "os": "macOS"}
}
```

---

## ❌ Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "Agent output cannot be empty",
    "details": {
      "field": "agent_output",
      "received": "",
      "expected": "non-empty string"
    }
  },
  "timestamp": "2025-10-24T12:00:00Z",
  "request_id": "req_abc123"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_INPUT` | 400 | Invalid request parameters |
| `UNAUTHORIZED` | 401 | Invalid or missing API key |
| `RATE_LIMITED` | 429 | Rate limit exceeded |
| `MODEL_ERROR` | 500 | Internal model processing error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### Error Handling Best Practices

```python
import requests
from requests.exceptions import RequestException

def detect_hallucination(text, api_key):
    try:
        response = requests.post(
            "https://watcher-api.onrender.com/test-agent",
            headers={"X-API-Key": api_key},
            json={"agent_output": text},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            print("Rate limited - please wait before retrying")
            return None
        else:
            error_data = response.json()
            print(f"API Error: {error_data['error']['message']}")
            return None
            
    except RequestException as e:
        print(f"Request failed: {e}")
        return None
```

---

## 🚦 Rate Limits

### Current Limits

| Plan | Requests/Minute | Requests/Day | Concurrent |
|------|-----------------|--------------|------------|
| **Free** | 10 | 1,000 | 2 |
| **Starter** | 100 | 10,000 | 5 |
| **Pro** | 1,000 | 100,000 | 20 |
| **Enterprise** | Custom | Custom | Custom |

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1635724800
X-RateLimit-Window: 60
```

### Handling Rate Limits

```python
import time

def make_request_with_retry(url, headers, data, max_retries=3):
    for attempt in range(max_retries):
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            print(f"Rate limited. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
            continue
            
        return response
    
    raise Exception("Max retries exceeded")
```

---

## 🛠️ SDKs & Examples

### Python SDK

```bash
pip install agentguard-python
```

```python
from agentguard import AgentGuardClient

client = AgentGuardClient(api_key="your_api_key")

# Basic detection
result = client.detect_hallucination(
    text="The Eiffel Tower is 500 meters tall",
    context="The Eiffel Tower is 330 meters tall"
)

print(f"Score: {result.hallucination_score}")
print(f"Confidence: {result.confidence}")

# Streaming detection
for update in client.stream_detect(text="Your text here"):
    if update.type == "final_result":
        print(f"Final score: {update.hallucination_score}")
```

### JavaScript SDK

```bash
npm install agentguard-js
```

```javascript
import { AgentGuardClient } from 'agentguard-js';

const client = new AgentGuardClient({ apiKey: 'your_api_key' });

// Basic detection
const result = await client.detectHallucination({
  text: 'The Eiffel Tower is 500 meters tall',
  context: 'The Eiffel Tower is 330 meters tall'
});

console.log(`Score: ${result.hallucinationScore}`);

// Real-time streaming
const stream = client.streamDetect({
  text: 'Your text here',
  threshold: 0.7
});

stream.on('result', (data) => {
  console.log('Real-time result:', data);
});
```

### cURL Examples

#### Basic Detection

```bash
curl -X POST https://watcher-api.onrender.com/test-agent \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_output": "The sky is green and grass is blue",
    "ground_truth": "The sky is blue and grass is green",
    "domain": "general"
  }'
```

#### Image Analysis

```bash
curl -X POST https://watcher-api.onrender.com/multimodal/detect-image \
  -H "X-API-Key: your_api_key" \
  -F "image=@/path/to/image.jpg" \
  -F "text_description=A red car in a parking lot"
```

#### Batch Processing

```bash
curl -X POST https://watcher-api.onrender.com/multimodal/batch-images \
  -H "X-API-Key: your_api_key" \
  -F "images=@image1.jpg" \
  -F "images=@image2.jpg" \
  -F "text_descriptions=First image description" \
  -F "text_descriptions=Second image description"
```

---

## 🔗 Integration Examples

### LangChain Integration

```python
from langchain.callbacks.base import BaseCallbackHandler
from agentguard import AgentGuardClient

class HallucinationCallback(BaseCallbackHandler):
    def __init__(self, api_key, threshold=0.7):
        self.client = AgentGuardClient(api_key=api_key)
        self.threshold = threshold
    
    def on_llm_end(self, response, **kwargs):
        text = response.generations[0][0].text
        result = self.client.detect_hallucination(text=text)
        
        if result.hallucination_score > self.threshold:
            print(f"⚠️ High hallucination risk: {result.hallucination_score:.3f}")
            print(f"Recommendations: {result.recommendations}")

# Usage
from langchain.llms import OpenAI

llm = OpenAI(callbacks=[HallucinationCallback("your_api_key")])
response = llm("Tell me about the Eiffel Tower")
```

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from agentguard import AgentGuardClient

app = FastAPI()
guard_client = AgentGuardClient(api_key="your_api_key")

@app.post("/safe-generate")
async def safe_generate(text: str, threshold: float = 0.7):
    # Your text generation logic here
    generated_text = generate_text(text)
    
    # Check for hallucinations
    result = guard_client.detect_hallucination(text=generated_text)
    
    if result.hallucination_score > threshold:
        raise HTTPException(
            status_code=400,
            detail=f"High hallucination risk detected: {result.hallucination_score:.3f}"
        )
    
    return {
        "text": generated_text,
        "hallucination_score": result.hallucination_score,
        "confidence": result.confidence
    }
```

---

## 📞 Support & Resources

### Documentation

- **API Reference**: [docs.agentguard.ai](https://docs.agentguard.ai)
- **Tutorials**: [docs.agentguard.ai/tutorials](https://docs.agentguard.ai/tutorials)
- **Examples**: [github.com/mothership-ai/agentguard-examples](https://github.com/mothership-ai/agentguard-examples)

### Community

- **Discord**: [Join our community](https://discord.gg/agentguard)
- **GitHub**: [github.com/mothership-ai/agentguard](https://github.com/mothership-ai/agentguard)
- **Blog**: [blog.mothership-ai.com](https://blog.mothership-ai.com)

### Support

- **Email**: support@mothership-ai.com
- **Beta Support**: beta-support@mothership-ai.com
- **Enterprise**: enterprise@mothership-ai.com

### Status Page

- **System Status**: [status.agentguard.ai](https://status.agentguard.ai)
- **API Uptime**: 99.9% SLA
- **Response Time**: <200ms average

---

**Last Updated:** October 24, 2025  
**API Version:** 2.0.0  
**Documentation Version:** 1.0.0

*For the most up-to-date information, please visit [docs.agentguard.ai](https://docs.agentguard.ai)*
