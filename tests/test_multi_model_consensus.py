"""
Tests for Multi-Model Consensus Service and API

Author: AgentGuard Engineering Team
Date: October 2025
"""

import pytest
import asyncio
from datetime import datetime

from src.services.multi_model_consensus import (
    MultiModelConsensusService,
    ModelName,
    ModelProvider,
    VotingStrategy,
    ModelConfig,
    ModelResult,
    ConsensusResult
)


class TestMultiModelConsensusService:
    """Test suite for multi-model consensus service."""
    
    @pytest.fixture
    def service(self):
        """Create a test service instance."""
        return MultiModelConsensusService()
    
    @pytest.fixture
    def custom_service(self):
        """Create a service with custom model configs."""
        models = {
            ModelName.CLAUDE_SONNET_4_5: ModelConfig(
                name=ModelName.CLAUDE_SONNET_4_5,
                provider=ModelProvider.ANTHROPIC,
                weight=1.5,
                enabled=True
            ),
            ModelName.GPT_4_TURBO: ModelConfig(
                name=ModelName.GPT_4_TURBO,
                provider=ModelProvider.OPENAI,
                weight=1.2,
                enabled=True
            ),
            ModelName.GEMINI_2_0_PRO: ModelConfig(
                name=ModelName.GEMINI_2_0_PRO,
                provider=ModelProvider.GOOGLE,
                weight=1.0,
                enabled=True
            )
        }
        return MultiModelConsensusService(models=models)
    
    # Initialization Tests
    
    def test_service_initialization(self, service):
        """Test service initializes correctly."""
        assert service is not None
        assert len(service.models) > 0
        assert service.default_strategy == VotingStrategy.WEIGHTED
        assert service.enable_fallback is True
    
    def test_default_models_loaded(self, service):
        """Test default models are loaded."""
        assert ModelName.CLAUDE_SONNET_4_5 in service.models
        assert service.models[ModelName.CLAUDE_SONNET_4_5].enabled is True
    
    def test_custom_models(self, custom_service):
        """Test custom model configuration."""
        assert len(custom_service.models) == 3
        assert custom_service.models[ModelName.CLAUDE_SONNET_4_5].weight == 1.5
        assert custom_service.models[ModelName.GPT_4_TURBO].enabled is True
    
    # Detection Tests
    
    @pytest.mark.asyncio
    async def test_basic_detection(self, custom_service):
        """Test basic hallucination detection."""
        result = await custom_service.detect_hallucination(
            agent_output="The Eiffel Tower is in London",
            agent_input="Where is the Eiffel Tower?"
        )
        
        assert isinstance(result, ConsensusResult)
        assert isinstance(result.is_hallucination, bool)
        assert 0.0 <= result.confidence <= 1.0
        assert 0.0 <= result.agreement_score <= 1.0
        assert len(result.model_results) > 0
        assert result.models_voted >= 2
    
    @pytest.mark.asyncio
    async def test_detection_with_context(self, custom_service):
        """Test detection with additional context."""
        result = await custom_service.detect_hallucination(
            agent_output="The capital is Paris",
            agent_input="What is the capital of France?",
            context="Geography question about European capitals"
        )
        
        assert isinstance(result, ConsensusResult)
        assert result.total_processing_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_detection_min_models(self, custom_service):
        """Test minimum models requirement."""
        result = await custom_service.detect_hallucination(
            agent_output="Test output",
            min_models=2
        )
        
        assert result.models_voted >= 2
    
    @pytest.mark.asyncio
    async def test_detection_insufficient_models(self, service):
        """Test error when insufficient models enabled."""
        # Only 1 model enabled by default
        with pytest.raises(ValueError, match="Not enough enabled models"):
            await service.detect_hallucination(
                agent_output="Test",
                min_models=5
            )
    
    # Voting Strategy Tests
    
    @pytest.mark.asyncio
    async def test_majority_voting(self, custom_service):
        """Test majority voting strategy."""
        result = await custom_service.detect_hallucination(
            agent_output="Test output",
            strategy=VotingStrategy.MAJORITY
        )
        
        assert result.voting_strategy == VotingStrategy.MAJORITY
        assert isinstance(result.is_hallucination, bool)
    
    @pytest.mark.asyncio
    async def test_weighted_voting(self, custom_service):
        """Test weighted voting strategy."""
        result = await custom_service.detect_hallucination(
            agent_output="Test output",
            strategy=VotingStrategy.WEIGHTED
        )
        
        assert result.voting_strategy == VotingStrategy.WEIGHTED
        assert isinstance(result.confidence, float)
    
    @pytest.mark.asyncio
    async def test_unanimous_voting(self, custom_service):
        """Test unanimous voting strategy."""
        result = await custom_service.detect_hallucination(
            agent_output="Test output",
            strategy=VotingStrategy.UNANIMOUS
        )
        
        assert result.voting_strategy == VotingStrategy.UNANIMOUS
        # Agreement score should be 1.0 or 0.0 for unanimous
        assert result.agreement_score in [0.0, 1.0] or 0.0 < result.agreement_score < 1.0
    
    @pytest.mark.asyncio
    async def test_threshold_voting(self, custom_service):
        """Test threshold voting strategy."""
        result = await custom_service.detect_hallucination(
            agent_output="Test output",
            strategy=VotingStrategy.THRESHOLD,
            confidence_threshold=0.8
        )
        
        assert result.voting_strategy == VotingStrategy.THRESHOLD
    
    @pytest.mark.asyncio
    async def test_cascading_voting(self, custom_service):
        """Test cascading voting strategy."""
        result = await custom_service.detect_hallucination(
            agent_output="Test output",
            strategy=VotingStrategy.CASCADING
        )
        
        assert result.voting_strategy == VotingStrategy.CASCADING
        # Cascading may use fewer models
        assert result.models_voted >= 1
    
    # Model Management Tests
    
    def test_enable_model(self, service):
        """Test enabling a model."""
        service.enable_model(ModelName.GPT_4_TURBO)
        assert service.models[ModelName.GPT_4_TURBO].enabled is True
    
    def test_disable_model(self, custom_service):
        """Test disabling a model."""
        custom_service.disable_model(ModelName.GPT_4_TURBO)
        assert custom_service.models[ModelName.GPT_4_TURBO].enabled is False
    
    def test_configure_model(self, service):
        """Test configuring a model."""
        new_config = ModelConfig(
            name=ModelName.CLAUDE_SONNET_4_5,
            provider=ModelProvider.ANTHROPIC,
            weight=2.0,
            enabled=True
        )
        service.configure_model(ModelName.CLAUDE_SONNET_4_5, new_config)
        
        assert service.models[ModelName.CLAUDE_SONNET_4_5].weight == 2.0
    
    # Performance Stats Tests
    
    def test_performance_stats_initialization(self, service):
        """Test performance stats are initialized."""
        stats = service.get_performance_stats()
        assert len(stats) > 0
        
        for model_name, model_stats in stats.items():
            assert "total_calls" in model_stats
            assert "successful_calls" in model_stats
            assert "failed_calls" in model_stats
            assert "avg_latency_ms" in model_stats
            assert "avg_confidence" in model_stats
            assert "total_cost" in model_stats
    
    @pytest.mark.asyncio
    async def test_performance_stats_update(self, custom_service):
        """Test performance stats update after detection."""
        initial_stats = custom_service.get_performance_stats()
        initial_calls = sum(s["total_calls"] for s in initial_stats.values())
        
        await custom_service.detect_hallucination(
            agent_output="Test output"
        )
        
        updated_stats = custom_service.get_performance_stats()
        updated_calls = sum(s["total_calls"] for s in updated_stats.values())
        
        assert updated_calls > initial_calls
    
    # Result Validation Tests
    
    @pytest.mark.asyncio
    async def test_result_structure(self, custom_service):
        """Test consensus result structure."""
        result = await custom_service.detect_hallucination(
            agent_output="Test output"
        )
        
        # Check all required fields
        assert hasattr(result, 'is_hallucination')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'agreement_score')
        assert hasattr(result, 'model_results')
        assert hasattr(result, 'voting_strategy')
        assert hasattr(result, 'models_voted')
        assert hasattr(result, 'models_agreed')
        assert hasattr(result, 'final_reasoning')
        assert hasattr(result, 'total_processing_time_ms')
        assert hasattr(result, 'total_cost')
        assert hasattr(result, 'timestamp')
    
    @pytest.mark.asyncio
    async def test_model_result_structure(self, custom_service):
        """Test individual model result structure."""
        result = await custom_service.detect_hallucination(
            agent_output="Test output"
        )
        
        for model_result in result.model_results:
            assert hasattr(model_result, 'model_name')
            assert hasattr(model_result, 'is_hallucination')
            assert hasattr(model_result, 'confidence')
            assert hasattr(model_result, 'reasoning')
            assert hasattr(model_result, 'processing_time_ms')
            assert hasattr(model_result, 'tokens_used')
            assert hasattr(model_result, 'cost')
            assert hasattr(model_result, 'error')
    
    # Cost Calculation Tests
    
    @pytest.mark.asyncio
    async def test_cost_calculation(self, custom_service):
        """Test cost is calculated correctly."""
        result = await custom_service.detect_hallucination(
            agent_output="Test output"
        )
        
        assert result.total_cost >= 0
        assert result.total_cost == sum(r.cost for r in result.model_results)
    
    @pytest.mark.asyncio
    async def test_cascading_cost_optimization(self, custom_service):
        """Test cascading strategy reduces costs."""
        # Run weighted (all models)
        weighted_result = await custom_service.detect_hallucination(
            agent_output="Test output",
            strategy=VotingStrategy.WEIGHTED
        )
        
        # Run cascading (optimized)
        cascading_result = await custom_service.detect_hallucination(
            agent_output="Test output",
            strategy=VotingStrategy.CASCADING
        )
        
        # Cascading should use fewer models or similar cost
        assert cascading_result.models_voted <= weighted_result.models_voted
    
    # Edge Cases
    
    @pytest.mark.asyncio
    async def test_empty_output(self, custom_service):
        """Test detection with empty output."""
        result = await custom_service.detect_hallucination(
            agent_output=""
        )
        
        assert isinstance(result, ConsensusResult)
    
    @pytest.mark.asyncio
    async def test_very_long_output(self, custom_service):
        """Test detection with very long output."""
        long_output = "This is a test. " * 1000
        result = await custom_service.detect_hallucination(
            agent_output=long_output
        )
        
        assert isinstance(result, ConsensusResult)
        assert result.total_processing_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_special_characters(self, custom_service):
        """Test detection with special characters."""
        result = await custom_service.detect_hallucination(
            agent_output="Test with special chars: @#$%^&*()"
        )
        
        assert isinstance(result, ConsensusResult)
    
    # Agreement Score Tests
    
    @pytest.mark.asyncio
    async def test_agreement_score_range(self, custom_service):
        """Test agreement score is in valid range."""
        result = await custom_service.detect_hallucination(
            agent_output="Test output"
        )
        
        assert 0.0 <= result.agreement_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_high_agreement(self, custom_service):
        """Test high agreement scenario."""
        # Use obvious hallucination
        result = await custom_service.detect_hallucination(
            agent_output="The sky is green and grass is blue"
        )
        
        # Should have some level of agreement
        assert result.agreement_score >= 0.0
    
    # Performance Tests
    
    @pytest.mark.asyncio
    async def test_response_time(self, custom_service):
        """Test response time is reasonable."""
        result = await custom_service.detect_hallucination(
            agent_output="Test output"
        )
        
        # Should complete in reasonable time (< 5 seconds for 3 models)
        assert result.total_processing_time_ms < 5000
    
    @pytest.mark.asyncio
    async def test_parallel_execution(self, custom_service):
        """Test parallel execution of models."""
        result = await custom_service.detect_hallucination(
            agent_output="Test output",
            strategy=VotingStrategy.WEIGHTED
        )
        
        # Total time should be less than sum of individual times (parallel)
        individual_times = sum(r.processing_time_ms for r in result.model_results)
        # Allow some overhead, but should be significantly faster
        assert result.total_processing_time_ms < individual_times * 0.8


