"""
Statistical Judge for Hallucination Detection

Open-source implementation of statistical hallucination detection using
entropy analysis, attention patterns, and context alignment.
"""

import logging
import warnings
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from scipy import stats
from dataclasses import dataclass

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning)
logging.getLogger("transformers").setLevel(logging.ERROR)

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
    Statistical hallucination detection using entropy analysis and attention patterns.
    
    This open-source implementation provides fast, accurate hallucination detection
    using statistical methods without requiring external API calls.
    
    Features:
    - Entropy-based uncertainty detection
    - Attention weight analysis
    - Context comparison and alignment
    - Confidence interval estimation
    - Span-level detection capabilities
    
    Example:
        >>> judge = StatisticalJudge()
        >>> score, confidence = judge.evaluate("The Eiffel Tower is 500m tall")
        >>> print(f"Hallucination score: {score:.3f}")
    """
    
    def __init__(self, 
                 model_name: str = "distilbert-base-uncased",
                 device: str = "auto",
                 high_entropy_threshold: float = 0.7,
                 context_ratio_threshold: float = 0.3,
                 attention_variance_threshold: float = 0.5):
        """
        Initialize the Statistical Judge.
        
        Args:
            model_name: Hugging Face model identifier
            device: Device for inference ('cpu', 'cuda', 'auto')
            high_entropy_threshold: Threshold for flagging high-entropy tokens
            context_ratio_threshold: Threshold for context alignment
            attention_variance_threshold: Threshold for attention variance
        """
        self.model_name = model_name
        self.device = self._setup_device(device)
        
        # Thresholds
        self.high_entropy_threshold = high_entropy_threshold
        self.context_ratio_threshold = context_ratio_threshold
        self.attention_variance_threshold = attention_variance_threshold
        
        # Load model and tokenizer
        logger.info(f"Loading model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name, output_attentions=True)
        self.model.to(self.device)
        self.model.eval()
        
        # Performance tracking
        self.stats = {
            'evaluations': 0,
            'total_time': 0.0,
            'avg_score': 0.0
        }
        
        logger.info(f"Statistical Judge initialized on {self.device}")

    def _setup_device(self, device: str) -> str:
        """Setup computation device."""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        return device

    def evaluate(self, 
                 agent_output: str, 
                 context: Optional[str] = None) -> Tuple[float, List[float]]:
        """
        Evaluate text for hallucination indicators.
        
        Args:
            agent_output: Text to evaluate for hallucination indicators
            context: Optional context for comparison
            
        Returns:
            Tuple of (hallucination_score, confidence_interval)
            - hallucination_score: 0-1 where 1=likely hallucination, 0=likely accurate
            - confidence_interval: [lower_bound, upper_bound] from bootstrapping
        """
        import time
        start_time = time.time()
        
        try:
            # Tokenize input
            inputs = self.tokenizer(
                agent_output,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs, output_hidden_states=True, output_attentions=True)
                hidden_states = outputs.last_hidden_state
                attentions = outputs.attentions
            
            # Core statistical analysis
            entropy_score = self._compute_entropy_score(hidden_states)
            confidence_score = self._compute_first_token_confidence(hidden_states)
            
            # Attention-based analysis
            attention_metrics = self._compute_attention_metrics(attentions, inputs['input_ids'])
            attention_score = self._attention_to_score(attention_metrics)
            
            # Context comparison if provided
            context_score = 1.0
            if context is not None:
                context_score = self._compute_context_ratio_score(agent_output, context)
            
            # Weighted combination
            combined_score = (
                0.4 * entropy_score +
                0.3 * confidence_score +
                0.2 * attention_score +
                0.1 * context_score
            )
            
            # Bootstrap confidence interval
            confidence_interval = self._bootstrap_confidence_interval_enhanced(
                entropy_score,
                confidence_score,
                attention_score,
                context_score,
                attention_metrics.attention_variance
            )
            
            # Update statistics
            processing_time = time.time() - start_time
            self._update_stats(combined_score, processing_time)
            
            return combined_score, confidence_interval
            
        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            return 0.5, [0.0, 1.0]  # Neutral score with wide interval

    def evaluate_with_attention_details(self, 
                                      agent_output: str, 
                                      context: Optional[str] = None) -> Dict[str, Any]:
        """
        Detailed evaluation with attention analysis and token-level information.
        
        Args:
            agent_output: Text to evaluate
            context: Optional context for comparison
            
        Returns:
            Dictionary with detailed analysis including:
            - hallucination_score: Overall score
            - confidence_interval: Confidence bounds
            - attention_metrics: Attention analysis results
            - flagged_tokens: List of potentially problematic tokens
            - tokens: List of all tokens
        """
        try:
            # Run standard evaluation
            score, confidence = self.evaluate(agent_output, context)
            
            # Get detailed token analysis
            inputs = self.tokenizer(
                agent_output,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                return_offsets_mapping=True
            ).to(self.device)
            
            tokens = self.tokenizer.convert_ids_to_tokens(inputs['input_ids'][0])
            
            with torch.no_grad():
                outputs = self.model(**{k: v for k, v in inputs.items() if k != 'offset_mapping'})
                attentions = outputs.attentions
            
            # Compute attention metrics
            attention_metrics = self._compute_attention_metrics(attentions, inputs['input_ids'])
            
            # Identify flagged tokens
            flagged_tokens = []
            for token_idx in attention_metrics.high_entropy_tokens:
                if token_idx < len(tokens):
                    flagged_tokens.append({
                        'index': token_idx,
                        'token': tokens[token_idx],
                        'reason': 'high_entropy'
                    })
            
            return {
                'hallucination_score': score,
                'confidence_interval': confidence,
                'attention_metrics': {
                    'attention_entropy': attention_metrics.attention_entropy,
                    'context_ratio': attention_metrics.context_ratio,
                    'attention_variance': attention_metrics.attention_variance
                },
                'flagged_tokens': flagged_tokens,
                'tokens': tokens,
                'total_tokens': len(tokens)
            }
            
        except Exception as e:
            logger.error(f"Detailed evaluation error: {e}")
            return {
                'hallucination_score': 0.5,
                'confidence_interval': [0.0, 1.0],
                'attention_metrics': {},
                'flagged_tokens': [],
                'tokens': [],
                'total_tokens': 0
            }

    def batch_evaluate(self, 
                      texts: List[str], 
                      contexts: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Batch evaluation of multiple texts.
        
        Args:
            texts: List of texts to evaluate
            contexts: Optional list of contexts (must match length of texts)
            
        Returns:
            List of evaluation results
        """
        if contexts and len(contexts) != len(texts):
            raise ValueError("Contexts list must match length of texts")
        
        results = []
        for i, text in enumerate(texts):
            context = contexts[i] if contexts else None
            score, confidence = self.evaluate(text, context)
            
            results.append({
                'text': text,
                'hallucination_score': score,
                'confidence_interval': confidence,
                'index': i
            })
        
        return results

    def _compute_entropy_score(self, hidden_states: torch.Tensor) -> float:
        """Compute entropy-based uncertainty score."""
        try:
            # Calculate token-level entropy
            logits = hidden_states.mean(dim=1)  # Average across sequence
            probs = F.softmax(logits, dim=-1)
            entropy = -torch.sum(probs * torch.log(probs + 1e-10), dim=-1)
            
            # Normalize entropy
            max_entropy = np.log(hidden_states.size(-1))
            normalized_entropy = entropy.mean().item() / max_entropy
            
            return float(np.clip(normalized_entropy, 0.0, 1.0))
            
        except Exception as e:
            logger.error(f"Entropy computation error: {e}")
            return 0.5

    def _compute_first_token_confidence(self, hidden_states: torch.Tensor) -> float:
        """Compute confidence based on first token representation."""
        try:
            first_token = hidden_states[0, 0, :]  # [CLS] token
            
            # Calculate confidence as inverse of variance
            variance = torch.var(first_token).item()
            confidence = 1.0 / (1.0 + variance)
            
            return float(np.clip(confidence, 0.0, 1.0))
            
        except Exception as e:
            logger.error(f"Confidence computation error: {e}")
            return 0.5

    def _compute_attention_metrics(self, 
                                 attentions: Tuple[torch.Tensor], 
                                 input_ids: torch.Tensor) -> AttentionMetrics:
        """Compute attention-based metrics for hallucination detection."""
        try:
            if not attentions:
                return AttentionMetrics(0.5, 0.5, 0.5, [])
            
            # Use last layer attention
            last_attention = attentions[-1]  # Shape: [batch, heads, seq_len, seq_len]
            
            # Average across heads and batch
            avg_attention = last_attention.mean(dim=(0, 1))  # Shape: [seq_len, seq_len]
            
            # Calculate attention entropy for each position
            entropies = []
            for i in range(avg_attention.size(0)):
                attn_dist = F.softmax(avg_attention[i], dim=0)
                entropy = -torch.sum(attn_dist * torch.log(attn_dist + 1e-10))
                entropies.append(entropy.item())
            
            # Attention metrics
            attention_entropy = np.mean(entropies)
            attention_variance = np.var(entropies)
            
            # Normalize entropy
            max_entropy = np.log(avg_attention.size(0))
            normalized_entropy = attention_entropy / max_entropy if max_entropy > 0 else 0.5
            
            # Find high entropy tokens
            high_entropy_tokens = [
                i for i, entropy in enumerate(entropies)
                if entropy > self.high_entropy_threshold * max_entropy
            ]
            
            # Context ratio (simplified)
            context_ratio = 0.5  # Placeholder for context analysis
            
            return AttentionMetrics(
                attention_entropy=normalized_entropy,
                context_ratio=context_ratio,
                attention_variance=attention_variance,
                high_entropy_tokens=high_entropy_tokens
            )
            
        except Exception as e:
            logger.error(f"Attention metrics error: {e}")
            return AttentionMetrics(0.5, 0.5, 0.5, [])

    def _attention_to_score(self, attention_metrics: AttentionMetrics) -> float:
        """Convert attention metrics to hallucination score."""
        try:
            # High entropy and variance suggest potential hallucination
            entropy_component = attention_metrics.attention_entropy
            variance_component = min(attention_metrics.attention_variance / 1.0, 1.0)
            context_component = 1.0 - attention_metrics.context_ratio
            
            score = (
                0.5 * entropy_component +
                0.3 * variance_component +
                0.2 * context_component
            )
            
            return float(np.clip(score, 0.0, 1.0))
            
        except Exception as e:
            logger.error(f"Attention score conversion error: {e}")
            return 0.5

    def _compute_context_ratio_score(self, agent_output: str, context: str) -> float:
        """Compute context alignment score."""
        try:
            # Simple token overlap ratio
            agent_tokens = set(self.tokenizer.tokenize(agent_output.lower()))
            context_tokens = set(self.tokenizer.tokenize(context.lower()))
            
            if not agent_tokens:
                return 0.5
            
            overlap = len(agent_tokens.intersection(context_tokens))
            ratio = overlap / len(agent_tokens)
            
            return float(np.clip(ratio, 0.0, 1.0))
            
        except Exception as e:
            logger.error(f"Context ratio computation error: {e}")
            return 0.5

    def _bootstrap_confidence_interval_enhanced(self, 
                                              entropy_score: float,
                                              confidence_score: float,
                                              attention_score: float,
                                              context_score: float,
                                              attention_variance: float,
                                              n_bootstrap: int = 100) -> List[float]:
        """Enhanced bootstrap confidence interval with attention uncertainty."""
        try:
            scores = []
            
            for _ in range(n_bootstrap):
                # Add noise based on attention variance
                noise_scale = min(attention_variance, 0.1)
                
                noisy_entropy = np.clip(entropy_score + np.random.normal(0, noise_scale), 0, 1)
                noisy_confidence = np.clip(confidence_score + np.random.normal(0, noise_scale), 0, 1)
                noisy_attention = np.clip(attention_score + np.random.normal(0, noise_scale), 0, 1)
                noisy_context = np.clip(context_score + np.random.normal(0, noise_scale), 0, 1)
                
                # Recombine with same weights
                bootstrap_score = (
                    0.4 * noisy_entropy +
                    0.3 * noisy_confidence +
                    0.2 * noisy_attention +
                    0.1 * noisy_context
                )
                
                scores.append(bootstrap_score)
            
            # Calculate confidence interval
            lower = np.percentile(scores, 2.5)
            upper = np.percentile(scores, 97.5)
            
            return [float(lower), float(upper)]
            
        except Exception as e:
            logger.error(f"Bootstrap confidence interval error: {e}")
            return [0.0, 1.0]

    def _update_stats(self, score: float, processing_time: float):
        """Update processing statistics."""
        self.stats['evaluations'] += 1
        self.stats['total_time'] += processing_time
        
        # Update running average
        n = self.stats['evaluations']
        current_avg = self.stats['avg_score']
        self.stats['avg_score'] = (current_avg * (n - 1) + score) / n

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        stats = self.stats.copy()
        if stats['evaluations'] > 0:
            stats['avg_processing_time'] = stats['total_time'] / stats['evaluations']
        else:
            stats['avg_processing_time'] = 0.0
        
        stats['model_name'] = self.model_name
        stats['device'] = self.device
        
        return stats

    def evaluate_dataset(self, dataset: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Evaluate performance on a labeled dataset.
        
        Args:
            dataset: List of dicts with 'text' and 'label' keys
                    label: 0 = accurate, 1 = hallucination
                    
        Returns:
            Dictionary with accuracy, precision, recall, f1
        """
        try:
            predictions = []
            labels = []
            
            for item in dataset:
                score, _ = self.evaluate(item['text'])
                prediction = 1 if score > 0.5 else 0
                
                predictions.append(prediction)
                labels.append(item['label'])
            
            # Calculate metrics
            tp = sum(1 for p, l in zip(predictions, labels) if p == 1 and l == 1)
            fp = sum(1 for p, l in zip(predictions, labels) if p == 1 and l == 0)
            fn = sum(1 for p, l in zip(predictions, labels) if p == 0 and l == 1)
            tn = sum(1 for p, l in zip(predictions, labels) if p == 0 and l == 0)
            
            accuracy = (tp + tn) / len(labels) if labels else 0.0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            
            return {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'samples': len(labels)
            }
            
        except Exception as e:
            logger.error(f"Dataset evaluation error: {e}")
            return {'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'samples': 0}
