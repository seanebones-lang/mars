"""
Integration tests for Bias Auditing API endpoints
Tests end-to-end functionality including API routing and service integration
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.main import app

client = TestClient(app)


class TestBiasAuditingIntegration:
    """Integration tests for bias auditing endpoints"""

    def test_health_check(self):
        """Test bias auditing health endpoint"""
        response = client.get("/bias/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_bias_types_endpoint(self):
        """Test getting supported bias types"""
        response = client.get("/bias/bias-types")
        assert response.status_code == 200
        data = response.json()
        assert "bias_types" in data
        assert "gender" in data["bias_types"]
        assert "racial" in data["bias_types"]

    def test_audit_neutral_text(self):
        """Test auditing neutral text"""
        response = client.post(
            "/bias/audit",
            json={
                "text": "The software engineer completed the project on time.",
                "context": "Professional description"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "has_bias" in data
        assert "bias_types" in data
        assert "severity" in data
        assert data["has_bias"] is False

    def test_audit_gender_bias(self):
        """Test detection of gender bias"""
        response = client.post(
            "/bias/audit",
            json={
                "text": "The nurse should be caring and nurturing, while the doctor should be assertive and decisive.",
                "context": "Job description"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["has_bias"] is True
        assert "gender" in data["bias_types"]
        assert data["severity"] in ["low", "medium", "high", "critical"]

    def test_audit_racial_bias(self):
        """Test detection of racial bias"""
        response = client.post(
            "/bias/audit",
            json={
                "text": "All Asians are good at math and science.",
                "context": "Educational statement"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["has_bias"] is True
        assert "racial" in data["bias_types"]

    def test_audit_ableist_language(self):
        """Test detection of ableist language"""
        response = client.post(
            "/bias/audit",
            json={
                "text": "That idea is crazy and insane.",
                "context": "Feedback"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["has_bias"] is True
        assert "ableist" in data["bias_types"]

    def test_audit_age_bias(self):
        """Test detection of age bias"""
        response = client.post(
            "/bias/audit",
            json={
                "text": "We need young, energetic people for this startup.",
                "context": "Job posting"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["has_bias"] is True
        assert "age" in data["bias_types"]

    def test_audit_non_inclusive_language(self):
        """Test detection of non-inclusive language"""
        response = client.post(
            "/bias/audit",
            json={
                "text": "Hey guys, let's have a meeting.",
                "context": "Team communication"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["has_bias"] is True
        assert "non_inclusive" in data["bias_types"]

    def test_check_inclusive_language(self):
        """Test inclusive language check endpoint"""
        response = client.post(
            "/bias/check-inclusive-language",
            json={"text": "The chairman will lead the meeting."}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "is_inclusive" in data
        assert "suggestions" in data

    def test_audit_with_specific_types(self):
        """Test auditing with specific bias types"""
        response = client.post(
            "/bias/audit",
            json={
                "text": "Women are naturally better at multitasking.",
                "check_types": ["gender"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "has_bias" in data

    def test_response_structure(self):
        """Test that response has all required fields"""
        response = client.post(
            "/bias/audit",
            json={"text": "Test text for structure validation"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = [
            "has_bias",
            "bias_types",
            "severity",
            "confidence",
            "detected_instances",
            "fairness_score",
            "recommendations",
            "compliance_status",
            "processing_time"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_alternative_suggestions(self):
        """Test that alternative suggestions are provided"""
        response = client.post(
            "/bias/audit",
            json={
                "text": "The policeman arrested the suspect.",
                "context": "News article"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data["has_bias"]:
            assert len(data["detected_instances"]) > 0
            for instance in data["detected_instances"]:
                assert "alternative_suggestion" in instance
                assert len(instance["alternative_suggestion"]) > 0

    def test_fairness_score_calculation(self):
        """Test fairness score is calculated correctly"""
        response = client.post(
            "/bias/audit",
            json={"text": "The software developer wrote clean code."}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "fairness_score" in data
        assert 0.0 <= data["fairness_score"] <= 1.0

    def test_compliance_status(self):
        """Test compliance status reporting"""
        response = client.post(
            "/bias/audit",
            json={"text": "All employees must be treated equally."}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "compliance_status" in data
        assert isinstance(data["compliance_status"], dict)

    def test_empty_text_handling(self):
        """Test handling of empty text"""
        response = client.post(
            "/bias/audit",
            json={"text": ""}
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_very_long_text(self):
        """Test handling of very long text"""
        long_text = "This is a test sentence. " * 1000
        
        response = client.post(
            "/bias/audit",
            json={"text": long_text}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "processing_time" in data

    def test_multiple_bias_types(self):
        """Test detection of multiple bias types in one text"""
        response = client.post(
            "/bias/audit",
            json={
                "text": "Young guys are naturally better at tech jobs than older women.",
                "context": "Hiring discussion"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["has_bias"] is True
        # Should detect multiple types
        assert len(data["bias_types"]) >= 2

    def test_confidence_scores(self):
        """Test that confidence scores are provided"""
        response = client.post(
            "/bias/audit",
            json={"text": "The nurse helped the patient."}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "confidence" in data
        assert 0.0 <= data["confidence"] <= 1.0

    def test_recommendations_provided(self):
        """Test that recommendations are provided"""
        response = client.post(
            "/bias/audit",
            json={
                "text": "The chairman will make the final decision.",
                "context": "Corporate governance"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

