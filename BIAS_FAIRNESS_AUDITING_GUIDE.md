# Bias and Fairness Auditing Guide

## Overview

AgentGuard's Bias and Fairness Auditing detects and mitigates bias in AI-generated content, ensuring fair and inclusive outputs that comply with ethical AI standards and regulations.

## Supported Bias Types

- **Gender Bias**: Stereotypes and discrimination based on gender
- **Racial Bias**: Racial stereotypes and discriminatory language
- **Age Bias**: Age-based discrimination and stereotypes
- **Ableist Language**: Discriminatory language toward people with disabilities
- **Non-Inclusive Language**: Exclusionary or non-inclusive terminology

## Quick Start

### Python SDK

```python
from agentguard_sdk import AgentGuardClient

client = AgentGuardClient(api_key="your_api_key")

result = client.bias_auditing(
    text="The nurse should be caring and empathetic.",
    context="Job description",
    check_types=["gender", "racial", "age"]
)

if result.has_bias:
    print(f"Bias detected: {result.bias_types}")
    print(f"Severity: {result.severity}")
    print(f"Fairness score: {result.fairness_score}")
    
    for instance in result.detected_instances:
        print(f"\nBias: {instance.bias_type}")
        print(f"Text: {instance.text_segment}")
        print(f"Suggestion: {instance.alternative_suggestion}")
```

### JavaScript/TypeScript SDK

```typescript
import { AgentGuardClient } from '@agentguard/sdk';

const client = new AgentGuardClient({ apiKey: 'your_api_key' });

const result = await client.auditBias({
  text: 'The nurse should be caring and empathetic.',
  context: 'Job description',
  check_types: ['gender', 'racial', 'age']
});

if (result.has_bias) {
  console.log('Bias types:', result.bias_types);
  console.log('Fairness score:', result.fairness_score);
}
```

### REST API

```bash
curl -X POST https://api.agentguard.io/bias/audit \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The nurse should be caring and empathetic.",
    "context": "Job description",
    "check_types": ["gender", "racial", "age"]
  }'
```

## Use Cases

### 1. Content Moderation

```python
def moderate_content(text):
    """Check content for bias before publishing"""
    result = client.bias_auditing(text=text)
    
    if result.severity in ["high", "critical"]:
        return {
            "approved": False,
            "reason": "High-severity bias detected",
            "suggestions": [i.alternative_suggestion for i in result.detected_instances]
        }
    
    return {"approved": True}
```

### 2. Job Description Review

```python
job_description = """
We're looking for young, energetic developers who can work long hours.
The ideal candidate is a rockstar programmer.
"""

result = client.bias_auditing(
    text=job_description,
    context="Job posting",
    check_types=["age", "gender", "ableist"]
)

if result.has_bias:
    print("Bias detected in job description:")
    for instance in result.detected_instances:
        print(f"- {instance.text_segment}")
        print(f"  Suggestion: {instance.alternative_suggestion}")
```

### 3. Marketing Copy Review

```python
marketing_text = "Our product is perfect for busy moms who need convenience."

result = client.bias_auditing(
    text=marketing_text,
    context="Marketing campaign"
)

print(f"Fairness score: {result.fairness_score}")
print(f"Compliance: {result.compliance_status}")
```

### 4. Educational Content Validation

```python
educational_content = """
Boys are naturally better at math and science,
while girls excel in language and arts.
"""

result = client.bias_auditing(
    text=educational_content,
    context="Educational material",
    check_types=["gender"]
)

if result.has_bias:
    print("Educational content contains gender bias")
    print(f"Severity: {result.severity}")
```

## API Reference

### Audit Text for Bias

**Endpoint**: `POST /bias/audit`

**Request**:
```json
{
  "text": "string",
  "context": "string (optional)",
  "check_types": ["gender", "racial", "age", "ableist", "non_inclusive"]
}
```

**Response**:
```json
{
  "has_bias": true,
  "bias_types": ["gender"],
  "severity": "medium",
  "confidence": 0.87,
  "detected_instances": [
    {
      "bias_type": "gender",
      "text_segment": "The nurse should be caring",
      "explanation": "Associates nursing with traditionally feminine traits",
      "alternative_suggestion": "The nurse should be professional and competent"
    }
  ],
  "fairness_score": 0.65,
  "recommendations": [
    "Use gender-neutral language",
    "Avoid stereotypical associations"
  ],
  "compliance_status": {
    "EU_AI_ACT": true,
    "NIST_RMF": true,
    "GDPR": true
  },
  "processing_time": 0.45
}
```

### Check Inclusive Language

**Endpoint**: `POST /bias/check-inclusive-language`

**Request**:
```json
{
  "text": "string"
}
```

**Response**:
```json
{
  "is_inclusive": false,
  "issues": [
    {
      "term": "guys",
      "suggestion": "everyone, folks, team"
    }
  ],
  "suggestions": ["Use gender-neutral terms"]
}
```

### Get Supported Bias Types

**Endpoint**: `GET /bias/bias-types`

**Response**:
```json
{
  "bias_types": [
    {
      "type": "gender",
      "description": "Gender stereotypes and discrimination",
      "examples": ["nurse (feminine)", "engineer (masculine)"]
    },
    {
      "type": "racial",
      "description": "Racial stereotypes and discrimination",
      "examples": ["All X are good at Y"]
    }
  ]
}
```

## Severity Levels

