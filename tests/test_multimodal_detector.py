"""
Tests for Multimodal Hallucination Detection
Test suite for multimodal consistency checking.

Author: AgentGuard Engineering Team
Date: October 2025
Version: 1.0.0
"""

import pytest
import asyncio
from src.services.multimodal_judge import (
    MultimodalHallucinationDetector,
    MediaContent,
    ModalityType,
    ConsistencyCheckType,
    RiskLevel
)


class TestMultimodalDetector:
    """Test suite for MultimodalHallucinationDetector."""
    
    @pytest.fixture
    def detector(self):
        """Create detector instance for testing."""
        return MultimodalHallucinationDetector(
            enable_clip=True,
            enable_object_detection=True
        )
    
    @pytest.mark.asyncio
    async def test_text_only_detection(self, detector):
        """Test detection with text only (no media)."""
        result = await detector.detect_hallucination(
            text_content="The sky is blue and the grass is green."
        )
        assert result.is_hallucination is False
        assert result.risk_level == RiskLevel.SAFE
        assert ModalityType.TEXT in result.modalities_checked
    
    @pytest.mark.asyncio
    async def test_image_text_consistency(self, detector):
        """Test image-text consistency checking."""
        image = MediaContent(
            modality=ModalityType.IMAGE,
            content=b"fake_image_data",
            content_type="image/jpeg"
        )
        
        result = await detector.detect_hallucination(
            text_content="A person standing next to a car",
            media_content=image
        )
        
        assert result is not None
        assert ModalityType.IMAGE in result.modalities_checked
        assert any(r.check_type == ConsistencyCheckType.IMAGE_TEXT for r in result.consistency_results)
    
    @pytest.mark.asyncio
    async def test_object_detection_consistency(self, detector):
        """Test object detection consistency."""
        image = MediaContent(
            modality=ModalityType.IMAGE,
            content=b"fake_image_data",
            content_type="image/jpeg"
        )
        
        result = await detector.detect_hallucination(
            text_content="A person and a car are visible in the scene",
            media_content=image
        )
        
        # Should include object detection check
        obj_checks = [r for r in result.consistency_results if r.check_type == ConsistencyCheckType.OBJECT_DETECTION]
        assert len(obj_checks) > 0
    
    @pytest.mark.asyncio
    async def test_video_text_consistency(self, detector):
        """Test video-text consistency checking."""
        video = MediaContent(
            modality=ModalityType.VIDEO,
            content=b"fake_video_data",
            content_type="video/mp4"
        )
        
        result = await detector.detect_hallucination(
            text_content="A person walking down the street",
            media_content=video
        )
        
        assert ModalityType.VIDEO in result.modalities_checked
        assert any(r.check_type == ConsistencyCheckType.VIDEO_TEXT for r in result.consistency_results)
    
    @pytest.mark.asyncio
    async def test_audio_text_consistency(self, detector):
        """Test audio-text consistency checking."""
        audio = MediaContent(
            modality=ModalityType.AUDIO,
            content=b"fake_audio_data",
            content_type="audio/wav"
        )
        
        result = await detector.detect_hallucination(
            text_content="Hello, this is a test message",
            media_content=audio
        )
        
        assert ModalityType.AUDIO in result.modalities_checked
        assert any(r.check_type == ConsistencyCheckType.AUDIO_TEXT for r in result.consistency_results)
    
    @pytest.mark.asyncio
    async def test_cross_modal_consistency(self, detector):
        """Test cross-modal consistency with multiple media."""
        image = MediaContent(
            modality=ModalityType.IMAGE,
            content=b"fake_image_data",
            content_type="image/jpeg"
        )
        
        audio = MediaContent(
            modality=ModalityType.AUDIO,
            content=b"fake_audio_data",
            content_type="audio/wav"
        )
        
        result = await detector.detect_hallucination(
            text_content="A person speaking",
            media_content=image,
            additional_media=[audio]
        )
        
        assert len(result.modalities_checked) >= 3  # TEXT, IMAGE, AUDIO
        assert any(r.check_type == ConsistencyCheckType.CROSS_MODAL for r in result.consistency_results)
    
    @pytest.mark.asyncio
    async def test_consistency_scoring(self, detector):
        """Test consistency score calculation."""
        image = MediaContent(
            modality=ModalityType.IMAGE,
            content=b"fake_image_data",
            content_type="image/jpeg"
        )
        
        result = await detector.detect_hallucination(
            text_content="A scene description",
            media_content=image
        )
        
        assert 0.0 <= result.overall_consistency <= 1.0
        for check in result.consistency_results:
            assert 0.0 <= check.consistency_score <= 1.0
            assert 0.0 <= check.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_risk_level_assignment(self, detector):
        """Test risk level assignment."""
        image = MediaContent(
            modality=ModalityType.IMAGE,
            content=b"fake_image_data",
            content_type="image/jpeg"
        )
        
        result = await detector.detect_hallucination(
            text_content="Test description",
            media_content=image
        )
        
        assert result.risk_level in [RiskLevel.SAFE, RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    @pytest.mark.asyncio
    async def test_recommendations_generation(self, detector):
        """Test that recommendations are generated."""
        image = MediaContent(
            modality=ModalityType.IMAGE,
            content=b"fake_image_data",
            content_type="image/jpeg"
        )
        
        result = await detector.detect_hallucination(
            text_content="Test content",
            media_content=image
        )
        
        assert isinstance(result.recommendations, list)
    
    @pytest.mark.asyncio
    async def test_processing_time(self, detector):
        """Test that processing time is recorded."""
        image = MediaContent(
            modality=ModalityType.IMAGE,
            content=b"fake_image_data",
            content_type="image/jpeg"
        )
        
        result = await detector.detect_hallucination(
            text_content="Test",
            media_content=image
        )
        
        assert result.total_processing_time_ms > 0
        for check in result.consistency_results:
            assert check.processing_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_media_content_hash(self, detector):
        """Test media content hashing."""
        image1 = MediaContent(
            modality=ModalityType.IMAGE,
            content=b"image_data_1",
            content_type="image/jpeg"
        )
        
        image2 = MediaContent(
            modality=ModalityType.IMAGE,
            content=b"image_data_2",
            content_type="image/jpeg"
        )
        
        hash1 = image1.get_hash()
        hash2 = image2.get_hash()
        
        assert hash1 != hash2
        assert len(hash1) == 64  # SHA256 hex length
    
    @pytest.mark.asyncio
    async def test_explanation_generation(self, detector):
        """Test explanation generation."""
        image = MediaContent(
            modality=ModalityType.IMAGE,
            content=b"fake_image_data",
            content_type="image/jpeg"
        )
        
        result = await detector.detect_hallucination(
            text_content="Description",
            media_content=image
        )
        
        assert result.final_explanation is not None
        assert len(result.final_explanation) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

