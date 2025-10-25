# Multimodal Hallucination Detection Guide

## Overview

AgentGuard's Multimodal Hallucination Detection provides cross-modal consistency checking across text, images, video, and audio to detect hallucinations and inconsistencies in AI-generated multimodal content.

## Features

- **Image-Text Consistency**: Verify that text descriptions match image content
- **Video-Text Consistency**: Validate video content against textual descriptions
- **Audio-Text Consistency**: Check audio transcriptions and descriptions
- **Object Detection**: Identify objects in images and videos
- **Cross-Modal Analysis**: Detect inconsistencies across multiple modalities
- **Risk Assessment**: Comprehensive risk scoring and recommendations

## Quick Start

### Python SDK

```python
from agentguard_sdk import AgentGuardClient

client = AgentGuardClient(api_key="your_api_key")

# Image-text consistency check
with open("image.jpg", "rb") as f:
    result = client.multimodal_detection(
        text_description="A red car on a highway",
        image=f.read(),
        check_consistency=True
    )

print(f"Hallucination detected: {result.is_hallucination}")
print(f"Consistency score: {result.consistency_score}")
print(f"Risk level: {result.risk_level}")
```

### JavaScript/TypeScript SDK

```typescript
import { AgentGuardClient } from '@agentguard/sdk';
import fs from 'fs';

const client = new AgentGuardClient({ apiKey: 'your_api_key' });

const imageBuffer = fs.readFileSync('image.jpg');

const result = await client.detectMultimodal({
  text_description: 'A red car on a highway',
  image: imageBuffer,
  check_consistency: true
});

console.log('Hallucination:', result.is_hallucination);
console.log('Consistency:', result.consistency_score);
```

### REST API

```bash
curl -X POST https://api.agentguard.io/multimodal/detect-image \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "text_description=A red car on a highway" \
  -F "image=@image.jpg"
```

## Use Cases

### 1. Image Captioning Validation

Validate that AI-generated captions accurately describe images:

```python
result = client.multimodal_detection(
    text_description="A golden retriever playing in a park",
    image=image_data
)

if result.is_hallucination:
    print("Caption does not match image content")
    print(f"Issues: {result.cross_modal_issues}")
```

### 2. Video Content Verification

Check video descriptions for accuracy:

```python
result = client.multimodal_detection(
    text_description="A tutorial on cooking pasta",
    video=video_data
)

if result.consistency_score < 0.8:
    print("Video content may not match description")
```

### 3. Audio Transcription Validation

Verify audio transcriptions:

```python
result = client.multimodal_detection(
    text_description="Speaker discussing climate change",
    audio=audio_data
)
```

### 4. Object Detection in Images

Identify objects and verify presence:

```python
result = client.multimodal_detection(
    text_description="A cat sitting on a couch",
    image=image_data
)

print(f"Detected objects: {result.detected_objects}")
```

## API Reference

### Detect Image-Text Consistency

**Endpoint**: `POST /multimodal/detect-image`

**Request**:
```json
{
  "text_description": "string",
  "check_consistency": true
}
```

**Form Data**:
- `image`: Image file (JPEG, PNG, GIF, WebP)

**Response**:
```json
{
  "is_hallucination": false,
  "risk_level": "low",
  "confidence": 0.92,
  "consistency_score": 0.88,
  "modality_scores": {
    "text": 0.95,
    "image": 0.90
  },
  "detected_objects": ["car", "highway", "sky"],
  "cross_modal_issues": [],
  "recommendations": [
    "Content is consistent across modalities"
  ],
  "processing_time": 1.23
}
```

### Detect Video-Text Consistency

**Endpoint**: `POST /multimodal/detect-video`

**Request**:
```json
{
  "text_description": "string"
}
```

**Form Data**:
- `video`: Video file (MP4, AVI, MOV)

**Response**: Same structure as image detection

### Detect Audio-Text Consistency

**Endpoint**: `POST /multimodal/detect-audio`

**Request**:
```json
{
  "text_description": "string"
}
```

**Form Data**:
- `audio`: Audio file (MP3, WAV, OGG)

**Response**: Same structure as image detection

### Get Supported Modalities

**Endpoint**: `GET /multimodal/supported-modalities`

**Response**:
```json
{
  "modalities": ["text", "image", "video", "audio"],
  "image_formats": ["JPEG", "PNG", "GIF", "WebP"],
  "video_formats": ["MP4", "AVI", "MOV"],
  "audio_formats": ["MP3", "WAV", "OGG"]
}
```

