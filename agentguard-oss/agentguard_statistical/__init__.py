"""
AgentGuard Statistical Judge - Open Source Hallucination Detection

A lightweight, fast, and accurate statistical approach to detecting hallucinations
in AI-generated text. This is the open-source core of the AgentGuard platform.

Example:
    >>> from agentguard_statistical import StatisticalJudge
    >>> judge = StatisticalJudge()
    >>> score, confidence = judge.evaluate("AI generated text here")
    >>> print(f"Hallucination score: {score:.3f}")
"""

__version__ = "1.0.0"
__author__ = "Mothership AI"
__email__ = "opensource@mothership-ai.com"
__license__ = "MIT"

from .statistical_judge import StatisticalJudge
from .utils import benchmark, load_dataset
from .metrics import calculate_metrics, bootstrap_confidence_interval

__all__ = [
    "StatisticalJudge",
    "benchmark",
    "load_dataset", 
    "calculate_metrics",
    "bootstrap_confidence_interval"
]
