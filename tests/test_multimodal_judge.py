"""
Tests for Multimodal Hallucination Detection
Tests ONNX-based image/video hallucination detection capabilities.
"""

import pytest
import asyncio
import os
import io
from unittest.mock import Mock, patch, AsyncMock
from PIL import Image
import numpy as np

from src.judges.multimodal_judge import (
    MultimodalJudge,
    MultimodalInput,
    MultimodalResult,
    BoundingBox,
    get_multimodal_judge
)


@pytest.fixture
def sample_image_bytes():
    """Create sample image bytes for testing."""
    # Create a simple test image
    image = Image.new('RGB', (224, 224), color='red')
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG')
    return buffer.getvalue()


@pytest.fixture
def sample_video_bytes():
    """Create sample video bytes for testing."""
    # Return mock video bytes (in production, use actual video data)
    return b'fake_video_data_for_testing'


@pytest.fixture
def multimodal_judge():
    """Create multimodal judge instance for testing."""
    return MultimodalJudge(device='cpu')


class TestMultimodalJudge:
    """Test suite for MultimodalJudge class."""
    
    def test_judge_initialization(self, multimodal_judge):
        """Test multimodal judge initialization."""
        assert multimodal_judge.device in ['cpu', 'cuda', 'mps']
        assert multimodal_judge.models_dir.exists()
        assert isinstance(multimodal_judge.processing_stats, dict)
        assert 'images_processed' in multimodal_judge.processing_stats
        assert 'videos_processed' in multimodal_judge.processing_stats

    def test_device_setup_auto(self):
        """Test automatic device selection."""
        judge = MultimodalJudge(device='auto')
        assert judge.device in ['cpu', 'cuda', 'mps']

    def test_device_setup_cpu(self):
        """Test CPU device selection."""
        judge = MultimodalJudge(device='cpu')
        assert judge.device == 'cpu'

    def test_ort_providers_setup(self, multimodal_judge):
        """Test ONNX Runtime providers setup."""
        providers = multimodal_judge.ort_providers
        assert isinstance(providers, list)
        assert 'CPUExecutionProvider' in providers

    def test_coco_classes(self, multimodal_judge):
        """Test COCO class names."""
        classes = multimodal_judge._get_coco_classes()
        assert isinstance(classes, list)
        assert len(classes) == 80  # COCO has 80 classes
        assert 'person' in classes
        assert 'car' in classes

    def test_load_image_from_bytes(self, multimodal_judge, sample_image_bytes):
        """Test loading image from bytes."""
        image = multimodal_judge._load_image_from_bytes(sample_image_bytes)
        assert image is not None
        assert isinstance(image, Image.Image)
        assert image.mode == 'RGB'
        assert image.size == (224, 224)

    def test_load_image_from_invalid_bytes(self, multimodal_judge):
        """Test loading image from invalid bytes."""
        invalid_bytes = b'not_an_image'
        image = multimodal_judge._load_image_from_bytes(invalid_bytes)
        assert image is None

    def test_image_to_bytes(self, multimodal_judge):
        """Test converting image to bytes."""
        # Create test image
        image = Image.new('RGB', (100, 100), color='blue')
        image_bytes = multimodal_judge._image_to_bytes(image)
        
        assert isinstance(image_bytes, bytes)
        assert len(image_bytes) > 0
        
        # Verify we can load it back
        loaded_image = multimodal_judge._load_image_from_bytes(image_bytes)
        assert loaded_image is not None
        assert loaded_image.size == (100, 100)

    @pytest.mark.asyncio
    async def test_detect_objects_mock(self, multimodal_judge, sample_image_bytes):
        """Test object detection with mock results."""
        image = multimodal_judge._load_image_from_bytes(sample_image_bytes)
        result = await multimodal_judge._detect_objects(image)
        
        assert isinstance(result, dict)
        assert 'objects' in result
        assert 'confidence' in result
        assert isinstance(result['objects'], list)
        
        # Check mock objects
        if result['objects']:
            obj = result['objects'][0]
            assert isinstance(obj, BoundingBox)
            assert hasattr(obj, 'label')
            assert hasattr(obj, 'confidence')
            assert hasattr(obj, 'x')
            assert hasattr(obj, 'y')

    @pytest.mark.asyncio
    async def test_analyze_scene_consistency(self, multimodal_judge, sample_image_bytes):
        """Test scene consistency analysis."""
        image = multimodal_judge._load_image_from_bytes(sample_image_bytes)
        result = await multimodal_judge._analyze_scene_consistency(image)
        
        assert isinstance(result, dict)
        assert 'consistency_score' in result
        assert 'issues' in result
        assert 0.0 <= result['consistency_score'] <= 1.0
        assert isinstance(result['issues'], list)

    @pytest.mark.asyncio
    async def test_detect_adversarial_content(self, multimodal_judge, sample_image_bytes):
        """Test adversarial content detection."""
        image = multimodal_judge._load_image_from_bytes(sample_image_bytes)
        result = await multimodal_judge._detect_adversarial_content(image)
        
        assert isinstance(result, dict)
        assert 'adversarial_probability' in result
        assert 'confidence' in result
        assert 0.0 <= result['adversarial_probability'] <= 1.0
        assert 0.0 <= result['confidence'] <= 1.0

    @pytest.mark.asyncio
    async def test_compute_text_image_alignment_no_clip(self, multimodal_judge, sample_image_bytes):
        """Test text-image alignment without CLIP model."""
        image = multimodal_judge._load_image_from_bytes(sample_image_bytes)
        text = "A red image"
        
        # Mock CLIP model as None
        multimodal_judge.clip_model = None
        
        alignment = await multimodal_judge._compute_text_image_alignment(image, text)
        assert alignment == 0.5  # Default when CLIP not available

    @pytest.mark.asyncio
    async def test_analyze_temporal_consistency_single_frame(self, multimodal_judge, sample_image_bytes):
        """Test temporal consistency with single frame."""
        image = multimodal_judge._load_image_from_bytes(sample_image_bytes)
        frames = [image]
        
        result = await multimodal_judge._analyze_temporal_consistency(frames)
        
        assert isinstance(result, dict)
        assert 'score' in result
        assert 'inconsistencies' in result
        assert result['score'] == 1.0  # Single frame should be perfectly consistent

    @pytest.mark.asyncio
    async def test_analyze_temporal_consistency_multiple_frames(self, multimodal_judge, sample_image_bytes):
        """Test temporal consistency with multiple frames."""
        image1 = multimodal_judge._load_image_from_bytes(sample_image_bytes)
        image2 = Image.new('RGB', (224, 224), color='blue')  # Different image
        frames = [image1, image2]
        
        result = await multimodal_judge._analyze_temporal_consistency(frames)
        
        assert isinstance(result, dict)
        assert 'score' in result
        assert 'inconsistencies' in result
        assert 'frame_similarities' in result
        assert 0.0 <= result['score'] <= 1.0
        assert isinstance(result['inconsistencies'], list)

    def test_compute_combined_hallucination_score(self, multimodal_judge):
        """Test combined hallucination score computation."""
        object_result = {'confidence': 0.8}
        scene_result = {'consistency_score': 0.7}
        adversarial_result = {'adversarial_probability': 0.2}
        text_alignment = 0.9
        
        score = multimodal_judge._compute_combined_hallucination_score(
            object_result, scene_result, adversarial_result, text_alignment
        )
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_extract_visual_inconsistencies(self, multimodal_judge):
        """Test visual inconsistencies extraction."""
        object_result = {'objects': []}
        scene_result = {'issues': [{'type': 'test_issue', 'severity': 'high'}]}
        adversarial_result = {'adversarial_probability': 0.8, 'confidence': 0.9}
        
        inconsistencies = multimodal_judge._extract_visual_inconsistencies(
            object_result, scene_result, adversarial_result
        )
        
        assert isinstance(inconsistencies, list)
        assert len(inconsistencies) >= 1  # Should have scene issues
        
        # Check for adversarial content issue
        adversarial_issues = [i for i in inconsistencies if i.get('type') == 'adversarial_content']
        assert len(adversarial_issues) == 1

    def test_update_processing_stats(self, multimodal_judge):
        """Test processing statistics update."""
        initial_images = multimodal_judge.processing_stats['images_processed']
        initial_videos = multimodal_judge.processing_stats['videos_processed']
        
        # Update with image processing
        multimodal_judge._update_processing_stats('image', 150.0, 0.8)
        
        assert multimodal_judge.processing_stats['images_processed'] == initial_images + 1
        assert multimodal_judge.processing_stats['videos_processed'] == initial_videos
        assert multimodal_judge.processing_stats['average_latency_ms'] > 0
        assert multimodal_judge.processing_stats['hallucinations_detected'] >= 0

    def test_get_processing_stats(self, multimodal_judge):
        """Test processing statistics retrieval."""
        stats = multimodal_judge.get_processing_stats()
        
        assert isinstance(stats, dict)
        assert 'images_processed' in stats
        assert 'videos_processed' in stats
        assert 'total_processed' in stats
        assert 'hallucination_rate' in stats
        assert 'device' in stats
        assert 'onnx_providers' in stats

    @pytest.mark.asyncio
    async def test_detect_image_hallucination(self, multimodal_judge, sample_image_bytes):
        """Test image hallucination detection."""
        multimodal_input = MultimodalInput(
            content_type='image',
            image_data=sample_image_bytes,
            text_description=None
        )
        
        result = await multimodal_judge.detect_image_hallucination(multimodal_input)
        
        assert isinstance(result, MultimodalResult)
        assert result.content_type == 'image'
        assert 0.0 <= result.hallucination_score <= 1.0
        assert 0.0 <= result.confidence <= 1.0
        assert result.processing_time_ms > 0
        assert isinstance(result.detected_objects, list)
        assert isinstance(result.visual_inconsistencies, list)

    @pytest.mark.asyncio
    async def test_detect_image_hallucination_with_text(self, multimodal_judge, sample_image_bytes):
        """Test image hallucination detection with text description."""
        multimodal_input = MultimodalInput(
            content_type='image_text',
            image_data=sample_image_bytes,
            text_description="A red colored image"
        )
        
        result = await multimodal_judge.detect_image_hallucination(multimodal_input)
        
        assert isinstance(result, MultimodalResult)
        assert result.content_type == 'image_text'
        assert 0.0 <= result.text_image_alignment <= 1.0

    @pytest.mark.asyncio
    async def test_detect_image_hallucination_invalid_data(self, multimodal_judge):
        """Test image hallucination detection with invalid data."""
        multimodal_input = MultimodalInput(
            content_type='image',
            image_data=b'invalid_image_data'
        )
        
        result = await multimodal_judge.detect_image_hallucination(multimodal_input)
        
        assert isinstance(result, MultimodalResult)
        assert result.hallucination_score == 0.5  # Neutral score on error
        assert result.confidence == 0.0
        assert 'error' in result.metadata

    @pytest.mark.asyncio
    async def test_extract_video_frames_mock(self, multimodal_judge):
        """Test video frame extraction with mock data."""
        # Mock video bytes (in production, use actual video)
        video_bytes = b'mock_video_data'
        
        # Mock the frame extraction to avoid file I/O in tests
        with patch.object(multimodal_judge, '_extract_video_frames') as mock_extract:
            # Create mock frames
            mock_frames = [
                Image.new('RGB', (224, 224), color='red'),
                Image.new('RGB', (224, 224), color='blue')
            ]
            mock_extract.return_value = mock_frames
            
            frames = await multimodal_judge._extract_video_frames(video_bytes)
            
            assert len(frames) == 2
            assert all(isinstance(frame, Image.Image) for frame in frames)

    @pytest.mark.asyncio
    async def test_detect_video_hallucination_mock(self, multimodal_judge, sample_video_bytes):
        """Test video hallucination detection with mocked components."""
        multimodal_input = MultimodalInput(
            content_type='video',
            video_data=sample_video_bytes
        )
        
        # Mock frame extraction and image detection
        with patch.object(multimodal_judge, '_extract_video_frames') as mock_extract, \
             patch.object(multimodal_judge, 'detect_image_hallucination') as mock_detect:
            
            # Setup mocks
            mock_frames = [Image.new('RGB', (224, 224), color='red')]
            mock_extract.return_value = mock_frames
            
            mock_image_result = MultimodalResult(
                content_type='image',
                hallucination_score=0.3,
                confidence=0.8,
                detected_objects=[],
                visual_inconsistencies=[],
                text_image_alignment=0.7,
                processing_time_ms=100.0,
                model_used='mock',
                metadata={}
            )
            mock_detect.return_value = mock_image_result
            
            result = await multimodal_judge.detect_video_hallucination(multimodal_input)
            
            assert isinstance(result, MultimodalResult)
            assert result.content_type == 'video'
            assert 0.0 <= result.hallucination_score <= 1.0

    @pytest.mark.asyncio
    async def test_process_multimodal_input_image(self, multimodal_judge, sample_image_bytes):
        """Test main multimodal processing entry point for images."""
        multimodal_input = MultimodalInput(
            content_type='image',
            image_data=sample_image_bytes
        )
        
        result = await multimodal_judge.process_multimodal_input(multimodal_input)
        
        assert isinstance(result, MultimodalResult)
        assert result.content_type == 'image'

    @pytest.mark.asyncio
    async def test_process_multimodal_input_unsupported(self, multimodal_judge):
        """Test multimodal processing with unsupported content type."""
        multimodal_input = MultimodalInput(
            content_type='audio',  # Unsupported
            image_data=b'fake_data'
        )
        
        with pytest.raises(ValueError, match="Unsupported content type"):
            await multimodal_judge.process_multimodal_input(multimodal_input)

    def test_get_multimodal_judge_singleton(self):
        """Test that get_multimodal_judge returns singleton instance."""
        # Clear any existing instance
        import src.judges.multimodal_judge
        src.judges.multimodal_judge._multimodal_judge = None
        
        judge1 = get_multimodal_judge()
        judge2 = get_multimodal_judge()
        
        assert judge1 is judge2  # Should be the same instance