- **LOW**: Minor bias that may not require immediate action
- **MEDIUM**: Noticeable bias that should be addressed
- **HIGH**: Significant bias requiring correction
- **CRITICAL**: Severe bias that must be corrected immediately

## Fairness Score

The fairness score (0.0 - 1.0) represents overall content fairness:

- **0.9 - 1.0**: Highly fair and inclusive
- **0.7 - 0.9**: Generally fair with minor issues
- **0.5 - 0.7**: Moderate bias present
- **< 0.5**: Significant bias requiring attention

## Best Practices

### 1. Provide Context

```python
# Good - provides context
result = client.bias_auditing(
    text="The chairman will lead the meeting",
    context="Corporate governance document"
)

# Less effective - no context
result = client.bias_auditing(
    text="The chairman will lead the meeting"
)
```

### 2. Check Multiple Types

```python
# Comprehensive check
result = client.bias_auditing(
    text=content,
    check_types=["gender", "racial", "age", "ableist", "non_inclusive"]
)
```

### 3. Implement Suggestions

```python
def apply_bias_corrections(text):
    """Apply bias corrections to text"""
    result = client.bias_auditing(text=text)
    
    if not result.has_bias:
        return text
    
    corrected_text = text
    for instance in result.detected_instances:
        # Apply suggestions
        corrected_text = corrected_text.replace(
            instance.text_segment,
            instance.alternative_suggestion
        )
    
    return corrected_text
```

### 4. Monitor Fairness Trends

```python
def monitor_content_fairness(contents):
    """Monitor fairness across multiple content pieces"""
    scores = []
    
    for content in contents:
        result = client.bias_auditing(text=content)
        scores.append(result.fairness_score)
    
    avg_score = sum(scores) / len(scores)
    print(f"Average fairness score: {avg_score}")
    
    if avg_score < 0.7:
        print("Warning: Content fairness below threshold")
```

## Compliance Frameworks

AgentGuard checks compliance against:

- **EU AI Act**: Bias mitigation requirements
- **NIST AI Risk Management Framework**: Fairness guidelines
- **GDPR**: Non-discrimination requirements
- **ISO 27001**: Information security and fairness

## Advanced Configuration

### Custom Bias Detection

```python
# Focus on specific bias types for your use case
result = client.bias_auditing(
    text=text,
    check_types=["gender", "age"]  # Only check these types
)
```

### Batch Processing

```python
def audit_batch(texts):
    """Audit multiple texts"""
    results = []
    
    for text in texts:
        result = client.bias_auditing(text=text)
        if result.has_bias:
            results.append({
                "text": text,
                "bias_types": result.bias_types,
                "severity": result.severity
            })
    
    return results
```

### Integration with Content Pipelines

```python
class ContentPipeline:
    def __init__(self, client):
        self.client = client
    
    def process_content(self, content):
        """Process content through bias auditing"""
        result = self.client.bias_auditing(text=content)
        
        if result.severity in ["high", "critical"]:
            # Reject content
            return {"status": "rejected", "reason": "High-severity bias"}
        
        if result.has_bias:
            # Flag for review
            return {
                "status": "review",
                "suggestions": [i.alternative_suggestion for i in result.detected_instances]
            }
        
        return {"status": "approved"}
```

## Common Bias Patterns

### Gender Bias Examples

```python
# Stereotypical associations
"The nurse was caring and gentle"  # Associates nursing with feminine traits
"The engineer solved the problem logically"  # Associates engineering with masculine traits

# Better alternatives
"The nurse was professional and competent"
"The engineer solved the problem effectively"
```

### Age Bias Examples

```python
# Age discrimination
"We need young, energetic employees"
"Looking for digital natives"

# Better alternatives
"We need motivated, enthusiastic employees"
"Looking for candidates with strong digital skills"
```

### Non-Inclusive Language Examples

```python
# Exclusionary terms
"Hey guys, let's meet"
"The chairman will decide"

# Better alternatives
"Hey everyone, let's meet"
"The chairperson will decide"
```

## Error Handling

```python
from agentguard_sdk import AgentGuardError

try:
    result = client.bias_auditing(text=content)
except AgentGuardError as e:
    if e.statusCode == 400:
        print("Invalid request format")
    elif e.statusCode == 429:
        print("Rate limit exceeded")
    else:
        print(f"Error: {e.message}")
```

## Performance Optimization

### Caching Results

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def audit_with_cache(text):
    """Cache audit results for repeated text"""
    return client.bias_auditing(text=text)
```

### Async Processing

```python
import asyncio

async def audit_multiple_async(texts):
    """Process multiple texts concurrently"""
    tasks = [
        client.bias_auditing_async(text=text)
        for text in texts
    ]
    return await asyncio.gather(*tasks)
```

## Limitations

- **Language Support**: Currently optimized for English
- **Context Sensitivity**: May require human review for nuanced cases
- **Cultural Variations**: Bias detection may vary across cultures
- **Rate Limits**: 100 requests per minute per API key

## Troubleshooting

### False Positives

If you're getting unexpected bias detections:

1. Provide more context in the `context` field
2. Review the explanation for each detected instance
3. Check if the text is using terms in a neutral way
4. Consider the specific use case and audience

### Low Fairness Scores

To improve fairness scores:

1. Use gender-neutral language
2. Avoid stereotypical associations
3. Include diverse perspectives
4. Apply suggested alternatives

## Support

- Documentation: https://docs.agentguard.io/bias-auditing
- API Reference: https://api.agentguard.io/docs
- Support: support@agentguard.io

