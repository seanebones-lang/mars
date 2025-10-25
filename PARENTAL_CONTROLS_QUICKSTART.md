# Parental Controls & Age Prediction - Quick Start Guide

**AgentGuard Parental Controls**  
Family-friendly content filtering and age prediction for education and family vertical markets.

**Version**: 1.0.0  
**Date**: October 2025  
**Author**: AgentGuard Engineering Team

---

## Overview

The Parental Controls feature provides comprehensive family safety tools for AI interactions:

- **Age Prediction**: Automatically detect user age groups from interaction patterns
- **Content Filtering**: Filter inappropriate content based on age appropriateness
- **Risk Detection**: Identify 10+ risk categories including violence, profanity, self-harm
- **Crisis Intervention**: Automatic crisis resource recommendations for self-harm content
- **Batch Processing**: Efficient filtering of multiple content items
- **Compliance**: COPPA and FERPA considerations for education markets

---

## Key Features

### Age Groups
- **Child** (0-12 years): Maximum protection, EVERYONE rating only
- **Teen** (13-17 years): Moderate content allowed, configurable strict mode
- **Young Adult** (18-25 years): Most content allowed except BLOCKED
- **Adult** (26+ years): All appropriate content allowed
- **Unknown**: Conservative filtering when age cannot be determined

### Risk Categories
- Violence
- Profanity
- Sexual Content
- Substance Use
- Hate Speech (CRITICAL - always blocked)
- Bullying
- Self-Harm (CRITICAL - always blocked + crisis resources)
- Personal Info Sharing (for children/teens)
- Stranger Danger
- Inappropriate Contact

### Content Ratings
- **E** (Everyone): All ages
- **E10+** (Everyone 10+): Mild content
- **T** (Teen): 13+ appropriate
- **M** (Mature): 17+ appropriate
- **AO** (Adults Only): 18+ only
- **Unrated**: Not yet rated

---

## Quick Start

### 1. Age Prediction

Predict user's age group from interaction patterns:

```python
import requests

# Predict age from text
response = requests.post(
    "https://agentguard-api.onrender.com/parental-controls/predict-age",
    json={
        "text": "I'm in high school and have a big test tomorrow.",
        "interaction_history": [
            "I have homework to do",
            "My teacher gave us an assignment"
        ]
    }
)

result = response.json()
print(f"Age Group: {result['predicted_age_group']}")
print(f"Confidence: {result['confidence']:.0%}")
print(f"Recommended Rating: {result['recommended_content_rating']}")
```

**Response**:
```json
{
  "predicted_age_group": "teen",
  "confidence": 0.85,
  "indicators": ["high school", "test", "homework"],
  "explanation": "Predicted age group: teen (confidence: 85%) based on indicators: high school, test, homework",
  "recommended_content_rating": "teen"
}
```

### 2. Content Filtering

Filter content for age appropriateness:

```python
# Filter content for a child
response = requests.post(
    "https://agentguard-api.onrender.com/parental-controls/filter-content",
    json={
        "content": "This story has some violence and fighting.",
        "age_group": "child",
        "strict_mode": False
    }
)

result = response.json()
print(f"Appropriate: {result['is_appropriate']}")
print(f"Risk Level: {result['risk_level']}")
print(f"Categories: {result['risk_categories']}")
```

**Response**:
```json
{
  "is_appropriate": false,
  "risk_level": "medium_risk",
  "risk_categories": ["violence"],
  "blocked_content": ["violence", "fighting"],
  "filtered_content": "This story has some ******** and ********.",
  "explanation": "Content is NOT appropriate for child age group. Risk level: medium_risk. Detected: violence",
  "recommendations": [
    "Block or filter this content before displaying to user",
    "Content not suitable for child age group"
  ],
  "age_group": "child",
  "content_rating": "mature"
}
```

### 3. Batch Filtering

Filter multiple content items efficiently:

```python
# Batch filter conversation history
response = requests.post(
    "https://agentguard-api.onrender.com/parental-controls/filter-batch",
    json={
        "contents": [
            "We will learn about animals!",
            "This has some damn profanity.",
            "Educational content for kids.",
            "Violence and weapons discussion."
        ],
        "age_group": "child",
        "strict_mode": True
    }
)

result = response.json()
print(f"Total: {result['summary']['total_items']}")
print(f"Blocked: {result['summary']['blocked_items']}")
print(f"Appropriate: {result['summary']['appropriate_items']}")
```

