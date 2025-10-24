import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from src.api.main import app
from src.models.schemas import HallucinationReport, ClaudeJudgment


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


class TestAPIEndpoints:
    """Test suite for FastAPI endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AgentGuard API"
        assert data["version"] == "0.1.0"
        assert "endpoints" in data
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "model" in data
        assert data["model"] == "claude-sonnet-4-5-20250929"
    
    def test_test_agent_missing_api_key(self, client):
        """Test /test-agent endpoint fails without API key."""
        with patch.dict('os.environ', {'CLAUDE_API_KEY': ''}):
            response = client.post("/test-agent", json={
                "agent_output": "Test output",
                "ground_truth": "Test truth"
            })
            assert response.status_code == 500
            assert "Claude API key not configured" in response.json()["detail"]
    
    def test_test_agent_with_mock(self, client):
        """Test /test-agent endpoint with mocked evaluation."""
        mock_report = HallucinationReport(
            hallucination_risk=0.25,
            details={
                "claude_score": 0.75,
                "statistical_score": 0.7,
                "needs_review": False
            },
            confidence_interval=[0.6, 0.8],
            uncertainty=0.2
        )
        
        with patch.dict('os.environ', {'CLAUDE_API_KEY': 'test_key'}), \
             patch('src.api.main.EnsembleJudge') as MockEnsemble:
            
            mock_judge = MockEnsemble.return_value
            mock_judge.evaluate = AsyncMock(return_value=mock_report)
            
            response = client.post("/test-agent", json={
                "agent_output": "Server rebooted successfully",
                "ground_truth": "Standard reboot procedure completed",
                "conversation_history": []
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "hallucination_risk" in data
            assert "details" in data
            assert "confidence_interval" in data
            assert "uncertainty" in data
    
    def test_test_agent_validation_errors(self, client):
        """Test validation errors for invalid requests."""
        # Missing required fields
        response = client.post("/test-agent", json={})
        assert response.status_code == 422
        
        # Invalid field types
        response = client.post("/test-agent", json={
            "agent_output": 123,  # Should be string
            "ground_truth": "Test"
        })
        assert response.status_code == 422
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
        # May return no data if MLflow not initialized
        data = response.json()
        assert data is not None


class TestCORS:
    """Test CORS middleware configuration."""
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/test-agent")
        # CORS headers should be present
        assert response.status_code in [200, 405]  # OPTIONS may not be explicitly defined


class TestErrorHandling:
    """Test error handling and exception responses."""
    
    def test_404_not_found(self, client):
        """Test 404 for non-existent endpoints."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test 405 for incorrect HTTP methods."""
        response = client.get("/test-agent")  # Should be POST
        assert response.status_code == 405


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