class TestMultimodalInput:
    """Test suite for MultimodalInput dataclass."""
    
    def test_multimodal_input_creation(self):
        """Test MultimodalInput creation and attributes."""
        input_data = MultimodalInput(
            content_type='image',
            image_data=b'fake_image_data',
            text_description='Test description',
            metadata={'test': 'value'}
        )
        
        assert input_data.content_type == 'image'
        assert input_data.image_data == b'fake_image_data'
        assert input_data.text_description == 'Test description'
        assert input_data.metadata == {'test': 'value'}
        assert input_data.video_data is None


class TestBoundingBox:
    """Test suite for BoundingBox dataclass."""
    
    def test_bounding_box_creation(self):
        """Test BoundingBox creation and attributes."""
        bbox = BoundingBox(
            x=100.0,
            y=150.0,
            width=200.0,
            height=100.0,
            confidence=0.85,
            label='person'
        )
        
        assert bbox.x == 100.0
        assert bbox.y == 150.0
        assert bbox.width == 200.0
        assert bbox.height == 100.0
        assert bbox.confidence == 0.85
        assert bbox.label == 'person'


class TestMultimodalResult:
    """Test suite for MultimodalResult dataclass."""
    
    def test_multimodal_result_creation(self):
        """Test MultimodalResult creation and attributes."""
        bbox = BoundingBox(x=0, y=0, width=100, height=100, confidence=0.9, label='test')
        inconsistency = {'type': 'test', 'severity': 'low'}
        
        result = MultimodalResult(
            content_type='image',
            hallucination_score=0.3,
            confidence=0.8,
            detected_objects=[bbox],
            visual_inconsistencies=[inconsistency],
            text_image_alignment=0.7,
            processing_time_ms=150.0,
            model_used='test_model',
            metadata={'test': 'value'}
        )
        
        assert result.content_type == 'image'
        assert result.hallucination_score == 0.3
        assert result.confidence == 0.8
        assert len(result.detected_objects) == 1
        assert len(result.visual_inconsistencies) == 1
        assert result.text_image_alignment == 0.7
        assert result.processing_time_ms == 150.0
        assert result.model_used == 'test_model'
        assert result.metadata == {'test': 'value'}


# Integration tests (require actual models and data)
@pytest.mark.integration
class TestMultimodalJudgeIntegration:
    """Integration tests for MultimodalJudge (require actual models)."""
    
    @pytest.mark.skipif(not os.path.exists("models/multimodal"), reason="Requires multimodal models")
    async def test_real_image_processing(self):
        """Test multimodal judge with real image processing."""
        judge = MultimodalJudge()
        
        # Create a real test image
        test_image = Image.new('RGB', (224, 224), color=(255, 0, 0))
        buffer = io.BytesIO()
        test_image.save(buffer, format='JPEG')
        image_bytes = buffer.getvalue()
        
        multimodal_input = MultimodalInput(
            content_type='image_text',
            image_data=image_bytes,
            text_description="A red colored square image"
        )
        
        result = await judge.process_multimodal_input(multimodal_input)
        
        assert isinstance(result, MultimodalResult)
        assert result.processing_time_ms > 0
        assert 0.0 <= result.hallucination_score <= 1.0
        assert 0.0 <= result.confidence <= 1.0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
