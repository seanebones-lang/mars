"""
Integration tests for Multimodal Detection API endpoints
Tests end-to-end functionality including API routing and service integration
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from io import BytesIO
from PIL import Image
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.main import app

client = TestClient(app)


def create_test_image() -> BytesIO:
    """Create a simple test image"""
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes


class TestMultimodalIntegration:
    """Integration tests for multimodal detection endpoints"""

    def test_health_check(self):
        """Test multimodal health endpoint"""
        response = client.get("/multimodal/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "supported_modalities" in data

    def test_supported_modalities(self):
        """Test getting supported modalities"""
        response = client.get("/multimodal/supported-modalities")
        assert response.status_code == 200
        data = response.json()
        assert "modalities" in data
        assert "image" in data["modalities"]
        assert "video" in data["modalities"]
        assert "audio" in data["modalities"]

    def test_detect_image_text_consistency(self):
        """Test image-text consistency detection"""
        img_bytes = create_test_image()
        
        response = client.post(
            "/multimodal/detect-image",
            data={"text_description": "A red square image"},
            files={"image": ("test.png", img_bytes, "image/png")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "is_hallucination" in data
        assert "consistency_score" in data
        assert "risk_level" in data
        assert data["risk_level"] in ["low", "medium", "high", "critical"]

    def test_detect_image_mismatch(self):
        """Test detection of image-text mismatch"""
        img_bytes = create_test_image()
        
        response = client.post(
            "/multimodal/detect-image",
            data={"text_description": "A blue circle with stars"},
            files={"image": ("test.png", img_bytes, "image/png")}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should detect inconsistency
        assert data["consistency_score"] < 0.9

    def test_detect_without_image(self):
        """Test text-only detection"""
        response = client.post(
            "/multimodal/detect-image",
            data={"text_description": "A description without an image"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "is_hallucination" in data

    def test_detect_video_endpoint(self):
        """Test video detection endpoint"""
        # Create a minimal video file (simulated)
        video_bytes = BytesIO(b"fake_video_data")
        
        response = client.post(
            "/multimodal/detect-video",
            data={"text_description": "A video of a car"},
            files={"video": ("test.mp4", video_bytes, "video/mp4")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "is_hallucination" in data
        assert "consistency_score" in data

    def test_detect_audio_endpoint(self):
        """Test audio detection endpoint"""
        # Create a minimal audio file (simulated)
        audio_bytes = BytesIO(b"fake_audio_data")
        
        response = client.post(
            "/multimodal/detect-audio",
            data={"text_description": "A person speaking"},
            files={"audio": ("test.mp3", audio_bytes, "audio/mp3")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "is_hallucination" in data
        assert "consistency_score" in data

    def test_invalid_file_type(self):
        """Test handling of invalid file types"""
        text_file = BytesIO(b"This is not an image")
        
        response = client.post(
            "/multimodal/detect-image",
            data={"text_description": "Test"},
            files={"image": ("test.txt", text_file, "text/plain")}
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_missing_description(self):
        """Test handling of missing text description"""
        img_bytes = create_test_image()
        
        response = client.post(
            "/multimodal/detect-image",
            files={"image": ("test.png", img_bytes, "image/png")}
        )
        
        # Should require text_description
        assert response.status_code == 422

    def test_large_image_handling(self):
        """Test handling of large images"""
        # Create a larger image
        img = Image.new('RGB', (2000, 2000), color='blue')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        response = client.post(
            "/multimodal/detect-image",
            data={"text_description": "A large blue image"},
            files={"image": ("large.png", img_bytes, "image/png")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "processing_time" in data

    def test_response_structure(self):
        """Test that response has all required fields"""
        img_bytes = create_test_image()
        
        response = client.post(
            "/multimodal/detect-image",
            data={"text_description": "Test image"},
            files={"image": ("test.png", img_bytes, "image/png")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields
        required_fields = [
            "is_hallucination",
            "risk_level",
            "confidence",
            "consistency_score",
            "modality_scores",
            "cross_modal_issues",
            "recommendations",
            "processing_time"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        img_bytes1 = create_test_image()
        img_bytes2 = create_test_image()
        
        # Make concurrent requests
        import concurrent.futures
        
        def make_request(img_bytes, desc):
            return client.post(
                "/multimodal/detect-image",
                data={"text_description": desc},
                files={"image": ("test.png", img_bytes, "image/png")}
            )
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(make_request, img_bytes1, "First image")
            future2 = executor.submit(make_request, img_bytes2, "Second image")
            
            response1 = future1.result()
            response2 = future2.result()
        
        assert response1.status_code == 200
        assert response2.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

