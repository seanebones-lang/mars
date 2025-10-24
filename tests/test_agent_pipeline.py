"""
Tests for 4-Agent Fact-Checking Pipeline
Tests the Generate → Review → Clarify → Score workflow with CrewAI integration.
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
from src.services.agent_pipeline import (
    AgentPipeline, 
    AgentRole, 
    PipelineStage, 
    AgentOutput, 
    PipelineResult,
    get_agent_pipeline
)


@pytest.fixture
def mock_claude_api_key():
    """Mock Claude API key for testing."""
    return "test_claude_api_key_12345"


@pytest.fixture
def sample_text():
    """Sample text with potential hallucinations for testing."""
    return "Paris is the capital of France and has a population of 50 million people. It was founded in 1889 by Napoleon Bonaparte."


@pytest.fixture
def sample_context():
    """Sample context for testing."""
    return "Geographic and historical information about Paris, France."


class TestAgentPipeline:
    """Test suite for AgentPipeline class."""
    
    def test_pipeline_initialization(self, mock_claude_api_key):
        """Test pipeline initialization with proper configuration."""
        pipeline = AgentPipeline(mock_claude_api_key)
        
        assert pipeline.claude_api_key == mock_claude_api_key
        assert pipeline.model_name == "claude-3-5-sonnet-20241022"
        assert hasattr(pipeline, 'generator_agent')
        assert hasattr(pipeline, 'reviewer_agent')
        assert hasattr(pipeline, 'clarifier_agent')
        assert hasattr(pipeline, 'scorer_agent')
        assert pipeline.pipeline_stats['total_runs'] == 0
    
    def test_pipeline_initialization_custom_model(self, mock_claude_api_key):
        """Test pipeline initialization with custom model."""
        custom_model = "claude-3-opus-20240229"
        pipeline = AgentPipeline(mock_claude_api_key, custom_model)
        
        assert pipeline.model_name == custom_model
    
    @patch('src.services.agent_pipeline.Crew')
    @patch('src.services.agent_pipeline.ChatAnthropic')
    async def test_process_text_success(self, mock_chat_anthropic, mock_crew, mock_claude_api_key, sample_text, sample_context):
        """Test successful text processing through the pipeline."""
        # Mock CrewAI responses
        mock_crew_instance = Mock()
        mock_crew_instance.kickoff.return_value = "Mocked agent response"
        mock_crew.return_value = mock_crew_instance
        
        # Mock LangChain ChatAnthropic
        mock_llm = Mock()
        mock_chat_anthropic.return_value = mock_llm
        
        pipeline = AgentPipeline(mock_claude_api_key)
        
        # Mock the individual agent methods to avoid actual API calls
        with patch.object(pipeline, '_run_generator', new_callable=AsyncMock) as mock_gen, \
             patch.object(pipeline, '_run_reviewer', new_callable=AsyncMock) as mock_rev, \
             patch.object(pipeline, '_run_clarifier', new_callable=AsyncMock) as mock_clar, \
             patch.object(pipeline, '_run_scorer', new_callable=AsyncMock) as mock_scor:
            
            # Setup mock returns
            mock_gen.return_value = AgentOutput(
                agent_role=AgentRole.GENERATOR,
                stage=PipelineStage.GENERATION,
                content="Found potential hallucination: population claim",
                confidence=0.8,
                reasoning="Population figure seems exaggerated",
                metadata={'issues_found': 1},
                processing_time_ms=100.0,
                timestamp="2025-10-24T12:00:00"
            )
            
            mock_rev.return_value = AgentOutput(
                agent_role=AgentRole.REVIEWER,
                stage=PipelineStage.REVIEW,
                content="Confirmed: population and founding date are incorrect",
                confidence=0.85,
                reasoning="Review confirms multiple factual errors",
                metadata={'confirmed_issues': 2},
                processing_time_ms=120.0,
                timestamp="2025-10-24T12:00:01"
            )
            
            mock_clar.return_value = AgentOutput(
                agent_role=AgentRole.CLARIFIER,
                stage=PipelineStage.CLARIFICATION,
                content="Corrected text: Paris is the capital of France and has a population of approximately 2.1 million people in the city proper.",
                confidence=0.9,
                reasoning="Provided accurate population figure",
                metadata={'corrections_made': True},
                processing_time_ms=150.0,
                timestamp="2025-10-24T12:00:02"
            )
            
            mock_scor.return_value = AgentOutput(
                agent_role=AgentRole.SCORER,
                stage=PipelineStage.SCORING,
                content="Final score: 0.7 - High likelihood of hallucination in original text",
                confidence=0.95,
                reasoning="Multiple factual errors confirmed",
                metadata={'final_assessment': True},
                processing_time_ms=80.0,
                timestamp="2025-10-24T12:00:03"
            )
            
            # Run the pipeline
            result = await pipeline.process_text(sample_text, sample_context, "geography")
            
            # Verify result structure
            assert isinstance(result, PipelineResult)
            assert result.original_text == sample_text
            assert result.correction_applied is True
            assert 0.0 <= result.hallucination_score <= 1.0
            assert 0.0 <= result.pipeline_confidence <= 1.0
            assert len(result.agent_outputs) == 4
            assert result.total_processing_time_ms > 0
            
            # Verify all agents were called
            mock_gen.assert_called_once()
            mock_rev.assert_called_once()
            mock_clar.assert_called_once()
            mock_scor.assert_called_once()
    
    async def test_process_text_with_error(self, mock_claude_api_key, sample_text):
        """Test pipeline behavior when an error occurs."""
        pipeline = AgentPipeline(mock_claude_api_key)
        
        # Mock an error in the generator
        with patch.object(pipeline, '_run_generator', side_effect=Exception("Test error")):
            result = await pipeline.process_text(sample_text)
            
            # Should return error result
            assert isinstance(result, PipelineResult)
            assert result.original_text == sample_text
            assert result.corrected_text == sample_text  # No correction on error
            assert result.correction_applied is False
            assert result.hallucination_score == 0.5  # Neutral score
            assert 'error' in result.improvement_metrics
    
    def test_extract_corrected_text(self, mock_claude_api_key):
        """Test corrected text extraction from clarifier output."""
        pipeline = AgentPipeline(mock_claude_api_key)
        
        # Test with clear correction pattern
        clarifier_output = AgentOutput(
            agent_role=AgentRole.CLARIFIER,
            stage=PipelineStage.CLARIFICATION,
            content="Corrected text: This is the corrected version of the text.",
            confidence=0.9,
            reasoning="Test",
            metadata={},
            processing_time_ms=100.0,
            timestamp="2025-10-24T12:00:00"
        )
        
        original_text = "This is the original text."
        corrected = pipeline._extract_corrected_text(clarifier_output, original_text)
        
        assert "corrected version" in corrected.lower()
        assert corrected != original_text
    
    def test_extract_corrected_text_no_pattern(self, mock_claude_api_key):
        """Test corrected text extraction when no clear pattern exists."""
        pipeline = AgentPipeline(mock_claude_api_key)
        
        clarifier_output = AgentOutput(
            agent_role=AgentRole.CLARIFIER,
            stage=PipelineStage.CLARIFICATION,
            content="No clear correction pattern in this output.",
            confidence=0.9,
            reasoning="Test",
            metadata={},
            processing_time_ms=100.0,
            timestamp="2025-10-24T12:00:00"
        )
        
        original_text = "This is the original text."
        corrected = pipeline._extract_corrected_text(clarifier_output, original_text)
        
        # Should return original text when no pattern found
        assert corrected == original_text
    
    def test_extract_hallucination_score(self, mock_claude_api_key):
        """Test hallucination score extraction from scorer output."""
        pipeline = AgentPipeline(mock_claude_api_key)
        
        scorer_output = AgentOutput(
            agent_role=AgentRole.SCORER,
            stage=PipelineStage.SCORING,
            content="Final hallucination score: 0.75 based on analysis",
            confidence=0.95,
            reasoning="Test",
            metadata={},
            processing_time_ms=100.0,
            timestamp="2025-10-24T12:00:00"
        )
        
        score = pipeline._extract_hallucination_score(scorer_output)
        
        assert score == 0.75
        assert 0.0 <= score <= 1.0
    
    def test_extract_hallucination_score_no_pattern(self, mock_claude_api_key):
        """Test hallucination score extraction when no clear pattern exists."""
        pipeline = AgentPipeline(mock_claude_api_key)
        
        scorer_output = AgentOutput(
            agent_role=AgentRole.SCORER,
            stage=PipelineStage.SCORING,
            content="No clear score pattern in this output.",
            confidence=0.95,
            reasoning="Test",
            metadata={},
            processing_time_ms=100.0,
            timestamp="2025-10-24T12:00:00"
        )
        
        score = pipeline._extract_hallucination_score(scorer_output)
        
        # Should return default score when no pattern found
        assert score == 0.5
    
    def test_calculate_pipeline_confidence(self, mock_claude_api_key):
        """Test pipeline confidence calculation."""
        pipeline = AgentPipeline(mock_claude_api_key)
        
        agent_outputs = [
            AgentOutput(AgentRole.GENERATOR, PipelineStage.GENERATION, "test", 0.8, "test", {}, 100.0, "2025-10-24T12:00:00"),
            AgentOutput(AgentRole.REVIEWER, PipelineStage.REVIEW, "test", 0.9, "test", {}, 100.0, "2025-10-24T12:00:01"),
            AgentOutput(AgentRole.CLARIFIER, PipelineStage.CLARIFICATION, "test", 0.7, "test", {}, 100.0, "2025-10-24T12:00:02"),
            AgentOutput(AgentRole.SCORER, PipelineStage.SCORING, "test", 0.95, "test", {}, 100.0, "2025-10-24T12:00:03")
        ]
        
        confidence = pipeline._calculate_pipeline_confidence(agent_outputs)
        
        expected_confidence = (0.8 + 0.9 + 0.7 + 0.95) / 4
        assert confidence == expected_confidence
        assert 0.0 <= confidence <= 1.0
    
    def test_calculate_pipeline_confidence_empty(self, mock_claude_api_key):
        """Test pipeline confidence calculation with empty outputs."""
        pipeline = AgentPipeline(mock_claude_api_key)
        
        confidence = pipeline._calculate_pipeline_confidence([])
        assert confidence == 0.0
    
    def test_calculate_improvement_metrics(self, mock_claude_api_key):
        """Test improvement metrics calculation."""
        pipeline = AgentPipeline(mock_claude_api_key)
        
        original_text = "Original text with errors."
        corrected_text = "Corrected text without errors."
        
        agent_outputs = [
            AgentOutput(AgentRole.CLARIFIER, PipelineStage.CLARIFICATION, "test", 0.9, "test", {}, 100.0, "2025-10-24T12:00:00")
        ]
        
        metrics = pipeline._calculate_improvement_metrics(original_text, corrected_text, agent_outputs)
        
        assert 'text_similarity' in metrics
        assert 'correction_confidence' in metrics
        assert 'processing_efficiency' in metrics
        assert 'agent_consensus' in metrics
        
        # All metrics should be between 0 and 1
        for metric_value in metrics.values():
            assert 0.0 <= metric_value <= 1.0
    
    def test_update_pipeline_stats(self, mock_claude_api_key):
        """Test pipeline statistics update."""
        pipeline = AgentPipeline(mock_claude_api_key)
        
        initial_runs = pipeline.pipeline_stats['total_runs']
        
        # Update stats
        pipeline._update_pipeline_stats(1000.0, {'correction_confidence': 0.8})
        
        assert pipeline.pipeline_stats['total_runs'] == initial_runs + 1
        assert pipeline.pipeline_stats['average_latency_ms'] > 0
        assert pipeline.pipeline_stats['average_improvement'] > 0
    
    def test_get_pipeline_stats(self, mock_claude_api_key):
        """Test pipeline statistics retrieval."""
        pipeline = AgentPipeline(mock_claude_api_key)
        
        # Add some mock stats
        pipeline.pipeline_stats['total_runs'] = 10
        pipeline.pipeline_stats['successful_corrections'] = 8
        
        stats = pipeline.get_pipeline_stats()
        
        assert 'total_runs' in stats
        assert 'successful_corrections' in stats
        assert 'success_rate' in stats
        assert stats['success_rate'] == 0.8  # 8/10
    
    def test_get_agent_pipeline_singleton(self, mock_claude_api_key):
        """Test that get_agent_pipeline returns singleton instance."""
        # Clear any existing instance
        import src.services.agent_pipeline
        src.services.agent_pipeline._agent_pipeline = None
        
        pipeline1 = get_agent_pipeline(mock_claude_api_key)
        pipeline2 = get_agent_pipeline(mock_claude_api_key)
        
        assert pipeline1 is pipeline2  # Should be the same instance


class TestAgentOutput:
    """Test suite for AgentOutput dataclass."""
    
    def test_agent_output_creation(self):
        """Test AgentOutput creation and attributes."""
        output = AgentOutput(
            agent_role=AgentRole.GENERATOR,
            stage=PipelineStage.GENERATION,
            content="Test content",
            confidence=0.8,
            reasoning="Test reasoning",
            metadata={'test': 'value'},
            processing_time_ms=100.0,
            timestamp="2025-10-24T12:00:00"
        )
        
        assert output.agent_role == AgentRole.GENERATOR
        assert output.stage == PipelineStage.GENERATION
        assert output.content == "Test content"
        assert output.confidence == 0.8
        assert output.reasoning == "Test reasoning"
        assert output.metadata == {'test': 'value'}
        assert output.processing_time_ms == 100.0
        assert output.timestamp == "2025-10-24T12:00:00"


class TestPipelineResult:
    """Test suite for PipelineResult dataclass."""
    
    def test_pipeline_result_creation(self):
        """Test PipelineResult creation and attributes."""
        agent_outputs = [
            AgentOutput(AgentRole.GENERATOR, PipelineStage.GENERATION, "test", 0.8, "test", {}, 100.0, "2025-10-24T12:00:00")
        ]
        
        result = PipelineResult(
            original_text="Original text",
            corrected_text="Corrected text",
            hallucination_score=0.7,
            correction_applied=True,
            agent_outputs=agent_outputs,
            total_processing_time_ms=500.0,
            pipeline_confidence=0.85,
            improvement_metrics={'test_metric': 0.9}
        )
        
        assert result.original_text == "Original text"
        assert result.corrected_text == "Corrected text"
        assert result.hallucination_score == 0.7
        assert result.correction_applied is True
        assert len(result.agent_outputs) == 1
        assert result.total_processing_time_ms == 500.0
        assert result.pipeline_confidence == 0.85
        assert result.improvement_metrics == {'test_metric': 0.9}


# Integration tests (require actual API key)
@pytest.mark.integration
class TestAgentPipelineIntegration:
    """Integration tests for AgentPipeline (require real API key)."""
    
    @pytest.mark.skipif(not os.getenv("CLAUDE_API_KEY"), reason="Requires CLAUDE_API_KEY environment variable")
    async def test_real_pipeline_processing(self):
        """Test pipeline with real Claude API (integration test)."""
        api_key = os.getenv("CLAUDE_API_KEY")
        pipeline = AgentPipeline(api_key)
        
        test_text = "The Eiffel Tower is 500 meters tall and was built in 1889."
        
        result = await pipeline.process_text(test_text, domain="architecture")
        
        assert isinstance(result, PipelineResult)
        assert result.original_text == test_text
        assert len(result.agent_outputs) == 4
        assert all(output.processing_time_ms > 0 for output in result.agent_outputs)
        assert 0.0 <= result.hallucination_score <= 1.0
        assert 0.0 <= result.pipeline_confidence <= 1.0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