**Response**:
```json
{
  "results": [...],
  "summary": {
    "total_items": 4,
    "blocked_items": 2,
    "high_risk_items": 1,
    "appropriate_items": 2,
    "risk_categories_found": ["profanity", "violence"],
    "age_group": "child",
    "strict_mode": true
  }
}
```

---

## API Endpoints

### POST `/parental-controls/predict-age`
Predict user's age group from text and interaction history.

**Request**:
```json
{
  "text": "string",
  "interaction_history": ["string"] // optional
}
```

**Response**: `AgeDetectionResponse`

---

### POST `/parental-controls/filter-content`
Filter content for age appropriateness.

**Request**:
```json
{
  "content": "string",
  "age_group": "child|teen|young_adult|adult|unknown",
  "strict_mode": false
}
```

**Response**: `ContentFilterResponse`

---

### POST `/parental-controls/filter-batch`
Batch filter multiple content items.

**Request**:
```json
{
  "contents": ["string"],
  "age_group": "child|teen|young_adult|adult|unknown",
  "strict_mode": false
}
```

**Response**: `BatchContentFilterResponse`

---

### GET `/parental-controls/age-groups`
List available age groups with descriptions.

**Response**: Array of age group definitions

---

### GET `/parental-controls/content-ratings`
List content rating system.

**Response**: Array of content ratings

---

### GET `/parental-controls/risk-categories`
List risk categories monitored.

**Response**: Array of risk categories

---

### GET `/parental-controls/health`
Health check endpoint.

**Response**: Service health status

---

## Use Cases

### 1. Educational Platforms

Filter classroom content and student interactions:

```python
# Filter student chat message
def filter_student_message(message, student_age):
    response = requests.post(
        f"{API_BASE}/parental-controls/filter-content",
        json={
            "content": message,
            "age_group": "child" if student_age < 13 else "teen",
            "strict_mode": True
        }
    )
    result = response.json()
    
    if not result['is_appropriate']:
        # Alert teacher and block message
        alert_teacher(result)
        return None
    
    return message
```

### 2. Family Chat Applications

Real-time content filtering for family-friendly chat:

```python
# Real-time chat filtering
def process_chat_message(message, user_profile):
    # Predict age if not known
    if not user_profile.get('age_group'):
        age_result = requests.post(
            f"{API_BASE}/parental-controls/predict-age",
            json={"text": message, "interaction_history": user_profile.get('history', [])}
        ).json()
        user_profile['age_group'] = age_result['predicted_age_group']
    
    # Filter content
    filter_result = requests.post(
        f"{API_BASE}/parental-controls/filter-content",
        json={
            "content": message,
            "age_group": user_profile['age_group'],
            "strict_mode": user_profile.get('parental_controls_enabled', False)
        }
    ).json()
    
    # Handle self-harm detection
    if 'self_harm' in filter_result['risk_categories']:
        notify_crisis_team(user_profile, filter_result)
        return filter_result['recommendations']
    
    # Return filtered or original content
    return filter_result['filtered_content'] if filter_result['filtered_content'] else message
```

### 3. Content Moderation

Bulk content moderation for user-generated content:

```python
# Moderate user-generated content
def moderate_content_batch(content_items, target_age_group='child'):
    response = requests.post(
        f"{API_BASE}/parental-controls/filter-batch",
        json={
            "contents": content_items,
            "age_group": target_age_group,
            "strict_mode": True
        }
    )
    results = response.json()
    
    # Separate safe and unsafe content
    safe_content = []
    flagged_content = []
    
    for i, result in enumerate(results['results']):
        if result['is_appropriate']:
            safe_content.append(content_items[i])
        else:
            flagged_content.append({
                'content': content_items[i],
                'reason': result['explanation'],
                'categories': result['risk_categories']
            })
    
    return safe_content, flagged_content
```

### 4. AI Tutoring Systems

Age-appropriate responses from AI tutors:

