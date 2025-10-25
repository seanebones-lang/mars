"""
Integration tests for Compliance Reporting API endpoints
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


class TestComplianceIntegration:
    """Integration tests for compliance reporting endpoints"""

    def test_health_check(self):
        """Test compliance health endpoint"""
        response = client.get("/compliance/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_generate_full_compliance_report(self):
        """Test generating full compliance report"""
        response = client.post(
            "/compliance/report",
            json={
                "include_recommendations": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data
        assert "frameworks" in data
        assert data["overall_status"] in ["compliant", "partial", "non_compliant"]

    def test_compliance_report_structure(self):
        """Test structure of compliance report"""
        response = client.post("/compliance/report", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = [
            "overall_status",
            "frameworks",
            "generated_at",
            "next_review_date"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_eu_ai_act_check(self):
        """Test EU AI Act compliance check"""
        response = client.get("/compliance/eu-ai-act-check")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "score" in data
        assert "requirements_met" in data
        assert "total_requirements" in data
        assert "gaps" in data

    def test_nist_rmf_check(self):
        """Test NIST RMF compliance check"""
        response = client.get("/compliance/nist-rmf-check")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "score" in data
        assert 0 <= data["score"] <= 100

    def test_gdpr_check(self):
        """Test GDPR compliance check"""
        response = client.get("/compliance/gdpr-check")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "score" in data
        assert "gaps" in data

    def test_owasp_llm_top10_check(self):
        """Test OWASP LLM Top 10 compliance check"""
        response = client.get("/compliance/owasp-llm-top10-check")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "score" in data
        assert "requirements_met" in data

    def test_framework_status_values(self):
        """Test that framework status values are valid"""
        response = client.post("/compliance/report", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        valid_statuses = ["compliant", "partial", "non_compliant"]
        
        for framework, details in data["frameworks"].items():
            assert details["status"] in valid_statuses

    def test_score_ranges(self):
        """Test that scores are within valid ranges"""
        response = client.post("/compliance/report", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        for framework, details in data["frameworks"].items():
            assert 0 <= details["score"] <= 100

    def test_gaps_and_recommendations(self):
        """Test that gaps and recommendations are provided"""
        response = client.post(
            "/compliance/report",
            json={"include_recommendations": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for framework, details in data["frameworks"].items():
            assert "gaps" in details
            assert "recommendations" in details
            assert isinstance(details["gaps"], list)
            assert isinstance(details["recommendations"], list)

    def test_requirements_tracking(self):
        """Test requirements tracking"""
        response = client.post("/compliance/report", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        for framework, details in data["frameworks"].items():
            assert "requirements_met" in details
            assert "total_requirements" in details
            assert details["requirements_met"] <= details["total_requirements"]

    def test_specific_scope_filtering(self):
        """Test filtering by specific compliance scope"""
        response = client.post(
            "/compliance/report",
            json={"scope": ["EU_AI_ACT", "GDPR"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "frameworks" in data

    def test_timestamp_format(self):
        """Test timestamp format in report"""
        response = client.post("/compliance/report", json={})
        
        assert response.status_code == 200
        data = response.json()
        assert "generated_at" in data
        assert "next_review_date" in data
        
        # Should be valid ISO format strings
        from datetime import datetime
        try:
            datetime.fromisoformat(data["generated_at"].replace('Z', '+00:00'))
            datetime.fromisoformat(data["next_review_date"].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail("Invalid timestamp format")

    def test_overall_status_calculation(self):
        """Test overall status calculation logic"""
        response = client.post("/compliance/report", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        framework_statuses = [details["status"] for details in data["frameworks"].values()]
        
        # If all compliant, overall should be compliant
        if all(s == "compliant" for s in framework_statuses):
            assert data["overall_status"] == "compliant"
        # If any non-compliant, overall should reflect that
        elif any(s == "non_compliant" for s in framework_statuses):
            assert data["overall_status"] in ["partial", "non_compliant"]

    def test_empty_scope(self):
        """Test handling of empty scope"""
        response = client.post(
            "/compliance/report",
            json={"scope": []}
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_invalid_scope(self):
        """Test handling of invalid scope"""
        response = client.post(
            "/compliance/report",
            json={"scope": ["INVALID_FRAMEWORK"]}
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_concurrent_report_generation(self):
        """Test concurrent report generation"""
        import concurrent.futures
        
        def generate_report():
            return client.post("/compliance/report", json={})
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(generate_report) for _ in range(3)]
            responses = [f.result() for f in futures]
        
        for response in responses:
            assert response.status_code == 200

    def test_recommendations_quality(self):
        """Test that recommendations are actionable"""
        response = client.post(
            "/compliance/report",
            json={"include_recommendations": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for framework, details in data["frameworks"].items():
            if len(details["gaps"]) > 0:
                # Should have recommendations if there are gaps
                assert len(details["recommendations"]) > 0

    def test_framework_coverage(self):
        """Test that all major frameworks are covered"""
        response = client.post("/compliance/report", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        expected_frameworks = ["EU_AI_ACT", "NIST_RMF", "GDPR", "OWASP_LLM_TOP10"]
        
        for framework in expected_frameworks:
            assert framework in data["frameworks"]

    def test_individual_framework_endpoints(self):
        """Test all individual framework check endpoints"""
        endpoints = [
            "/compliance/eu-ai-act-check",
            "/compliance/nist-rmf-check",
            "/compliance/gdpr-check",
            "/compliance/owasp-llm-top10-check"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "score" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

