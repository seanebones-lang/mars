"""
MLflow Setup and Configuration for AgentGuard Experimentation
Provides baseline tracking and A/B testing infrastructure for hallucination detection.

October 2025 Enhancement for systematic model improvement tracking.
"""

import os
import logging
import mlflow
import mlflow.sklearn
import mlflow.pytorch
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from pathlib import Path
import numpy as np
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ExperimentConfig:
    """Configuration for MLflow experiments."""
    experiment_name: str
    description: str
    tags: Dict[str, str]
    artifact_location: Optional[str] = None


@dataclass
class BaselineMetrics:
    """Baseline metrics for comparison."""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    false_positive_rate: float
    false_negative_rate: float
    latency_ms: float
    timestamp: str


class MLflowManager:
    """
    MLflow manager for AgentGuard experimentation and tracking.
    
    Features:
    - Baseline tracking for accuracy improvements
    - A/B testing infrastructure for model comparisons
    - Experiment management for different configurations
    - Artifact logging for model versions and datasets
    """
    
    def __init__(self, tracking_uri: str = None, experiment_name: str = "agentguard-hallucination-detection"):
        """
        Initialize MLflow manager.
        
        Args:
            tracking_uri: MLflow tracking server URI (defaults to local)
            experiment_name: Name of the main experiment
        """
        # Set tracking URI
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
        else:
            # Default to local file store
            tracking_dir = Path("mlruns")
            tracking_dir.mkdir(exist_ok=True)
            mlflow.set_tracking_uri(f"file://{tracking_dir.absolute()}")
        
        self.experiment_name = experiment_name
        self.experiment_id = self._setup_experiment()
        
        logger.info(f"MLflow initialized with experiment: {experiment_name}")
        logger.info(f"Tracking URI: {mlflow.get_tracking_uri()}")

    def _setup_experiment(self) -> str:
        """Setup or get existing experiment."""
        try:
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if experiment:
                experiment_id = experiment.experiment_id
                logger.info(f"Using existing experiment: {self.experiment_name} (ID: {experiment_id})")
            else:
                experiment_id = mlflow.create_experiment(
                    name=self.experiment_name,
                    tags={
                        "project": "AgentGuard",
                        "version": "2025.10",
                        "purpose": "hallucination-detection",
                        "created_at": datetime.now().isoformat()
                    }
                )
                logger.info(f"Created new experiment: {self.experiment_name} (ID: {experiment_id})")
            
            mlflow.set_experiment(self.experiment_name)
            return experiment_id
            
        except Exception as e:
            logger.error(f"Failed to setup experiment: {e}")
            raise

    def log_baseline_metrics(self, metrics: BaselineMetrics, model_version: str = "baseline") -> str:
        """
        Log baseline metrics for comparison.
        
        Args:
            metrics: BaselineMetrics object with performance data
            model_version: Version identifier for the model
            
        Returns:
            Run ID for the logged baseline
        """
        with mlflow.start_run(run_name=f"baseline-{model_version}") as run:
            # Log metrics
            mlflow.log_metric("accuracy", metrics.accuracy)
            mlflow.log_metric("precision", metrics.precision)
            mlflow.log_metric("recall", metrics.recall)
            mlflow.log_metric("f1_score", metrics.f1_score)
            mlflow.log_metric("false_positive_rate", metrics.false_positive_rate)
            mlflow.log_metric("false_negative_rate", metrics.false_negative_rate)
            mlflow.log_metric("latency_ms", metrics.latency_ms)
            
            # Log parameters
            mlflow.log_param("model_version", model_version)
            mlflow.log_param("baseline_timestamp", metrics.timestamp)
            mlflow.log_param("run_type", "baseline")
            
            # Log tags
            mlflow.set_tag("model_type", "baseline")
            mlflow.set_tag("evaluation_date", datetime.now().strftime("%Y-%m-%d"))
            
            # Save metrics as artifact
            metrics_dict = asdict(metrics)
            metrics_file = f"baseline_metrics_{model_version}.json"
            with open(metrics_file, 'w') as f:
                json.dump(metrics_dict, f, indent=2)
            mlflow.log_artifact(metrics_file)
            os.remove(metrics_file)  # Clean up temp file
            
            logger.info(f"Logged baseline metrics for {model_version}: {run.info.run_id}")
            return run.info.run_id

    def start_ab_test(self, 
                     test_name: str, 
                     variant_a_config: Dict[str, Any], 
                     variant_b_config: Dict[str, Any],
                     description: str = "") -> Dict[str, str]:
        """
        Start an A/B test between two model configurations.
        
        Args:
            test_name: Name of the A/B test
            variant_a_config: Configuration for variant A (control)
            variant_b_config: Configuration for variant B (treatment)
            description: Description of the test
            
        Returns:
            Dict with run IDs for both variants
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Start variant A (control)
        with mlflow.start_run(run_name=f"{test_name}_variant_a_{timestamp}") as run_a:
            mlflow.log_params(variant_a_config)
            mlflow.log_param("ab_test_name", test_name)
            mlflow.log_param("variant", "A")
            mlflow.log_param("variant_type", "control")
            mlflow.set_tag("ab_test", test_name)
            mlflow.set_tag("variant", "A")
            mlflow.set_tag("description", description)
            run_a_id = run_a.info.run_id
        
        # Start variant B (treatment)
        with mlflow.start_run(run_name=f"{test_name}_variant_b_{timestamp}") as run_b:
            mlflow.log_params(variant_b_config)
            mlflow.log_param("ab_test_name", test_name)
            mlflow.log_param("variant", "B")
            mlflow.log_param("variant_type", "treatment")
            mlflow.set_tag("ab_test", test_name)
            mlflow.set_tag("variant", "B")
            mlflow.set_tag("description", description)
            run_b_id = run_b.info.run_id
        
        logger.info(f"Started A/B test '{test_name}': A={run_a_id}, B={run_b_id}")
        
        return {
            "test_name": test_name,
            "variant_a_run_id": run_a_id,
            "variant_b_run_id": run_b_id,
            "timestamp": timestamp
        }

    def log_ab_test_results(self, 
                           run_id: str, 
                           metrics: Dict[str, float], 
                           additional_data: Dict[str, Any] = None) -> None:
        """
        Log results for an A/B test variant.
        
        Args:
            run_id: MLflow run ID for the variant
            metrics: Performance metrics to log
            additional_data: Additional data to log as parameters/artifacts
        """
        with mlflow.start_run(run_id=run_id):
            # Log metrics
            for metric_name, value in metrics.items():
                mlflow.log_metric(metric_name, value)
            
            # Log additional parameters
            if additional_data:
                for key, value in additional_data.items():
                    if isinstance(value, (int, float, str, bool)):
                        mlflow.log_param(key, value)
                    else:
                        # Log complex objects as artifacts
                        artifact_file = f"{key}.json"
                        with open(artifact_file, 'w') as f:
                            json.dump(value, f, indent=2, default=str)
                        mlflow.log_artifact(artifact_file)
                        os.remove(artifact_file)
            
            logger.info(f"Logged A/B test results for run: {run_id}")

    def compare_ab_test_results(self, test_name: str) -> Dict[str, Any]:
        """
        Compare results between A/B test variants.
        
        Args:
            test_name: Name of the A/B test to analyze
            
        Returns:
            Dict with comparison results and statistical significance
        """
        # Search for runs with the test name
        experiment = mlflow.get_experiment_by_name(self.experiment_name)
        runs = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string=f"tags.ab_test = '{test_name}'"
        )
        
        if len(runs) < 2:
            logger.warning(f"Not enough runs found for A/B test: {test_name}")
            return {"error": "Insufficient data for comparison"}
        
        # Separate variants
        variant_a_runs = runs[runs['tags.variant'] == 'A']
        variant_b_runs = runs[runs['tags.variant'] == 'B']
        
        if len(variant_a_runs) == 0 or len(variant_b_runs) == 0:
            logger.warning(f"Missing variant data for A/B test: {test_name}")
            return {"error": "Missing variant data"}
        
        # Compare key metrics
        comparison_results = {
            "test_name": test_name,
            "variant_a_runs": len(variant_a_runs),
            "variant_b_runs": len(variant_b_runs),
            "metrics_comparison": {}
        }
        
        # Compare common metrics
        common_metrics = ['accuracy', 'f1_score', 'latency_ms', 'false_positive_rate']
        
        for metric in common_metrics:
            if f"metrics.{metric}" in variant_a_runs.columns and f"metrics.{metric}" in variant_b_runs.columns:
                a_values = variant_a_runs[f"metrics.{metric}"].dropna()
                b_values = variant_b_runs[f"metrics.{metric}"].dropna()
                
                if len(a_values) > 0 and len(b_values) > 0:
                    comparison_results["metrics_comparison"][metric] = {
                        "variant_a_mean": float(a_values.mean()),
                        "variant_b_mean": float(b_values.mean()),
                        "improvement": float((b_values.mean() - a_values.mean()) / a_values.mean() * 100),
                        "variant_a_std": float(a_values.std()),
                        "variant_b_std": float(b_values.std())
                    }
        
        logger.info(f"Completed A/B test comparison for: {test_name}")
        return comparison_results

    def log_model_artifact(self, 
                          model: Any, 
                          model_name: str, 
                          model_type: str = "sklearn",
                          additional_files: List[str] = None) -> None:
        """
        Log model as MLflow artifact.
        
        Args:
            model: Trained model object
            model_name: Name for the model
            model_type: Type of model (sklearn, pytorch, etc.)
            additional_files: Additional files to log with the model
        """
        try:
            if model_type == "sklearn":
                mlflow.sklearn.log_model(model, model_name)
            elif model_type == "pytorch":
                mlflow.pytorch.log_model(model, model_name)
            else:
                # Generic pickle logging
                import pickle
                model_file = f"{model_name}.pkl"
                with open(model_file, 'wb') as f:
                    pickle.dump(model, f)
                mlflow.log_artifact(model_file)
                os.remove(model_file)
            
            # Log additional files
            if additional_files:
                for file_path in additional_files:
                    if os.path.exists(file_path):
                        mlflow.log_artifact(file_path)
            
            logger.info(f"Logged model artifact: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to log model artifact: {e}")

    def create_experiment_report(self, experiment_name: str = None) -> Dict[str, Any]:
        """
        Generate comprehensive experiment report.
        
        Args:
            experiment_name: Name of experiment to report on (defaults to current)
            
        Returns:
            Dict with experiment summary and insights
        """
        if experiment_name is None:
            experiment_name = self.experiment_name
        
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if not experiment:
            return {"error": f"Experiment not found: {experiment_name}"}
        
        # Get all runs
        runs_df = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
        
        if len(runs_df) == 0:
            return {"error": "No runs found in experiment"}
        
        # Generate report
        report = {
            "experiment_name": experiment_name,
            "experiment_id": experiment.experiment_id,
            "total_runs": len(runs_df),
            "date_range": {
                "start": runs_df['start_time'].min().isoformat() if 'start_time' in runs_df.columns else None,
                "end": runs_df['start_time'].max().isoformat() if 'start_time' in runs_df.columns else None
            },
            "metrics_summary": {},
            "best_runs": {},
            "ab_tests": []
        }
        
        # Metrics summary
        metric_columns = [col for col in runs_df.columns if col.startswith('metrics.')]
        for col in metric_columns:
            metric_name = col.replace('metrics.', '')
            values = runs_df[col].dropna()
            if len(values) > 0:
                report["metrics_summary"][metric_name] = {
                    "mean": float(values.mean()),
                    "std": float(values.std()),
                    "min": float(values.min()),
                    "max": float(values.max()),
                    "count": len(values)
                }
        
        # Best runs by key metrics
        key_metrics = ['accuracy', 'f1_score']
        for metric in key_metrics:
            col_name = f"metrics.{metric}"
            if col_name in runs_df.columns:
                best_run = runs_df.loc[runs_df[col_name].idxmax()]
                report["best_runs"][metric] = {
                    "run_id": best_run['run_id'],
                    "value": float(best_run[col_name]),
                    "run_name": best_run.get('tags.mlflow.runName', 'Unknown')
                }
        
        # A/B tests summary
        ab_test_runs = runs_df[runs_df['tags.ab_test'].notna()]
        if len(ab_test_runs) > 0:
            ab_tests = ab_test_runs['tags.ab_test'].unique()
            for test_name in ab_tests:
                test_comparison = self.compare_ab_test_results(test_name)
                if "error" not in test_comparison:
                    report["ab_tests"].append(test_comparison)
        
        logger.info(f"Generated experiment report for: {experiment_name}")
        return report


def setup_agentguard_experiments() -> MLflowManager:
    """
    Setup AgentGuard MLflow experiments with predefined configurations.
    
    Returns:
        Configured MLflowManager instance
    """
    manager = MLflowManager()
    
    # Create baseline experiment if needed
    baseline_config = ExperimentConfig(
        experiment_name="agentguard-baselines",
        description="Baseline performance tracking for AgentGuard hallucination detection",
        tags={
            "project": "AgentGuard",
            "type": "baseline",
            "created": datetime.now().isoformat()
        }
    )
    
    # Create A/B testing experiment
    ab_test_config = ExperimentConfig(
        experiment_name="agentguard-ab-tests",
        description="A/B testing for AgentGuard model improvements",
        tags={
            "project": "AgentGuard",
            "type": "ab_test",
            "created": datetime.now().isoformat()
        }
    )
    
    logger.info("AgentGuard MLflow experiments setup complete")
    return manager


if __name__ == "__main__":
    # Example usage
    manager = setup_agentguard_experiments()
    
    # Log sample baseline
    baseline_metrics = BaselineMetrics(
        accuracy=0.89,
        precision=0.87,
        recall=0.91,
        f1_score=0.89,
        false_positive_rate=0.13,
        false_negative_rate=0.09,
        latency_ms=150.5,
        timestamp=datetime.now().isoformat()
    )
    
    run_id = manager.log_baseline_metrics(baseline_metrics, "v1.0.0")
    print(f"Logged baseline with run ID: {run_id}")
    
    # Generate report
    report = manager.create_experiment_report()
    print(f"Experiment report: {json.dumps(report, indent=2)}")
