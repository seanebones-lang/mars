import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import numpy as np

from src.judges.claude_judge import ClaudeJudge
from src.judges.statistical_judge import StatisticalJudge
from src.judges.ensemble_judge import EnsembleJudge
from src.models.schemas import AgentTestRequest, ClaudeJudgment


class TestClaudeJudge:
    """Test suite for ClaudeJudge LLM-as-a-Judge implementation."""
    
    @pytest.mark.asyncio
    async def test_claude_judge_initialization(self):
        """Test ClaudeJudge initialization with API key."""
        judge = ClaudeJudge("test_api_key")
        assert judge.model == "claude-sonnet-4-5-20250929"
        assert judge.num_samples == 3
        assert judge.temperature == 0.1
    
    @pytest.mark.asyncio
    async def test_claude_judge_evaluate_mock(self):
        """Test ClaudeJudge evaluation with mocked API response."""
        judge = ClaudeJudge("test_api_key")
        
        # Mock response data
        mock_response_text = '''{"score": 0.85, "explanation": "Mostly accurate", "hallucinated_segments": [], "samples": []}'''
        
        with patch.object(judge.client, 'messages', new_callable=Mock) as mock_messages:
            mock_create = AsyncMock()
            mock_create.return_value = Mock(content=[Mock(text=mock_response_text)])
            mock_messages.create = mock_create
            
            result = await judge.evaluate(
                agent_output="Server rebooted successfully",
                ground_truth="Standard server reboot procedure",
                history=[]
            )
            
            assert isinstance(result, ClaudeJudgment)
            assert 0 <= result.score <= 1
    
    def test_parse_response_with_markdown(self):
        """Test JSON parsing from markdown-wrapped responses."""
        judge = ClaudeJudge("test_api_key")
        
        markdown_response = '''```json
{"score": 0.9, "explanation": "Test", "hallucinated_segments": []}
```'''
        
        parsed = judge._parse_response(markdown_response)
        assert parsed["score"] == 0.9
        assert parsed["explanation"] == "Test"
    
    def test_build_consensus(self):
        """Test consensus building from multiple samples."""
        judge = ClaudeJudge("test_api_key")
        
        samples = [
            {"score": 0.8, "explanation": "Good", "hallucinated_segments": ["test1"]},
            {"score": 0.9, "explanation": "Better", "hallucinated_segments": ["test2"]},
            {"score": 0.85, "explanation": "Good enough", "hallucinated_segments": ["test1"]}
        ]
        
        result = judge._build_consensus(samples)
        assert isinstance(result, ClaudeJudgment)
        assert result.score == 0.85  # Median of [0.8, 0.85, 0.9]
        assert "test1" in result.hallucinated_segments
        assert "test2" in result.hallucinated_segments


class TestStatisticalJudge:
    """Test suite for StatisticalJudge token-level analysis."""
    
    def test_statistical_judge_initialization(self):
        """Test StatisticalJudge initialization."""
        with patch('src.judges.statistical_judge.AutoTokenizer.from_pretrained'), \
             patch('src.judges.statistical_judge.AutoModelForCausalLM.from_pretrained'):
            judge = StatisticalJudge()
            assert judge.device is not None
    
    def test_evaluate_returns_valid_scores(self):
        """Test that evaluate returns scores in valid range."""
        with patch('src.judges.statistical_judge.AutoTokenizer.from_pretrained'), \
             patch('src.judges.statistical_judge.AutoModelForCausalLM.from_pretrained'):
            judge = StatisticalJudge()
            
            # Mock model outputs
            with patch.object(judge.model, '__call__') as mock_call:
                mock_call.return_value = Mock(
                    logits=np.random.randn(1, 10, 100)  # Simplified logits
                )
                
                score, ci = judge.evaluate("Test output")
                
                assert 0 <= score <= 1
                assert len(ci) == 2
                assert ci[0] <= ci[1]
    
    def test_compute_entropy_score(self):
        """Test entropy score computation."""
        with patch('src.judges.statistical_judge.AutoTokenizer.from_pretrained'), \
             patch('src.judges.statistical_judge.AutoModelForCausalLM.from_pretrained'):
            judge = StatisticalJudge()
            
            # Mock logits
            import torch
            logits = torch.randn(1, 10, 100)
            
            score = judge._compute_entropy_score(logits)
            assert 0 <= score <= 1
    
    def test_bootstrap_confidence_interval(self):
        """Test bootstrap confidence interval generation."""
        with patch('src.judges.statistical_judge.AutoTokenizer.from_pretrained'), \
             patch('src.judges.statistical_judge.AutoModelForCausalLM.from_pretrained'):
            judge = StatisticalJudge()
            
            ci = judge._bootstrap_confidence_interval(0.7, 0.8)
            assert len(ci) == 2
            assert 0 <= ci[0] <= 1
            assert 0 <= ci[1] <= 1
            assert ci[0] <= ci[1]