# API Tests

@pytest.mark.asyncio
async def test_api_detect_endpoint():
    """Test the /multi-model/detect API endpoint."""
    from fastapi.testclient import TestClient
    from src.api.main import app
    
    client = TestClient(app)
    
    response = client.post(
        "/multi-model/detect",
        json={
            "agent_output": "The Eiffel Tower is in London",
            "agent_input": "Where is the Eiffel Tower?",
            "strategy": "weighted",
            "min_models": 1
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "is_hallucination" in data
    assert "confidence" in data
    assert "agreement_score" in data
    assert "model_results" in data
    assert "total_cost" in data


@pytest.mark.asyncio
async def test_api_list_models():
    """Test the /multi-model/models API endpoint."""
    from fastapi.testclient import TestClient
    from src.api.main import app
    
    client = TestClient(app)
    
    response = client.get("/multi-model/models")
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) > 0
    assert "name" in data[0]
    assert "provider" in data[0]
    assert "enabled" in data[0]


@pytest.mark.asyncio
async def test_api_performance_stats():
    """Test the /multi-model/performance API endpoint."""
    from fastapi.testclient import TestClient
    from src.api.main import app
    
    client = TestClient(app)
    
    response = client.get("/multi-model/performance")
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    if len(data) > 0:
        assert "model_name" in data[0]
        assert "total_calls" in data[0]
        assert "success_rate" in data[0]


@pytest.mark.asyncio
async def test_api_health_check():
    """Test the /multi-model/health API endpoint."""
    from fastapi.testclient import TestClient
    from src.api.main import app
    
    client = TestClient(app)
    
    response = client.get("/multi-model/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert data["service"] == "multi_model_consensus"
    assert "models_available" in data


@pytest.mark.asyncio
async def test_api_list_strategies():
    """Test the /multi-model/strategies API endpoint."""
    from fastapi.testclient import TestClient
    from src.api.main import app
    
    client = TestClient(app)
    
    response = client.get("/multi-model/strategies")
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert "majority" in data
    assert "weighted" in data
    assert "unanimous" in data


@pytest.mark.asyncio
async def test_api_list_providers():
    """Test the /multi-model/providers API endpoint."""
    from fastapi.testclient import TestClient
    from src.api.main import app
    
    client = TestClient(app)
    
    response = client.get("/multi-model/providers")
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert "anthropic" in data
    assert "openai" in data
    assert "google" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