```python
# Filter AI tutor responses
def generate_tutor_response(student_question, student_age_group):
    # Generate response from AI
    ai_response = generate_ai_response(student_question)
    
    # Filter response for age appropriateness
    filter_result = requests.post(
        f"{API_BASE}/parental-controls/filter-content",
        json={
            "content": ai_response,
            "age_group": student_age_group,
            "strict_mode": True
        }
    ).json()
    
    if not filter_result['is_appropriate']:
        # Regenerate with stricter guidelines
        return regenerate_response_safe(student_question, student_age_group)
    
    return ai_response
```

---

## Performance

- **Age Prediction**: <100ms per request
- **Content Filtering**: <100ms per item
- **Batch Filtering**: <500ms for 5 items
- **Pattern Matching**: Regex-based for efficiency
- **Scalability**: Stateless service, horizontally scalable

---

## Compliance & Safety

### COPPA Compliance
- Age verification support
- Parental consent workflows
- Personal information protection for children

### FERPA Compliance
- Educational records protection
- Student privacy safeguards
- Secure data handling

### Crisis Intervention
- Automatic detection of self-harm content
- Crisis resource recommendations (988 Suicide & Crisis Lifeline)
- Alert mechanisms for guardians/administrators

---

## Pricing

**Family & Education Add-On**: $29/month per organization

Includes:
- Unlimited age predictions
- Unlimited content filtering
- Batch processing
- Real-time API access
- Crisis intervention features
- Compliance reporting

**Enterprise**: Custom pricing for large-scale deployments

---

## Integration Examples

### Python SDK

```python
from agentguard_sdk import AgentGuardClient

client = AgentGuardClient(api_key="your_api_key")

# Predict age
age_result = client.parental_controls.predict_age(
    text="I'm in high school",
    interaction_history=["I have homework"]
)

# Filter content
filter_result = client.parental_controls.filter_content(
    content="Some text to filter",
    age_group="child",
    strict_mode=True
)

# Batch filter
batch_result = client.parental_controls.filter_batch(
    contents=["text1", "text2", "text3"],
    age_group="teen"
)
```

### JavaScript/TypeScript

```typescript
import { AgentGuardClient } from '@agentguard/sdk';

const client = new AgentGuardClient({ apiKey: 'your_api_key' });

// Predict age
const ageResult = await client.parentalControls.predictAge({
  text: "I'm in high school",
  interactionHistory: ["I have homework"]
});

// Filter content
const filterResult = await client.parentalControls.filterContent({
  content: "Some text to filter",
  ageGroup: "child",
  strictMode: true
});
```

### cURL

```bash
# Predict age
curl -X POST https://agentguard-api.onrender.com/parental-controls/predict-age \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key" \
  -d '{
    "text": "I am in high school",
    "interaction_history": ["I have homework"]
  }'

# Filter content
curl -X POST https://agentguard-api.onrender.com/parental-controls/filter-content \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key" \
  -d '{
    "content": "Some text to filter",
    "age_group": "child",
    "strict_mode": true
  }'
```

---

## Best Practices

1. **Age Detection**: Use interaction history for better accuracy
2. **Strict Mode**: Enable for children and educational settings
3. **Crisis Handling**: Always implement crisis intervention workflows
4. **Batch Processing**: Use batch endpoints for efficiency
5. **Caching**: Cache age predictions for known users
6. **Monitoring**: Track blocked content for policy improvements
7. **Transparency**: Inform users about filtering policies
8. **Appeals**: Provide mechanisms for content review

---

## Support

- **Documentation**: [docs.agentguard.ai/parental-controls](https://docs.agentguard.ai/parental-controls)
- **Email**: support@mothership-ai.com
- **GitHub**: [github.com/agentguard/parental-controls](https://github.com/agentguard/parental-controls)
- **Community**: [community.agentguard.ai](https://community.agentguard.ai)

---

## Roadmap

**Q4 2025**:
- Image content filtering
- Audio/video content analysis
- Multi-language support
- Custom risk categories
- Parental dashboard UI

**Q1 2026**:
- AI-powered age verification
- Behavioral analysis
- Screen time recommendations
- Educational content suggestions
- Integration with major LMS platforms

---

*Built with care for families and educators by the AgentGuard team.*  
*Protecting the next generation in the age of AI.*

