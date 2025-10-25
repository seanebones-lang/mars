"""
Multimodal Detection API Endpoints
FastAPI endpoints for multimodal hallucination detection.

Author: AgentGuard Engineering Team
Date: October 2025
Version: 1.0.0
"""

from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from typing import Optional, List
from pydantic import BaseModel
import logging

from src.services.multimodal_judge import (
    get_multimodal_detector,
    MediaContent,
    ModalityType,
    ConsistencyCheckType
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/multimodal", tags=["multimodal"])


class MultimodalDetectionRequest(BaseModel):
    """Request for multimodal detection."""
    text_content: str
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    check_types: Optional[List[str]] = None


class MultimodalDetectionResponse(BaseModel):
    """Response from multimodal detection."""
    is_hallucination: bool
    overall_consistency: float
    risk_level: str
    modalities_checked: List[str]
    consistency_results: List[dict]
    final_explanation: str
    recommendations: List[str]
    processing_time_ms: float


@router.post("/detect", response_model=MultimodalDetectionResponse)
async def detect_multimodal_hallucination(request: MultimodalDetectionRequest):
    """
    Detect hallucinations in multimodal content.
    
    Supports:
    - Image-text consistency
    - Video-description alignment
    - Audio-transcript verification
    - Cross-modal consistency
    
    Returns comprehensive analysis with recommendations.
    """
    try:
        detector = get_multimodal_detector()
        
        # Prepare media content
        media_content = None
        additional_media = []
        
        if request.image_url:
            media_content = MediaContent(
                modality=ModalityType.IMAGE,
                content=request.image_url,
                content_type="image/jpeg",
                source_url=request.image_url
            )
        
        if request.video_url:
            video_content = MediaContent(
                modality=ModalityType.VIDEO,
                content=request.video_url,
                content_type="video/mp4",
                source_url=request.video_url
            )
            if media_content:
                additional_media.append(video_content)
            else:
                media_content = video_content
        
        if request.audio_url:
            audio_content = MediaContent(
                modality=ModalityType.AUDIO,
                content=request.audio_url,
                content_type="audio/wav",
                source_url=request.audio_url
            )
            if media_content:
                additional_media.append(audio_content)
            else:
                media_content = audio_content
        
        # Parse check types if provided
        check_types = None
        if request.check_types:
            check_types = [ConsistencyCheckType(ct) for ct in request.check_types]
        
        # Run detection
        result = await detector.detect_hallucination(
            text_content=request.text_content,
            media_content=media_content,
            additional_media=additional_media if additional_media else None,
            check_types=check_types
        )
        
        # Format response
        return MultimodalDetectionResponse(
            is_hallucination=result.is_hallucination,
            overall_consistency=result.overall_consistency,
            risk_level=result.risk_level.value,
            modalities_checked=[m.value for m in result.modalities_checked],
            consistency_results=[
                {
                    "is_consistent": cr.is_consistent,
                    "consistency_score": cr.consistency_score,
                    "risk_level": cr.risk_level.value,
                    "check_type": cr.check_type.value,
                    "detected_objects": cr.detected_objects,
                    "missing_objects": cr.missing_objects,
                    "hallucinated_objects": cr.hallucinated_objects,
                    "explanation": cr.explanation,
                    "confidence": cr.confidence
                }
                for cr in result.consistency_results
            ],
            final_explanation=result.final_explanation,
            recommendations=result.recommendations,
            processing_time_ms=result.total_processing_time_ms
        )
    
    except Exception as e:
        logger.error(f"Multimodal detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.post("/detect-image")
async def detect_image_text(
    text_description: str = Form(...),
    image: Optional[UploadFile] = File(None)
):
    """
    Detect image-text consistency.
    
    Upload an image and provide a text description to verify consistency.
    """
    try:
        detector = get_multimodal_detector()
        
        media_content = None
        if image:
            # Read image data
            image_data = await image.read()
            media_content = MediaContent(
                modality=ModalityType.IMAGE,
                content=image_data,
                content_type=image.content_type or "image/jpeg"
            )
        
        result = await detector.detect_hallucination(
            text_content=text_description,
            media_content=media_content
        )
        
        # Extract detected objects from consistency results
        detected_objects = []
        if result.consistency_results:
            for cr in result.consistency_results:
                if cr.detected_objects:
                    detected_objects.extend(cr.detected_objects)
        
        # Calculate modality scores
        modality_scores = {}
        modality_scores["text"] = 0.95  # Default text score
        if result.consistency_results:
            for cr in result.consistency_results:
                modality_scores[cr.check_type.value] = cr.consistency_score
        
        # Get cross-modal issues
        cross_modal_issues = []
        if result.consistency_results:
            for cr in result.consistency_results:
                if not cr.is_consistent:
                    cross_modal_issues.append(cr.explanation)
        
        return {
            "is_hallucination": result.is_hallucination,
            "risk_level": result.risk_level.value,
            "confidence": result.consistency_results[0].confidence if result.consistency_results else 0.9,
            "consistency_score": result.overall_consistency,
            "modality_scores": modality_scores,
            "detected_objects": list(set(detected_objects)),
            "cross_modal_issues": cross_modal_issues,
            "recommendations": result.recommendations,
            "processing_time": result.total_processing_time_ms / 1000.0  # Convert to seconds
        }
    
    except Exception as e:
        logger.error(f"Image detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.post("/detect-video")
async def detect_video_text(
    text_description: str = Form(...),
    video: UploadFile = File(...)
):
    """
    Detect video-text consistency.
    
    Upload a video and provide a text description to verify consistency.
    """
    try:
        # Read video data
        video_data = await video.read()
        
        detector = get_multimodal_detector()
        
        media_content = MediaContent(
            modality=ModalityType.VIDEO,
            content=video_data,
            content_type=video.content_type or "video/mp4"
        )
        
        result = await detector.detect_hallucination(
            text_content=text_description,
            media_content=media_content
        )
        
        # Extract detected objects
        detected_objects = []
        if result.consistency_results:
            for cr in result.consistency_results:
                if cr.detected_objects:
                    detected_objects.extend(cr.detected_objects)
        
        # Calculate modality scores
        modality_scores = {"text": 0.95}
        if result.consistency_results:
            for cr in result.consistency_results:
                modality_scores[cr.check_type.value] = cr.consistency_score
        
        # Get cross-modal issues
        cross_modal_issues = []
        if result.consistency_results:
            for cr in result.consistency_results:
                if not cr.is_consistent:
                    cross_modal_issues.append(cr.explanation)
        
        return {
            "is_hallucination": result.is_hallucination,
            "risk_level": result.risk_level.value,
            "confidence": result.consistency_results[0].confidence if result.consistency_results else 0.9,
            "consistency_score": result.overall_consistency,
            "modality_scores": modality_scores,
            "detected_objects": list(set(detected_objects)),
            "cross_modal_issues": cross_modal_issues,
            "recommendations": result.recommendations,
            "processing_time": result.total_processing_time_ms / 1000.0
        }
    
    except Exception as e:
        logger.error(f"Video detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.post("/detect-audio")
async def detect_audio_text(
    text_description: str = Form(...),
    audio: UploadFile = File(...)
):
    """
    Detect audio-text consistency.
    
    Upload an audio file and provide a text description to verify consistency.
    """
    try:
        # Read audio data
        audio_data = await audio.read()
        
        detector = get_multimodal_detector()
        
        media_content = MediaContent(
            modality=ModalityType.AUDIO,
            content=audio_data,
            content_type=audio.content_type or "audio/mp3"
        )
        
        result = await detector.detect_hallucination(
            text_content=text_description,
            media_content=media_content
        )
        
        # Calculate modality scores
        modality_scores = {"text": 0.95}
        if result.consistency_results:
            for cr in result.consistency_results:
                modality_scores[cr.check_type.value] = cr.consistency_score
        
        # Get cross-modal issues
        cross_modal_issues = []
        if result.consistency_results:
            for cr in result.consistency_results:
                if not cr.is_consistent:
                    cross_modal_issues.append(cr.explanation)
        
        return {
            "is_hallucination": result.is_hallucination,
            "risk_level": result.risk_level.value,
            "confidence": result.consistency_results[0].confidence if result.consistency_results else 0.9,
            "consistency_score": result.overall_consistency,
            "modality_scores": modality_scores,
            "detected_objects": [],
            "cross_modal_issues": cross_modal_issues,
            "recommendations": result.recommendations,
            "processing_time": result.total_processing_time_ms / 1000.0
        }
    
    except Exception as e:
        logger.error(f"Audio detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.get("/health")
async def multimodal_health():
    """Health check for multimodal detection service."""
    try:
        detector = get_multimodal_detector()
        return {
            "status": "healthy",
            "service": "multimodal_detection",
            "supported_modalities": ["text", "image", "video", "audio"],
            "clip_enabled": detector.enable_clip,
            "object_detection_enabled": detector.enable_object_detection,
            "scene_understanding_enabled": detector.enable_scene_understanding
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/supported-modalities")
async def get_supported_modalities():
    """Get list of supported modalities."""
    return {
        "modalities": [m.value for m in ModalityType],
        "check_types": [ct.value for ct in ConsistencyCheckType]
    }