class TestEnsembleJudge:
    """Test suite for EnsembleJudge orchestration."""
    
    @pytest.mark.asyncio
    async def test_ensemble_judge_initialization(self):
        """Test EnsembleJudge initialization."""
        with patch('src.judges.ensemble_judge.ClaudeJudge'), \
             patch('src.judges.ensemble_judge.StatisticalJudge'):
            judge = EnsembleJudge("test_api_key")
            assert judge.claude_weight == 0.6
            assert judge.statistical_weight == 0.4
            assert judge.uncertainty_threshold == 0.3
    
    @pytest.mark.asyncio
    async def test_ensemble_evaluate_integration(self):
        """Test ensemble evaluation with mocked judges."""
        with patch('src.judges.ensemble_judge.ClaudeJudge') as MockClaude, \
             patch('src.judges.ensemble_judge.StatisticalJudge') as MockStat:
            
            # Mock Claude judge
            mock_claude_instance = MockClaude.return_value
            mock_claude_result = ClaudeJudgment(
                score=0.8,
                explanation="Test explanation",
                hallucinated_segments=["test"],
                samples=[]
            )
            mock_claude_instance.evaluate = AsyncMock(return_value=mock_claude_result)
            
            # Mock Statistical judge
            mock_stat_instance = MockStat.return_value
            mock_stat_instance.evaluate.return_value = (0.7, [0.6, 0.8])
            
            # Create ensemble and test
            judge = EnsembleJudge("test_api_key")
            request = AgentTestRequest(
                agent_output="Test output",
                ground_truth="Test truth",
                conversation_history=[]
            )
            
            with patch('mlflow.start_run'), \
                 patch('mlflow.log_param'), \
                 patch('mlflow.log_metric'):
                report = await judge.evaluate(request)
                
                assert 0 <= report.hallucination_risk <= 1
                assert report.uncertainty >= 0
                assert "needs_review" in report.details
    
    def test_compute_uncertainty(self):
        """Test uncertainty computation from confidence interval."""
        with patch('src.judges.ensemble_judge.ClaudeJudge'), \
             patch('src.judges.ensemble_judge.StatisticalJudge'):
            judge = EnsembleJudge("test_api_key")
            
            # Narrow confidence interval -> low uncertainty
            uncertainty_low = judge._compute_uncertainty([0.7, 0.75])
            assert uncertainty_low < 0.2
            
            # Wide confidence interval -> high uncertainty
            uncertainty_high = judge._compute_uncertainty([0.3, 0.9])
            assert uncertainty_high > 0.2
    
    def test_set_weights(self):
        """Test dynamic weight adjustment."""
        with patch('src.judges.ensemble_judge.ClaudeJudge'), \
             patch('src.judges.ensemble_judge.StatisticalJudge'):
            judge = EnsembleJudge("test_api_key")
            
            judge.set_weights(0.7, 0.3)
            assert judge.claude_weight == 0.7
            assert judge.statistical_weight == 0.3
            assert abs(judge.claude_weight + judge.statistical_weight - 1.0) < 1e-6


class TestIntegration:
    """Integration tests for end-to-end workflows."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_evaluation_pipeline(self):
        """Test complete evaluation pipeline (requires API key in environment)."""
        import os
        
        api_key = os.getenv("CLAUDE_API_KEY")
        if not api_key:
            pytest.skip("CLAUDE_API_KEY not set, skipping integration test")
        
        # This test would run actual API calls
        # Commented out to avoid costs during automated testing
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