## Risk Levels

- **LOW**: Content is highly consistent (score > 0.85)
- **MEDIUM**: Minor inconsistencies detected (score 0.70-0.85)
- **HIGH**: Significant inconsistencies (score 0.50-0.70)
- **CRITICAL**: Major hallucinations detected (score < 0.50)

## Best Practices

### 1. Provide Clear Descriptions

```python
# Good
text_description = "A red sedan car driving on a four-lane highway during daytime"

# Less effective
text_description = "A car"
```

### 2. Use High-Quality Media

- Images: Minimum 640x480 resolution
- Videos: Minimum 720p resolution
- Audio: Minimum 128 kbps bitrate

### 3. Enable Consistency Checking

```python
result = client.multimodal_detection(
    text_description=description,
    image=image_data,
    check_consistency=True  # Enable cross-modal analysis
)
```

### 4. Handle Results Appropriately

```python
if result.risk_level in ["high", "critical"]:
    # Flag for human review
    send_for_review(result)
elif result.risk_level == "medium":
    # Log warning
    logger.warning(f"Moderate inconsistency: {result.cross_modal_issues}")
else:
    # Content is safe
    approve_content(result)
```

## Advanced Configuration

### Custom Thresholds

```python
# Set custom consistency threshold
if result.consistency_score < 0.75:
    # Custom handling
    handle_inconsistency(result)
```

### Batch Processing

```python
images = load_images_from_directory("./images")
descriptions = load_descriptions("descriptions.json")

results = []
for img, desc in zip(images, descriptions):
    result = client.multimodal_detection(
        text_description=desc,
        image=img
    )
    results.append(result)

# Analyze batch results
high_risk = [r for r in results if r.risk_level in ["high", "critical"]]
print(f"High-risk detections: {len(high_risk)}")
```

### Integration with Content Pipelines

```python
def validate_generated_content(text, image):
    """Validate AI-generated multimodal content"""
    result = client.multimodal_detection(
        text_description=text,
        image=image
    )
    
    if result.is_hallucination:
        # Regenerate content
        return regenerate_content()
    
    return {"text": text, "image": image, "validated": True}
```

## Performance Optimization

### 1. Image Preprocessing

```python
from PIL import Image
import io

def optimize_image(image_path, max_size=(1920, 1080)):
    """Optimize image before sending"""
    img = Image.open(image_path)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    return buffer.getvalue()

# Use optimized image
optimized = optimize_image("large_image.jpg")
result = client.multimodal_detection(
    text_description="Description",
    image=optimized
)
```

### 2. Async Processing

```python
import asyncio

async def process_multiple_images(items):
    """Process multiple images concurrently"""
    tasks = [
        client.multimodal_detection_async(
            text_description=item['text'],
            image=item['image']
        )
        for item in items
    ]
    return await asyncio.gather(*tasks)
```

## Error Handling

```python
from agentguard_sdk import AgentGuardError

try:
    result = client.multimodal_detection(
        text_description="A cat",
        image=image_data
    )
except AgentGuardError as e:
    if e.statusCode == 413:
        print("File too large, please resize")
    elif e.statusCode == 415:
        print("Unsupported file format")
    else:
        print(f"Error: {e.message}")
```

## Compliance and Privacy

### GDPR Compliance

- All uploaded media is processed in-memory
- No media files are stored permanently
- Metadata is retained for 30 days for audit purposes

### Data Security

- All API calls use TLS 1.3 encryption
- Media files are deleted immediately after processing
- No third-party sharing of uploaded content

## Limitations

- **File Size**: Maximum 50MB per file
- **Processing Time**: 2-10 seconds depending on file size
- **Supported Formats**: JPEG, PNG, GIF, WebP (images); MP4, AVI, MOV (video); MP3, WAV, OGG (audio)
- **Rate Limits**: 100 requests per minute per API key

## Troubleshooting

### Low Consistency Scores

If you're getting unexpectedly low scores:

1. **Check Image Quality**: Ensure images are clear and well-lit
2. **Verify Descriptions**: Make descriptions specific and detailed
3. **Review Detected Objects**: Check if expected objects are detected
4. **Consider Context**: Some abstract or artistic content may score lower

### Timeout Errors

For large files:

1. Resize images to < 2000x2000 pixels
2. Compress videos to < 100MB
3. Use async processing for batch operations

## Support

- Documentation: https://docs.agentguard.io/multimodal
- API Reference: https://api.agentguard.io/docs
- Support: support@agentguard.io

