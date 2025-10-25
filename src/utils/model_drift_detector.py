"""
AI Model Drift Detection
P1-1: Monitor for changes in AI model behavior over time
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


class ModelDriftDetector:
    """
    Detect drift in AI model behavior.
    
    Monitors:
    - Hallucination detection accuracy
    - Response patterns
    - Confidence scores
    - Error rates
    """
    
    def __init__(self, window_days: int = 7):
        """
        Initialize drift detector.
        
        Args:
            window_days: Number of days for baseline comparison
        """
        self.window_days = window_days
        
        # Historical data storage
        self.detection_results: List[Dict] = []
        self.baseline_metrics: Optional[Dict] = None
        
        # Drift thresholds
        self.accuracy_threshold = float(os.getenv("DRIFT_ACCURACY_THRESHOLD", "0.05"))  # 5% change
        self.confidence_threshold = float(os.getenv("DRIFT_CONFIDENCE_THRESHOLD", "0.10"))  # 10% change
        self.error_rate_threshold = float(os.getenv("DRIFT_ERROR_RATE_THRESHOLD", "0.02"))  # 2% change
        
        logger.info(f"Model drift detector initialized with {window_days}-day window")
    
    def record_detection(
        self,
        model: str,
        is_hallucination: bool,
        confidence: float,
        ground_truth: Optional[bool] = None,
        response_time: float = 0.0,
        error: bool = False
    ):
        """
        Record a detection result for drift analysis.
        
        Args:
            model: Model name
            is_hallucination: Whether hallucination was detected
            confidence: Confidence score (0-1)
            ground_truth: Actual ground truth (if known)
            response_time: Response time in seconds
            error: Whether an error occurred
        """
        result = {
            "timestamp": datetime.utcnow(),
            "model": model,
            "is_hallucination": is_hallucination,
            "confidence": confidence,
            "ground_truth": ground_truth,
            "response_time": response_time,
            "error": error,
            "correct": ground_truth == is_hallucination if ground_truth is not None else None
        }
        
        self.detection_results.append(result)
        
        # Keep only recent data (2x window for comparison)
        cutoff = datetime.utcnow() - timedelta(days=self.window_days * 2)
        self.detection_results = [
            r for r in self.detection_results
            if r["timestamp"] >= cutoff
        ]
    
    def calculate_baseline_metrics(self) -> Dict:
        """
        Calculate baseline metrics from historical data.
        
        Returns:
            Dictionary of baseline metrics
        """
        cutoff = datetime.utcnow() - timedelta(days=self.window_days)
        baseline_data = [
            r for r in self.detection_results
            if r["timestamp"] >= cutoff
        ]
        
        if not baseline_data:
            return {
                "sample_size": 0,
                "accuracy": 0.0,
                "avg_confidence": 0.0,
                "error_rate": 0.0,
                "hallucination_rate": 0.0,
                "avg_response_time": 0.0
            }
        
        # Calculate metrics
        correct_predictions = [r for r in baseline_data if r["correct"] is True]
        total_with_ground_truth = [r for r in baseline_data if r["ground_truth"] is not None]
        
        accuracy = len(correct_predictions) / len(total_with_ground_truth) if total_with_ground_truth else 0.0
        
        confidences = [r["confidence"] for r in baseline_data]
        avg_confidence = statistics.mean(confidences) if confidences else 0.0
        
        errors = [r for r in baseline_data if r["error"]]
        error_rate = len(errors) / len(baseline_data) if baseline_data else 0.0
        
        hallucinations = [r for r in baseline_data if r["is_hallucination"]]
        hallucination_rate = len(hallucinations) / len(baseline_data) if baseline_data else 0.0
        
        response_times = [r["response_time"] for r in baseline_data]
        avg_response_time = statistics.mean(response_times) if response_times else 0.0
        
        metrics = {
            "sample_size": len(baseline_data),
            "accuracy": accuracy,
            "avg_confidence": avg_confidence,
            "error_rate": error_rate,
            "hallucination_rate": hallucination_rate,
            "avg_response_time": avg_response_time,
            "confidence_std": statistics.stdev(confidences) if len(confidences) > 1 else 0.0,
            "calculated_at": datetime.utcnow().isoformat()
        }
        
        self.baseline_metrics = metrics
        return metrics
    
    def detect_drift(self) -> Tuple[bool, Dict]:
        """
        Detect if model behavior has drifted.
        
        Returns:
            Tuple of (drift_detected, drift_report)
        """
        # Calculate current metrics (last 24 hours)
        cutoff_current = datetime.utcnow() - timedelta(days=1)
        current_data = [
            r for r in self.detection_results
            if r["timestamp"] >= cutoff_current
        ]
        
        if len(current_data) < 10:
            return False, {
                "status": "insufficient_data",
                "message": "Not enough recent data to detect drift (minimum 10 samples)",
                "sample_size": len(current_data)
            }
        
        # Calculate baseline if not exists
        if self.baseline_metrics is None:
            self.calculate_baseline_metrics()
        
        if self.baseline_metrics["sample_size"] < 50:
            return False, {
                "status": "insufficient_baseline",
                "message": "Not enough baseline data to detect drift (minimum 50 samples)",
                "baseline_size": self.baseline_metrics["sample_size"]
            }
        
        # Calculate current metrics
        correct_predictions = [r for r in current_data if r["correct"] is True]
        total_with_ground_truth = [r for r in current_data if r["ground_truth"] is not None]
        
        current_accuracy = len(correct_predictions) / len(total_with_ground_truth) if total_with_ground_truth else 0.0
        
        confidences = [r["confidence"] for r in current_data]
        current_confidence = statistics.mean(confidences) if confidences else 0.0
        
        errors = [r for r in current_data if r["error"]]
        current_error_rate = len(errors) / len(current_data) if current_data else 0.0
        
        hallucinations = [r for r in current_data if r["is_hallucination"]]
        current_hallucination_rate = len(hallucinations) / len(current_data) if current_data else 0.0
        
        response_times = [r["response_time"] for r in current_data]
        current_response_time = statistics.mean(response_times) if response_times else 0.0
        
        # Detect drift
        drift_detected = False
        drift_details = []
        
        # Accuracy drift
        accuracy_change = abs(current_accuracy - self.baseline_metrics["accuracy"])
        if accuracy_change > self.accuracy_threshold:
            drift_detected = True
            drift_details.append({
                "metric": "accuracy",
                "baseline": self.baseline_metrics["accuracy"],
                "current": current_accuracy,
                "change": accuracy_change,
                "threshold": self.accuracy_threshold,
                "severity": "high" if accuracy_change > self.accuracy_threshold * 2 else "medium"
            })
        
        # Confidence drift
        confidence_change = abs(current_confidence - self.baseline_metrics["avg_confidence"])
        if confidence_change > self.confidence_threshold:
            drift_detected = True
            drift_details.append({
                "metric": "confidence",
                "baseline": self.baseline_metrics["avg_confidence"],
                "current": current_confidence,
                "change": confidence_change,
                "threshold": self.confidence_threshold,
                "severity": "medium"
            })
        
        # Error rate drift
        error_rate_change = abs(current_error_rate - self.baseline_metrics["error_rate"])
        if error_rate_change > self.error_rate_threshold:
            drift_detected = True
            drift_details.append({
                "metric": "error_rate",
                "baseline": self.baseline_metrics["error_rate"],
                "current": current_error_rate,
                "change": error_rate_change,
                "threshold": self.error_rate_threshold,
                "severity": "high" if current_error_rate > self.baseline_metrics["error_rate"] else "medium"
            })
        
        # Hallucination rate drift (informational)
        hallucination_change = abs(current_hallucination_rate - self.baseline_metrics["hallucination_rate"])
        if hallucination_change > 0.10:  # 10% change
            drift_details.append({
                "metric": "hallucination_rate",
                "baseline": self.baseline_metrics["hallucination_rate"],
                "current": current_hallucination_rate,
                "change": hallucination_change,
                "threshold": 0.10,
                "severity": "low"
            })
        
        # Response time drift (informational)
        response_time_change = abs(current_response_time - self.baseline_metrics["avg_response_time"])
        if response_time_change > 0.5:  # 500ms change
            drift_details.append({
                "metric": "response_time",
                "baseline": self.baseline_metrics["avg_response_time"],
                "current": current_response_time,
                "change": response_time_change,
                "threshold": 0.5,
                "severity": "low"
            })
        
        report = {
            "drift_detected": drift_detected,
            "timestamp": datetime.utcnow().isoformat(),
            "baseline_period": f"{self.window_days} days",
            "current_period": "24 hours",
            "baseline_metrics": self.baseline_metrics,
            "current_metrics": {
                "sample_size": len(current_data),
                "accuracy": current_accuracy,
                "avg_confidence": current_confidence,
                "error_rate": current_error_rate,
                "hallucination_rate": current_hallucination_rate,
                "avg_response_time": current_response_time
            },
            "drift_details": drift_details
        }
        
        if drift_detected:
            logger.warning(f"Model drift detected: {len(drift_details)} metrics changed")
            
            # Send alert
            from .alert_manager import get_alert_manager
            alert_manager = get_alert_manager()
            
            severity_counts = defaultdict(int)
            for detail in drift_details:
                severity_counts[detail["severity"]] += 1
            
            alert_manager.capture_message(
                f"AI Model Drift Detected: {severity_counts['high']} high, {severity_counts['medium']} medium severity changes",
                level="warning",
                context={"drift_report": report}
            )
        
        return drift_detected, report
    
    def get_drift_history(self, days: int = 30) -> List[Dict]:
        """
        Get historical drift detection results.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of drift reports
        """
        # This would typically be stored in a database
        # For now, return empty list (would need to persist drift reports)
        return []


# Global drift detector instance
_drift_detector: Optional[ModelDriftDetector] = None


def get_drift_detector() -> ModelDriftDetector:
    """Get the global drift detector instance."""
    global _drift_detector
    if _drift_detector is None:
        _drift_detector = ModelDriftDetector()
    return _drift_detector

