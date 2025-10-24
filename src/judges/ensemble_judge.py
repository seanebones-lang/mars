import logging
from typing import Dict
import mlflow

from .claude_judge import ClaudeJudge
from .statistical_judge import StatisticalJudge
from ..models.schemas import AgentTestRequest, HallucinationReport

logger = logging.getLogger(__name__)


class EnsembleJudge:
    """
    Ensemble hallucination detection combining Claude LLM-as-a-Judge
    with statistical token-level analysis. Implements adaptive weighting
    (60% Claude + 40% statistical) with uncertainty thresholding.
    
    Target accuracy: 92%+ via multi-stage verification per SemEval-2025 metrics.
    """
    
    def __init__(self, claude_api_key: str, model_name: str = "distilbert-base-uncased"):
        """
        Initialize ensemble with both judges.
        
        Args:
            claude_api_key: API key for Claude Sonnet 4.5
            model_name: Statistical model name (default: distilbert)
        """
        self.claude_judge = ClaudeJudge(claude_api_key)
        self.statistical_judge = StatisticalJudge(model_name)
        
        # Adaptive weighting (tunable via MLflow experiments)
        self.claude_weight = 0.6
        self.statistical_weight = 0.4
        
        # Uncertainty threshold for human review escalation
        self.uncertainty_threshold = 0.3
        
        logger.info(
            f"Initialized EnsembleJudge with weights: "
            f"Claude={self.claude_weight}, Statistical={self.statistical_weight}"
        )

    async def evaluate(self, request: AgentTestRequest) -> HallucinationReport:
        """
        Perform ensemble hallucination detection on agent output.
        
        Args:
            request: Test request containing agent output, ground truth, and history
            
        Returns:
            Comprehensive hallucination report with risk score and confidence metrics
        """
        with mlflow.start_run():
            # Log request metadata
            mlflow.log_param("agent_output_length", len(request.agent_output))
            mlflow.log_param("has_ground_truth", bool(request.ground_truth))
            mlflow.log_param("conversation_turns", len(request.conversation_history))
            
            # Run both judges in parallel
            logger.info("Starting parallel evaluation with Claude and Statistical judges")
            
            # Claude evaluation (async)
            claude_task = self.claude_judge.evaluate(
                request.agent_output,
                request.ground_truth,
                request.conversation_history
            )
            
            # Statistical evaluation (synchronous, but fast)
            stat_score, stat_ci = self.statistical_judge.evaluate(request.agent_output)
            
            # Await Claude results
            claude_result = await claude_task
            
            # Log individual scores
            mlflow.log_metric("claude_score", claude_result.score)
            mlflow.log_metric("statistical_score", stat_score)
            
            # Adaptive weighting: Trust Claude more when it's very confident
            # (score near 0 or 1 indicates high confidence)
            claude_confidence = abs(claude_result.score - 0.5) * 2  # 0-1 scale
            
            if claude_confidence > 0.7:
                # Claude is very confident - increase its weight
                adaptive_claude_weight = 0.85
                adaptive_stat_weight = 0.15
                mlflow.log_param("weighting_mode", "claude_confident")
            else:
                # Normal weighting for uncertain cases
                adaptive_claude_weight = self.claude_weight
                adaptive_stat_weight = self.statistical_weight
                mlflow.log_param("weighting_mode", "balanced")
            
            # Ensemble scoring with adaptive weighting
            final_score = (
                adaptive_claude_weight * claude_result.score +
                adaptive_stat_weight * stat_score
            )
            mlflow.log_metric("ensemble_score", final_score)
            mlflow.log_metric("claude_confidence", claude_confidence)
            mlflow.log_metric("adaptive_claude_weight", adaptive_claude_weight)
            
            # Compute uncertainty from confidence interval width
            uncertainty = self._compute_uncertainty(stat_ci)
            mlflow.log_metric("uncertainty", uncertainty)
            
            # Build comprehensive report
            report = self._build_report(
                claude_result,
                stat_score,
                stat_ci,
                final_score,
                uncertainty
            )
            
            logger.info(
                f"Ensemble evaluation complete: "
                f"Risk={report.hallucination_risk:.3f}, "
                f"Uncertainty={report.uncertainty:.3f}, "
                f"Review={'Yes' if report.details['needs_review'] else 'No'}"
            )
            
            return report

    def _compute_uncertainty(self, confidence_interval: list) -> float:
        """
        Compute uncertainty metric from confidence interval.
        
        Args:
            confidence_interval: [lower_bound, upper_bound]
            
        Returns:
            Uncertainty score (0-1), higher = more uncertain
        """
        # Interval width as uncertainty proxy
        interval_width = abs(confidence_interval[1] - confidence_interval[0])
        
        # Normalize and ensure minimum threshold
        uncertainty = max(interval_width / 2, 0.1)
        
        return float(min(uncertainty, 1.0))

    def _build_report(
        self,
        claude_result,
        stat_score: float,
        stat_ci: list,
        final_score: float,
        uncertainty: float
    ) -> HallucinationReport:
        """
        Build comprehensive hallucination report from ensemble results.
        
        Args:
            claude_result: ClaudeJudgment object
            stat_score: Statistical judge score
            stat_ci: Statistical confidence interval
            final_score: Ensemble final score
            uncertainty: Computed uncertainty metric
            
        Returns:
            HallucinationReport with all metrics and flagging
        """
        # Convert hallucination risk (invert score: high score = accurate, low risk)
        hallucination_risk = 1 - final_score
        
        # Flag for human review if uncertainty exceeds threshold
        needs_review = uncertainty > self.uncertainty_threshold
        
        # Build detailed results dictionary
        details = {
            "claude_score": claude_result.score,
            "claude_explanation": claude_result.explanation,
            "hallucinated_segments": claude_result.hallucinated_segments,
            "claude_samples": claude_result.samples,
            "statistical_score": stat_score,
            "needs_review": needs_review,
            "ensemble_weights": {
                "claude": self.claude_weight,
                "statistical": self.statistical_weight
            }
        }
        
        return HallucinationReport(
            hallucination_risk=hallucination_risk,
            details=details,
            confidence_interval=stat_ci,
            uncertainty=uncertainty
        )

    def set_weights(self, claude_weight: float, statistical_weight: float):
        """
        Adjust ensemble weights for experimentation via MLflow.
        
        Args:
            claude_weight: Weight for Claude judge (0-1)
            statistical_weight: Weight for statistical judge (0-1)
        """
        # Normalize weights to sum to 1
        total = claude_weight + statistical_weight
        self.claude_weight = claude_weight / total
        self.statistical_weight = statistical_weight / total
        
        logger.info(
            f"Updated ensemble weights: "
            f"Claude={self.claude_weight:.2f}, Statistical={self.statistical_weight:.2f}"
        )

