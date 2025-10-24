"""
Synthetic Data Generator for Hallucination Detection Training
Generates 1,000+ task-specific hallucination examples for AgentGuard training.

Based on October 2025 research on controlled synthetic data generation
for hallucination detection improvement.
"""

import json
import random
import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class HallucinationExample:
    """Structured hallucination example for training."""
    id: str
    domain: str
    agent_output: str
    ground_truth: str
    hallucination_type: str
    severity: str  # low, medium, high
    confidence_score: float  # Expected detection confidence
    metadata: Dict
    created_at: str


class SyntheticDataGenerator:
    """
    Generate synthetic hallucination examples across multiple domains.
    
    Targets:
    - 1,000+ examples across IT, retail, healthcare, finance domains
    - Multiple hallucination types: factual, temporal, numerical, contextual
    - Balanced severity distribution for robust training
    """
    
    def __init__(self, output_dir: str = "data/synthetic"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Hallucination patterns based on 2025 research
        self.hallucination_patterns = {
            "factual_error": {
                "templates": [
                    "The capital of {country} is {wrong_capital}",
                    "{company} was founded in {wrong_year}",
                    "{technology} was invented by {wrong_inventor}",
                    "The population of {city} is {wrong_population}",
                ],
                "severity_weights": {"low": 0.3, "medium": 0.5, "high": 0.2}
            },
            "temporal_confusion": {
                "templates": [
                    "This event happened {wrong_timeframe} ago",
                    "The {technology} was released {wrong_date}",
                    "According to {wrong_recent_date} reports",
                    "Last {wrong_period}, the company announced",
                ],
                "severity_weights": {"low": 0.4, "medium": 0.4, "high": 0.2}
            },
            "numerical_hallucination": {
                "templates": [
                    "The system processes {wrong_number} requests per second",
                    "Our accuracy improved by {wrong_percentage}%",
                    "The database contains {wrong_count} records",
                    "Response time decreased to {wrong_latency}ms",
                ],
                "severity_weights": {"low": 0.2, "medium": 0.5, "high": 0.3}
            },
            "contextual_fabrication": {
                "templates": [
                    "Based on our {nonexistent_study}, we found",
                    "According to {fake_expert}, the best practice is",
                    "The {nonexistent_feature} allows users to",
                    "Our {fake_integration} with {real_service} enables",
                ],
                "severity_weights": {"low": 0.1, "medium": 0.4, "high": 0.5}
            }
        }
        
        # Domain-specific knowledge bases
        self.domain_knowledge = {
            "it_support": {
                "entities": ["servers", "databases", "APIs", "microservices", "containers"],
                "metrics": ["latency", "throughput", "uptime", "error rate"],
                "technologies": ["Kubernetes", "Docker", "Redis", "PostgreSQL", "FastAPI"],
                "common_issues": ["memory leaks", "connection timeouts", "SSL errors"]
            },
            "retail": {
                "entities": ["products", "customers", "orders", "inventory", "payments"],
                "metrics": ["conversion rate", "cart abandonment", "customer satisfaction"],
                "technologies": ["Shopify", "Stripe", "inventory management", "CRM"],
                "common_issues": ["payment failures", "stock shortages", "shipping delays"]
            },
            "healthcare": {
                "entities": ["patients", "diagnoses", "treatments", "medications", "procedures"],
                "metrics": ["patient outcomes", "treatment efficacy", "safety scores"],
                "technologies": ["EHR systems", "HIPAA compliance", "medical devices"],
                "common_issues": ["data privacy", "interoperability", "regulatory compliance"]
            },
            "finance": {
                "entities": ["transactions", "accounts", "investments", "portfolios", "risks"],
                "metrics": ["ROI", "volatility", "liquidity", "compliance scores"],
                "technologies": ["blockchain", "algorithmic trading", "risk management"],
                "common_issues": ["fraud detection", "regulatory reporting", "market volatility"]
            }
        }

    def generate_factual_error(self, domain: str) -> HallucinationExample:
        """Generate factual error hallucination."""
        domain_data = self.domain_knowledge[domain]
        
        # Create factual error about technology or metric
        technology = random.choice(domain_data["technologies"])
        wrong_fact = f"{technology} supports up to 1 million concurrent users"
        correct_fact = f"{technology} typically supports thousands of concurrent users"
        
        if domain == "it_support":
            agent_output = f"Our {technology} deployment can handle {random.randint(500000, 2000000)} concurrent connections without any performance degradation."
            ground_truth = f"Standard {technology} deployments typically handle {random.randint(1000, 50000)} concurrent connections effectively."
        elif domain == "retail":
            agent_output = f"Our {technology} integration processes {random.randint(100000, 500000)} transactions per second."
            ground_truth = f"Typical {technology} integrations process {random.randint(100, 5000)} transactions per second."
        else:
            agent_output = wrong_fact
            ground_truth = correct_fact
        
        severity = np.random.choice(
            list(self.hallucination_patterns["factual_error"]["severity_weights"].keys()),
            p=list(self.hallucination_patterns["factual_error"]["severity_weights"].values())
        )
        
        return HallucinationExample(
            id=f"fact_error_{domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}",
            domain=domain,
            agent_output=agent_output,
            ground_truth=ground_truth,
            hallucination_type="factual_error",
            severity=severity,
            confidence_score=0.8 if severity == "high" else 0.6 if severity == "medium" else 0.4,
            metadata={
                "technology": technology,
                "error_type": "capability_exaggeration",
                "domain_specific": True
            },
            created_at=datetime.now().isoformat()
        )

    def generate_numerical_hallucination(self, domain: str) -> HallucinationExample:
        """Generate numerical hallucination with wrong metrics."""
        domain_data = self.domain_knowledge[domain]
        metric = random.choice(domain_data["metrics"])
        
        # Generate realistic but wrong numbers
        if "percentage" in metric or "rate" in metric:
            wrong_value = random.randint(150, 300)  # Impossible percentages
            correct_value = random.randint(5, 95)
            unit = "%"
        elif "latency" in metric or "time" in metric:
            wrong_value = random.uniform(0.001, 0.1)  # Impossibly fast
            correct_value = random.randint(50, 500)
            unit = "ms"
        else:
            wrong_value = random.randint(10000000, 100000000)  # Exaggerated numbers
            correct_value = random.randint(1000, 50000)
            unit = ""
        
        agent_output = f"Our system achieves {wrong_value}{unit} {metric}, which is industry-leading performance."
        ground_truth = f"Typical systems achieve {correct_value}{unit} {metric} in production environments."
        
        severity = np.random.choice(
            list(self.hallucination_patterns["numerical_hallucination"]["severity_weights"].keys()),
            p=list(self.hallucination_patterns["numerical_hallucination"]["severity_weights"].values())
        )
        
        return HallucinationExample(
            id=f"num_hall_{domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}",
            domain=domain,
            agent_output=agent_output,
            ground_truth=ground_truth,
            hallucination_type="numerical_hallucination",
            severity=severity,
            confidence_score=0.9 if severity == "high" else 0.7 if severity == "medium" else 0.5,
            metadata={
                "metric": metric,
                "wrong_value": wrong_value,
                "correct_value": correct_value,
                "unit": unit
            },
            created_at=datetime.now().isoformat()
        )

    def generate_contextual_fabrication(self, domain: str) -> HallucinationExample:
        """Generate contextual fabrication with non-existent features."""
        domain_data = self.domain_knowledge[domain]
        
        # Create non-existent features or integrations
        fake_features = {
            "it_support": ["quantum load balancing", "AI-powered auto-healing", "telepathic monitoring"],
            "retail": ["mind-reading recommendations", "time-travel delivery", "emotion-based pricing"],
            "healthcare": ["DNA-based instant diagnosis", "quantum healing protocols", "telepathic patient monitoring"],
            "finance": ["crystal ball market prediction", "quantum encryption wallets", "time-dilated trading"]
        }
        
        fake_feature = random.choice(fake_features[domain])
        real_technology = random.choice(domain_data["technologies"])
        
        agent_output = f"Our new {fake_feature} feature integrates seamlessly with {real_technology} to provide unprecedented capabilities that no other solution offers."
        ground_truth = f"Standard {real_technology} integrations provide conventional monitoring and management capabilities."
        
        severity = np.random.choice(
            list(self.hallucination_patterns["contextual_fabrication"]["severity_weights"].keys()),
            p=list(self.hallucination_patterns["contextual_fabrication"]["severity_weights"].values())
        )
        
        return HallucinationExample(
            id=f"ctx_fab_{domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}",
            domain=domain,
            agent_output=agent_output,
            ground_truth=ground_truth,
            hallucination_type="contextual_fabrication",
            severity=severity,
            confidence_score=0.95 if severity == "high" else 0.8 if severity == "medium" else 0.6,
            metadata={
                "fake_feature": fake_feature,
                "real_technology": real_technology,
                "fabrication_type": "non_existent_capability"
            },
            created_at=datetime.now().isoformat()
        )

    def generate_temporal_confusion(self, domain: str) -> HallucinationExample:
        """Generate temporal confusion with wrong dates/timeframes."""
        domain_data = self.domain_knowledge[domain]
        technology = random.choice(domain_data["technologies"])
        
        # Generate wrong temporal references
        wrong_timeframes = ["yesterday", "last week", "next month", "in 2030", "5 years ago"]
        correct_timeframes = ["several months ago", "last year", "recently", "in the past", "previously"]
        
        wrong_time = random.choice(wrong_timeframes)
        correct_time = random.choice(correct_timeframes)
        
        agent_output = f"The {technology} update was released {wrong_time} and includes revolutionary features that transform the industry."
        ground_truth = f"The {technology} update was released {correct_time} and includes incremental improvements."
        
        severity = np.random.choice(
            list(self.hallucination_patterns["temporal_confusion"]["severity_weights"].keys()),
            p=list(self.hallucination_patterns["temporal_confusion"]["severity_weights"].values())
        )
        
        return HallucinationExample(
            id=f"temp_conf_{domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}",
            domain=domain,
            agent_output=agent_output,
            ground_truth=ground_truth,
            hallucination_type="temporal_confusion",
            severity=severity,
            confidence_score=0.7 if severity == "high" else 0.5 if severity == "medium" else 0.3,
            metadata={
                "technology": technology,
                "wrong_timeframe": wrong_time,
                "correct_timeframe": correct_time
            },
            created_at=datetime.now().isoformat()
        )

    def generate_dataset(self, total_examples: int = 1200) -> List[HallucinationExample]:
        """
        Generate complete synthetic dataset with balanced distribution.
        
        Args:
            total_examples: Total number of examples to generate
            
        Returns:
            List of HallucinationExample objects
        """
        examples = []
        domains = list(self.domain_knowledge.keys())
        hallucination_types = ["factual_error", "numerical_hallucination", 
                             "contextual_fabrication", "temporal_confusion"]
        
        examples_per_domain = total_examples // len(domains)
        examples_per_type = examples_per_domain // len(hallucination_types)
        
        logger.info(f"Generating {total_examples} synthetic examples...")
        logger.info(f"Distribution: {examples_per_domain} per domain, {examples_per_type} per type")
        
        for domain in domains:
            for hall_type in hallucination_types:
                for _ in range(examples_per_type):
                    if hall_type == "factual_error":
                        example = self.generate_factual_error(domain)
                    elif hall_type == "numerical_hallucination":
                        example = self.generate_numerical_hallucination(domain)
                    elif hall_type == "contextual_fabrication":
                        example = self.generate_contextual_fabrication(domain)
                    elif hall_type == "temporal_confusion":
                        example = self.generate_temporal_confusion(domain)
                    
                    examples.append(example)
        
        # Add some additional random examples to reach target
        remaining = total_examples - len(examples)
        for _ in range(remaining):
            domain = random.choice(domains)
            hall_type = random.choice(hallucination_types)
            
            if hall_type == "factual_error":
                example = self.generate_factual_error(domain)
            elif hall_type == "numerical_hallucination":
                example = self.generate_numerical_hallucination(domain)
            elif hall_type == "contextual_fabrication":
                example = self.generate_contextual_fabrication(domain)
            elif hall_type == "temporal_confusion":
                example = self.generate_temporal_confusion(domain)
            
            examples.append(example)
        
        logger.info(f"Generated {len(examples)} synthetic hallucination examples")
        return examples

    def save_dataset(self, examples: List[HallucinationExample], filename: str = None) -> str:
        """Save dataset to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"synthetic_hallucinations_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        # Convert to JSON-serializable format
        data = {
            "metadata": {
                "total_examples": len(examples),
                "generated_at": datetime.now().isoformat(),
                "generator_version": "1.0.0",
                "domains": list(self.domain_knowledge.keys()),
                "hallucination_types": list(self.hallucination_patterns.keys())
            },
            "examples": [asdict(example) for example in examples]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(examples)} examples to {filepath}")
        return str(filepath)

    def load_dataset(self, filepath: str) -> List[HallucinationExample]:
        """Load dataset from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        examples = []
        for example_data in data["examples"]:
            example = HallucinationExample(**example_data)
            examples.append(example)
        
        logger.info(f"Loaded {len(examples)} examples from {filepath}")
        return examples

    def get_statistics(self, examples: List[HallucinationExample]) -> Dict:
        """Get dataset statistics."""
        stats = {
            "total_examples": len(examples),
            "by_domain": {},
            "by_type": {},
            "by_severity": {},
            "confidence_distribution": {}
        }
        
        for example in examples:
            # Domain distribution
            if example.domain not in stats["by_domain"]:
                stats["by_domain"][example.domain] = 0
            stats["by_domain"][example.domain] += 1
            
            # Type distribution
            if example.hallucination_type not in stats["by_type"]:
                stats["by_type"][example.hallucination_type] = 0
            stats["by_type"][example.hallucination_type] += 1
            
            # Severity distribution
            if example.severity not in stats["by_severity"]:
                stats["by_severity"][example.severity] = 0
            stats["by_severity"][example.severity] += 1
        
        # Confidence score distribution
        confidence_scores = [example.confidence_score for example in examples]
        stats["confidence_distribution"] = {
            "mean": np.mean(confidence_scores),
            "std": np.std(confidence_scores),
            "min": np.min(confidence_scores),
            "max": np.max(confidence_scores)
        }
        
        return stats


def main():
    """Generate and save synthetic dataset."""
    generator = SyntheticDataGenerator()
    
    # Generate dataset
    examples = generator.generate_dataset(total_examples=1200)
    
    # Save to file
    filepath = generator.save_dataset(examples)
    
    # Print statistics
    stats = generator.get_statistics(examples)
    print("\nDataset Statistics:")
    print(f"Total Examples: {stats['total_examples']}")
    print(f"By Domain: {stats['by_domain']}")
    print(f"By Type: {stats['by_type']}")
    print(f"By Severity: {stats['by_severity']}")
    print(f"Confidence Distribution: {stats['confidence_distribution']}")
    print(f"\nDataset saved to: {filepath}")


if __name__ == "__main__":
    main()
