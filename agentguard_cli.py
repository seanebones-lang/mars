#!/usr/bin/env python3
"""
AgentGuard CLI - Command-line interface for batch hallucination detection testing.

Usage:
    python agentguard_cli.py --input data/sample_scenarios.json --output results.json
    python agentguard_cli.py --input single_test.json --multi-turn --verbose
"""

import argparse
import asyncio
import json
import sys
import os
from pathlib import Path
from typing import List, Dict
import logging
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.judges.ensemble_judge import EnsembleJudge
from src.models.schemas import AgentTestRequest, HallucinationReport
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AgentGuardCLI:
    """Command-line interface for AgentGuard hallucination detection."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.setup_logging()
        self.claude_api_key = os.getenv("CLAUDE_API_KEY")
        
        if not self.claude_api_key:
            self.logger.error("CLAUDE_API_KEY not set in environment")
            raise ValueError("CLAUDE_API_KEY must be configured")
    
    def setup_logging(self):
        """Configure logging based on verbosity."""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        self.logger = logging.getLogger(__name__)
    
    def load_test_scenarios(self, input_path: str) -> List[Dict]:
        """
        Load test scenarios from JSON file.
        
        Args:
            input_path: Path to input JSON file
            
        Returns:
            List of test scenario dictionaries
        """
        try:
            with open(input_path, 'r') as f:
                data = json.load(f)
            
            # Handle both single object and array
            if isinstance(data, dict):
                data = [data]
            
            self.logger.info(f"Loaded {len(data)} test scenario(s) from {input_path}")
            return data
        
        except FileNotFoundError:
            self.logger.error(f"Input file not found: {input_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in input file: {e}")
            sys.exit(1)
    
    async def evaluate_scenario(
        self,
        scenario: Dict,
        judge: EnsembleJudge
    ) -> Dict:
        """
        Evaluate a single test scenario.
        
        Args:
            scenario: Test scenario dictionary
            judge: EnsembleJudge instance
            
        Returns:
            Dictionary with scenario details and evaluation results
        """
        scenario_id = scenario.get("id", "unknown")
        self.logger.info(f"Evaluating scenario: {scenario_id}")
        
        try:
            # Build request
            request = AgentTestRequest(
                agent_output=scenario["agent_output"],
                ground_truth=scenario["ground_truth"],
                conversation_history=scenario.get("conversation_history", [])
            )
            
            # Perform evaluation
            start_time = datetime.now()
            report: HallucinationReport = await judge.evaluate(request)
            end_time = datetime.now()
            latency = (end_time - start_time).total_seconds()
            
            # Build result
            result = {
                "scenario_id": scenario_id,
                "category": scenario.get("category", "unknown"),
                "expected_hallucination": scenario.get("expected_hallucination"),
                "hallucination_risk": report.hallucination_risk,
                "details": report.details,
                "confidence_interval": report.confidence_interval,
                "uncertainty": report.uncertainty,
                "latency_seconds": latency,
                "timestamp": datetime.now().isoformat(),
                "notes": scenario.get("notes", "")
            }
            
            # Log summary
            detected = report.hallucination_risk > 0.5
            expected = scenario.get("expected_hallucination", None)
            match = "✓" if (detected == expected) else "✗"
            
            self.logger.info(
                f"  {match} Risk: {report.hallucination_risk:.3f}, "
                f"Uncertainty: {report.uncertainty:.3f}, "
                f"Latency: {latency:.2f}s"
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error evaluating scenario {scenario_id}: {e}")
            return {
                "scenario_id": scenario_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def run_batch_evaluation(
        self,
        scenarios: List[Dict],
        output_path: str
    ):
        """
        Run batch evaluation on all scenarios.
        
        Args:
            scenarios: List of test scenarios
            output_path: Path to output JSON file
        """
        self.logger.info(f"Starting batch evaluation of {len(scenarios)} scenarios")
        
        # Initialize judge
        judge = EnsembleJudge(self.claude_api_key)
        
        # Evaluate all scenarios
        results = []
        for i, scenario in enumerate(scenarios, 1):
            self.logger.info(f"\n[{i}/{len(scenarios)}] Processing scenario...")
            result = await self.evaluate_scenario(scenario, judge)
            results.append(result)
        
        # Calculate summary statistics
        summary = self.calculate_summary(results)
        
        # Save results
        output_data = {
            "summary": summary,
            "results": results,
            "metadata": {
                "total_scenarios": len(scenarios),
                "timestamp": datetime.now().isoformat(),
                "agentguard_version": "0.1.0"
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        self.logger.info(f"\n✓ Results saved to: {output_path}")
        self.print_summary(summary)
    
    def calculate_summary(self, results: List[Dict]) -> Dict:
        """Calculate summary statistics from results."""
        successful = [r for r in results if "error" not in r]
        failed = [r for r in results if "error" in r]
        
        if not successful:
            return {
                "total": len(results),
                "successful": 0,
                "failed": len(failed),
                "error": "No successful evaluations"
            }
        
        # Accuracy metrics
        detected_hallucinations = [
            r for r in successful
            if r["hallucination_risk"] > 0.5
        ]
        expected_hallucinations = [
            r for r in successful
            if r.get("expected_hallucination") is True
        ]
        
        # Matches (correct predictions)
        matches = [
            r for r in successful
            if r.get("expected_hallucination") is not None and
            (r["hallucination_risk"] > 0.5) == r["expected_hallucination"]
        ]
        
        # Latency metrics
        latencies = [r["latency_seconds"] for r in successful]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        max_latency = max(latencies) if latencies else 0
        
        # Uncertainty metrics
        uncertainties = [r["uncertainty"] for r in successful]
        avg_uncertainty = sum(uncertainties) / len(uncertainties) if uncertainties else 0
        high_uncertainty = [r for r in successful if r["uncertainty"] > 0.3]
        
        # Accuracy
        accuracy = len(matches) / len(successful) if successful else 0
        
        return {
            "total": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "detected_hallucinations": len(detected_hallucinations),
            "expected_hallucinations": len(expected_hallucinations),
            "correct_predictions": len(matches),
            "accuracy": accuracy,
            "avg_latency_seconds": avg_latency,
            "max_latency_seconds": max_latency,
            "avg_uncertainty": avg_uncertainty,
            "high_uncertainty_count": len(high_uncertainty),
            "target_accuracy_met": accuracy >= 0.92,
            "target_latency_met": avg_latency < 0.5
        }
    
    def print_summary(self, summary: Dict):
        """Print formatted summary to console."""
        print("\n" + "="*60)
        print(" AGENTGUARD BATCH EVALUATION SUMMARY")
        print("="*60)
        print(f"Total Scenarios:        {summary['total']}")
        print(f"Successful:             {summary['successful']}")
        print(f"Failed:                 {summary['failed']}")
        print(f"\nDetection Results:")
        print(f"  Detected Hallucinations: {summary['detected_hallucinations']}")
        print(f"  Expected Hallucinations: {summary['expected_hallucinations']}")
        print(f"  Correct Predictions:     {summary['correct_predictions']}")
        print(f"  Accuracy:                {summary['accuracy']:.1%} {'✓' if summary.get('target_accuracy_met') else '✗'} (target: 92%)")
        print(f"\nPerformance:")
        print(f"  Avg Latency:         {summary['avg_latency_seconds']:.3f}s {'✓' if summary.get('target_latency_met') else '✗'} (target: <0.5s)")
        print(f"  Max Latency:         {summary['max_latency_seconds']:.3f}s")
        print(f"  Avg Uncertainty:     {summary['avg_uncertainty']:.3f}")
        print(f"  High Uncertainty:    {summary['high_uncertainty_count']} (>0.3)")
        print("="*60 + "\n")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AgentGuard CLI - Batch hallucination detection testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate sample scenarios
  python agentguard_cli.py --input data/sample_scenarios.json --output results.json
  
  # Single scenario with verbose output
  python agentguard_cli.py --input test.json --output result.json --verbose
  
  # Multi-turn conversation testing
  python agentguard_cli.py --input conversations.json --multi-turn --output results.json

Input JSON format:
  [
    {
      "id": "test_001",
      "agent_output": "Agent response text",
      "ground_truth": "Expected correct response",
      "conversation_history": ["User: Question", "Agent: Previous response"],
      "expected_hallucination": true,
      "category": "IT Support"
    }
  ]
        """
    )
    
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to input JSON file with test scenarios"
    )
    
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Path to output JSON file for results"
    )
    
    parser.add_argument(
        "--multi-turn",
        action="store_true",
        help="Enable multi-turn conversation support (uses conversation_history field)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging output"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize CLI
        cli = AgentGuardCLI(verbose=args.verbose)
        
        # Load scenarios
        scenarios = cli.load_test_scenarios(args.input)
        
        # Run batch evaluation
        asyncio.run(cli.run_batch_evaluation(scenarios, args.output))
        
        sys.exit(0)
    
    except KeyboardInterrupt:
        print("\n\nEvaluation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

