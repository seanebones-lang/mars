import logging
from typing import Tuple, List, Dict, Optional
import torch
import torch.nn.functional as F
import numpy as np
from transformers import AutoTokenizer, AutoModel
import math
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AttentionMetrics:
    """Attention-based hallucination detection metrics."""
    attention_entropy: float
    context_ratio: float
    attention_variance: float
    high_entropy_tokens: List[int]


class StatisticalJudge:
    """
    Enhanced Statistical hallucination detection with attention analysis.
    
    October 2025 Enhancements:
    - Attention weight computation for hallucination detection
    - Context vs generated token ratio analysis
    - High-entropy segment flagging for real-time detection
    - Integration with ensemble weighting (20% contribution)
    
    Based on latest research in attention-based hallucination detection.
    """
    
    def __init__(self, model_name: str = "distilbert-base-uncased"):
        """
        Initialize enhanced statistical judge with attention analysis.
        
        Args:
            model_name: Hugging Face model identifier (default: distilbert for efficiency)
        """
        logger.info(f"Loading enhanced statistical model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name, output_attentions=True)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
        
        # Attention analysis thresholds
        self.high_entropy_threshold = 0.7  # Flag tokens with entropy > 0.7
        self.context_ratio_threshold = 0.3  # Flag if context ratio < 0.3
        self.attention_variance_threshold = 0.5  # Flag high attention variance
        
        logger.info(f"Enhanced statistical model loaded on {self.device} with attention analysis")

    def evaluate(self, agent_output: str, context: Optional[str] = None) -> Tuple[float, List[float]]:
        """
        Enhanced evaluation with attention-based hallucination detection.
        
        Args:
            agent_output: Text to evaluate for hallucination indicators
            context: Optional context for context vs generated token analysis
            
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
                outputs = self.model(**inputs, output_hidden_states=True, output_attentions=True)
                hidden_states = outputs.last_hidden_state
                attentions = outputs.attentions  # List of attention tensors per layer
            
            # Traditional entropy-based scoring
            entropy_score = self._compute_entropy_score(hidden_states)
            
            # First-token confidence
            confidence_score = self._compute_first_token_confidence(hidden_states)
            
            # NEW: Attention-based analysis (October 2025 enhancement)
            attention_metrics = self._compute_attention_metrics(attentions, inputs['input_ids'])
            attention_score = self._attention_to_score(attention_metrics)
            
            # NEW: Context ratio analysis if context provided
            context_score = 1.0  # Default if no context
            if context is not None:
                context_score = self._compute_context_ratio_score(agent_output, context)
            
            # Enhanced weighted combination (attention gets 20% weight as per plan)
            combined_score = (
                0.4 * entropy_score +
                0.3 * confidence_score +
                0.2 * attention_score +
                0.1 * context_score
            )
            
            # Enhanced confidence interval with attention uncertainty
            confidence_interval = self._bootstrap_confidence_interval_enhanced(
                entropy_score,
                confidence_score,
                attention_score,
                context_score,
                attention_metrics.attention_variance
            )
            
            logger.debug(
                f"Enhanced scores - Entropy: {entropy_score:.3f}, "
                f"Confidence: {confidence_score:.3f}, "
                f"Attention: {attention_score:.3f}, "
                f"Context: {context_score:.3f}, "
                f"Combined: {combined_score:.3f}"
            )
            
            return combined_score, confidence_interval
            
        except Exception as e:
            logger.error(f"Statistical evaluation error: {e}")
            # Fallback: neutral score with wide confidence interval
            return 0.5, [0.0, 1.0]

    def evaluate_with_attention_details(self, agent_output: str, context: Optional[str] = None) -> Dict:
        """
        Detailed evaluation with attention metrics for debugging and analysis.
        
        Returns:
            Dict with detailed metrics including attention analysis
        """
        try:
            inputs = self.tokenizer(
                agent_output,
                return_tensors="pt",
                truncation=True,
                max_length=512
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs, output_hidden_states=True, output_attentions=True)
                hidden_states = outputs.last_hidden_state
                attentions = outputs.attentions
            
            # Compute all metrics
            entropy_score = self._compute_entropy_score(hidden_states)
            confidence_score = self._compute_first_token_confidence(hidden_states)
            attention_metrics = self._compute_attention_metrics(attentions, inputs['input_ids'])
            attention_score = self._attention_to_score(attention_metrics)
            
            context_score = 1.0
            if context is not None:
                context_score = self._compute_context_ratio_score(agent_output, context)
            
            combined_score = (
                0.4 * entropy_score +
                0.3 * confidence_score +
                0.2 * attention_score +
                0.1 * context_score
            )
            
            # Get token-level details
            tokens = self.tokenizer.convert_ids_to_tokens(inputs['input_ids'][0])
            
            return {
                "combined_score": combined_score,
                "entropy_score": entropy_score,
                "confidence_score": confidence_score,
                "attention_score": attention_score,
                "context_score": context_score,
                "attention_metrics": {
                    "attention_entropy": attention_metrics.attention_entropy,
                    "context_ratio": attention_metrics.context_ratio,
                    "attention_variance": attention_metrics.attention_variance,
                    "high_entropy_tokens": attention_metrics.high_entropy_tokens
                },
                "tokens": tokens,
                "flagged_tokens": [tokens[i] for i in attention_metrics.high_entropy_tokens if i < len(tokens)]
            }
            
        except Exception as e:
            logger.error(f"Detailed evaluation error: {e}")
            return {
                "combined_score": 0.5,
                "error": str(e)
            }

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

    def _compute_attention_metrics(self, attentions: List[torch.Tensor], input_ids: torch.Tensor) -> AttentionMetrics:
        """
        Compute attention-based hallucination detection metrics.
        
        October 2025 Enhancement: Attention weight analysis for hallucination detection.
        
        Args:
            attentions: List of attention tensors from transformer layers
            input_ids: Input token IDs for context analysis
            
        Returns:
            AttentionMetrics with computed attention-based features
        """
        # Use last layer attention for analysis (most refined)
        last_attention = attentions[-1]  # Shape: [batch, heads, seq_len, seq_len]
        
        # Average across attention heads
        avg_attention = last_attention.mean(dim=1)  # Shape: [batch, seq_len, seq_len]
        
        # Compute attention entropy for each token
        attention_entropies = []
        seq_len = avg_attention.size(-1)
        
        for i in range(seq_len):
            # Attention distribution for token i
            attn_dist = avg_attention[0, i, :]  # Attention weights for token i
            
            # Normalize to probability distribution
            attn_probs = F.softmax(attn_dist, dim=0)
            
            # Calculate entropy
            entropy = -torch.sum(attn_probs * torch.log(attn_probs + 1e-10))
            attention_entropies.append(entropy.item())
        
        # Overall attention entropy (mean across tokens)
        attention_entropy = float(np.mean(attention_entropies))
        
        # Identify high-entropy tokens (potential hallucinations)
        high_entropy_tokens = [
            i for i, entropy in enumerate(attention_entropies) 
            if entropy > self.high_entropy_threshold
        ]
        
        # Compute attention variance (measure of uncertainty)
        attention_variance = float(torch.var(avg_attention).item())
        
        # Context ratio analysis
        # Compute how much attention is paid to context vs generated tokens
        # For simplicity, assume first half is context, second half is generated
        mid_point = seq_len // 2
        context_attention = avg_attention[0, mid_point:, :mid_point].sum().item()
        total_attention = avg_attention[0, mid_point:, :].sum().item()
        
        context_ratio = context_attention / (total_attention + 1e-10)
        
        return AttentionMetrics(
            attention_entropy=attention_entropy,
            context_ratio=context_ratio,
            attention_variance=attention_variance,
            high_entropy_tokens=high_entropy_tokens
        )

    def _attention_to_score(self, attention_metrics: AttentionMetrics) -> float:
        """
        Convert attention metrics to hallucination score.
        
        Lower entropy + higher context ratio + lower variance = higher score (less hallucination)
        """
        # Normalize entropy (typical range 0-3, invert so low entropy = high score)
        entropy_score = max(0.0, 1.0 - (attention_metrics.attention_entropy / 3.0))
        
        # Context ratio score (higher ratio = better)
        context_score = attention_metrics.context_ratio
        
        # Variance score (lower variance = better, typical range 0-1)
        variance_score = max(0.0, 1.0 - attention_metrics.attention_variance)
        
        # Weighted combination
        attention_score = 0.4 * entropy_score + 0.4 * context_score + 0.2 * variance_score
        
        return float(max(0.0, min(1.0, attention_score)))

    def _compute_context_ratio_score(self, agent_output: str, context: str) -> float:
        """
        Compute context vs generated token ratio score.
        
        Measures how well the agent output relates to the provided context.
        Higher overlap with context = higher score.
        """
        try:
            # Simple token overlap analysis
            agent_tokens = set(self.tokenizer.tokenize(agent_output.lower()))
            context_tokens = set(self.tokenizer.tokenize(context.lower()))
            
            # Compute Jaccard similarity
            intersection = len(agent_tokens.intersection(context_tokens))
            union = len(agent_tokens.union(context_tokens))
            
            jaccard_score = intersection / (union + 1e-10)
            
            # Penalize if context ratio is below threshold
            if jaccard_score < self.context_ratio_threshold:
                penalty = (self.context_ratio_threshold - jaccard_score) * 0.5
                jaccard_score = max(0.0, jaccard_score - penalty)
            
            return float(jaccard_score)
            
        except Exception as e:
            logger.error(f"Context ratio computation error: {e}")
            return 0.5  # Neutral score on error

    def _bootstrap_confidence_interval_enhanced(
        self,
        entropy_score: float,
        confidence_score: float,
        attention_score: float,
        context_score: float,
        attention_variance: float,
        n_bootstrap: int = 15,
        confidence_level: float = 0.9
    ) -> List[float]:
        """
        Enhanced bootstrap confidence interval with attention uncertainty.
        
        Incorporates attention variance as additional uncertainty measure.
        """
        # Generate bootstrap samples
        scores = [entropy_score, confidence_score, attention_score, context_score]
        bootstrap_samples = np.random.choice(
            scores,
            size=(n_bootstrap, len(scores)),
            replace=True
        )
        
        # Add noise proportional to attention variance (higher variance = more noise)
        noise_scale = 0.05 + (attention_variance * 0.1)
        bootstrap_samples += np.random.normal(0, noise_scale, size=bootstrap_samples.shape)
        
        # Compute weighted means (same weights as main evaluation)
        weights = [0.4, 0.3, 0.2, 0.1]
        bootstrap_means = np.average(bootstrap_samples, axis=1, weights=weights)
        
        # Calculate percentiles
        alpha = (1 - confidence_level) / 2
        lower_percentile = alpha * 100
        upper_percentile = (1 - alpha) * 100
        
        lower_bound = float(np.percentile(bootstrap_means, lower_percentile))
        upper_bound = float(np.percentile(bootstrap_means, upper_percentile))
        
        # Clip to [0, 1] range
        lower_bound = max(0.0, min(1.0, lower_bound))
        upper_bound = max(0.0, min(1.0, upper_bound))
        
        return [lower_bound, upper_bound]

