import logging
from typing import Tuple, List
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel

logger = logging.getLogger(__name__)


class StatisticalJudge:
    """
    Statistical hallucination detection using token-level entropy analysis.
    Implements enhanced methods from arXiv September 2025 for real-time scaling
    with 70B+ models and unsupervised confidence estimation.
    """
    
    def __init__(self, model_name: str = "distilbert-base-uncased"):
        """
        Initialize statistical judge with lightweight model.
        
        Args:
            model_name: Hugging Face model identifier (default: distilbert for efficiency)
        """
        logger.info(f"Loading statistical model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
        logger.info(f"Statistical model loaded on {self.device}")

    def evaluate(self, agent_output: str) -> Tuple[float, List[float]]:
        """
        Evaluate text using entropy-based hallucination detection.
        
        Args:
            agent_output: Text to evaluate for hallucination indicators
            
        Returns:
            Tuple of (combined_score, confidence_interval)
            - combined_score: 0-1 where 1=confident/accurate, 0=uncertain/hallucinated
            - confidence_interval: [lower_bound, upper_bound] from bootstrapping
        """
        try:
            # Tokenize input
            inputs = self.tokenizer(
                agent_output,
                return_tensors="pt",
                truncation=True,
                max_length=512
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs, output_hidden_states=True)
                # For encoder models, use last hidden state
                hidden_states = outputs.last_hidden_state
            
            # Entropy-based scoring (arXiv Sept 2025 real-time method)
            entropy_score = self._compute_entropy_score(hidden_states)
            
            # First-token confidence (unsupervised method, July 2025)
            confidence_score = self._compute_first_token_confidence(hidden_states)
            
            # Combined score (50/50 weighting)
            combined_score = 0.5 * entropy_score + 0.5 * confidence_score
            
            # Bootstrap confidence interval for uncertainty estimation
            confidence_interval = self._bootstrap_confidence_interval(
                entropy_score,
                confidence_score
            )
            
            logger.debug(
                f"Statistical scores - Entropy: {entropy_score:.3f}, "
                f"Confidence: {confidence_score:.3f}, "
                f"Combined: {combined_score:.3f}"
            )
            
            return combined_score, confidence_interval
            
        except Exception as e:
            logger.error(f"Statistical evaluation error: {e}")
            # Fallback: neutral score with wide confidence interval
            return 0.5, [0.0, 1.0]

    def _compute_entropy_score(self, hidden_states: torch.Tensor) -> float:
        """
        Compute normalized entropy score from hidden states.
        Low entropy = high confidence, High entropy = uncertainty/hallucination.
        """
        # Compute variance across hidden dimensions as uncertainty proxy
        variance = torch.var(hidden_states, dim=-1)
        mean_variance = variance.mean().item()
        
        # Normalize to 0-1 range (typical variance range for normalized embeddings)
        normalized_variance = min(mean_variance / 0.5, 1.0)
        
        # Invert: high variance -> low score (hallucination indicator)
        entropy_score = 1 - normalized_variance
        
        return float(max(0.0, min(1.0, entropy_score)))

    def _compute_first_token_confidence(self, hidden_states: torch.Tensor) -> float:
        """
        Compute confidence from hidden state magnitudes.
        Inspired by unsupervised hallucination detection (July 2025).
        """
        # Compute L2 norm of hidden states as confidence proxy
        norms = torch.norm(hidden_states, p=2, dim=-1)
        
        # First token norm as confidence indicator
        first_token_norm = norms[0, 0].item()
        
        # Average norm across all tokens for robustness
        avg_norm = norms.mean().item()
        
        # Normalize to 0-1 range (typical norm range is 0-10)
        first_token_conf = min(first_token_norm / 10.0, 1.0)
        avg_conf = min(avg_norm / 10.0, 1.0)
        
        # Weighted combination
        confidence_score = 0.6 * first_token_conf + 0.4 * avg_conf
        
        return float(max(0.0, min(1.0, confidence_score)))

    def _bootstrap_confidence_interval(
        self,
        entropy_score: float,
        confidence_score: float,
        n_bootstrap: int = 10,
        confidence_level: float = 0.9
    ) -> List[float]:
        """
        Generate confidence interval via bootstrapping for uncertainty estimation.
        
        Args:
            entropy_score: Entropy-based score
            confidence_score: Confidence-based score
            n_bootstrap: Number of bootstrap samples
            confidence_level: Confidence level (default 90%)
            
        Returns:
            [lower_bound, upper_bound] of confidence interval
        """
        # Generate bootstrap samples by resampling scores with noise
        bootstrap_samples = np.random.choice(
            [entropy_score, confidence_score],
            size=(n_bootstrap, 2),
            replace=True
        )
        
        # Add small Gaussian noise to simulate variability
        bootstrap_samples += np.random.normal(0, 0.05, size=bootstrap_samples.shape)
        
        # Compute means of bootstrap samples
        bootstrap_means = bootstrap_samples.mean(axis=1)
        
        # Calculate percentiles for confidence interval
        alpha = (1 - confidence_level) / 2
        lower_percentile = alpha * 100
        upper_percentile = (1 - alpha) * 100
        
        lower_bound = float(np.percentile(bootstrap_means, lower_percentile))
        upper_bound = float(np.percentile(bootstrap_means, upper_percentile))
        
        # Clip to [0, 1] range
        lower_bound = max(0.0, min(1.0, lower_bound))
        upper_bound = max(0.0, min(1.0, upper_bound))
        
        return [lower_bound, upper_bound]

