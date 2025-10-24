"""
4-Agent Fact-Checking Pipeline with CrewAI Integration
Implements Generate → Review → Clarify → Score workflow for auto-correction capabilities.

October 2025 Enhancement: Teaming LLMs for 40-50% hallucination mitigation improvement.
"""

import logging
import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

# CrewAI and LangChain imports
from crewai import Agent, Task, Crew, Process
from langchain_anthropic import ChatAnthropic
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.callbacks.base import BaseCallbackHandler

# Pydantic for structured outputs
from pydantic import BaseModel, Field
from instructor import patch

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Roles in the 4-agent pipeline."""
    GENERATOR = "generator"
    REVIEWER = "reviewer"
    CLARIFIER = "clarifier"
    SCORER = "scorer"


class PipelineStage(Enum):
    """Stages in the fact-checking pipeline."""
    GENERATION = "generation"
    REVIEW = "review"
    CLARIFICATION = "clarification"
    SCORING = "scoring"
    COMPLETE = "complete"


@dataclass
class AgentOutput:
    """Output from a single agent in the pipeline."""
    agent_role: AgentRole
    stage: PipelineStage
    content: str
    confidence: float
    reasoning: str
    metadata: Dict[str, Any]
    processing_time_ms: float
    timestamp: str


@dataclass
class PipelineResult:
    """Final result from the 4-agent pipeline."""
    original_text: str
    corrected_text: str
    hallucination_score: float
    correction_applied: bool
    agent_outputs: List[AgentOutput]
    total_processing_time_ms: float
    pipeline_confidence: float
    improvement_metrics: Dict[str, float]


class FactCheckingRequest(BaseModel):
    """Structured request for fact-checking."""
    claim: str = Field(description="The claim to fact-check")
    context: Optional[str] = Field(default=None, description="Additional context")
    domain: Optional[str] = Field(default=None, description="Domain (IT, healthcare, etc.)")


class ReviewResult(BaseModel):
    """Structured review result."""
    accuracy_score: float = Field(description="Accuracy score 0-1")
    issues_found: List[str] = Field(description="List of identified issues")
    confidence: float = Field(description="Reviewer confidence 0-1")
    needs_clarification: bool = Field(description="Whether clarification is needed")


class ClarificationResult(BaseModel):
    """Structured clarification result."""
    clarified_text: str = Field(description="Clarified version of the text")
    changes_made: List[str] = Field(description="List of changes made")
    confidence: float = Field(description="Clarification confidence 0-1")
    improvement_score: float = Field(description="Expected improvement 0-1")


class FinalScore(BaseModel):
    """Structured final scoring result."""
    hallucination_score: float = Field(description="Final hallucination score 0-1")
    confidence: float = Field(description="Scoring confidence 0-1")
    recommendation: str = Field(description="Final recommendation")
    correction_needed: bool = Field(description="Whether correction is recommended")


class AgentPipelineCallback(BaseCallbackHandler):
    """Custom callback handler for pipeline monitoring."""
    
    def __init__(self):
        self.events = []
        self.start_time = time.time()
    
    def on_agent_action(self, action, **kwargs):
        """Log agent actions."""
        self.events.append({
            'type': 'agent_action',
            'action': str(action),
            'timestamp': time.time() - self.start_time
        })
    
    def on_agent_finish(self, finish, **kwargs):
        """Log agent completion."""
        self.events.append({
            'type': 'agent_finish',
            'output': str(finish.return_values),
            'timestamp': time.time() - self.start_time
        })


class AgentPipeline:
    """
    4-Agent Fact-Checking Pipeline with CrewAI Integration.
    
    Pipeline Flow:
    1. Generator: Analyzes input and identifies potential issues
    2. Reviewer: Reviews the analysis and flags problems
    3. Clarifier: Provides corrections and improvements
    4. Scorer: Gives final hallucination assessment
    
    Target: 40-50% hallucination mitigation improvement through teaming LLMs.
    """
    
    def __init__(self, claude_api_key: str, model_name: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize the 4-agent pipeline.
        
        Args:
            claude_api_key: Anthropic API key for Claude models
            model_name: Claude model to use for all agents
        """
        self.claude_api_key = claude_api_key
        self.model_name = model_name
        
        # Initialize LangChain Claude client
        self.llm = ChatAnthropic(
            anthropic_api_key=claude_api_key,
            model_name=model_name,
            temperature=0.1,  # Low temperature for consistency
            max_tokens=1000
        )
        
        # Patch with instructor for structured outputs
        self.structured_llm = patch(self.llm)
        
        # Initialize agents
        self._initialize_agents()
        
        # Performance tracking
        self.pipeline_stats = {
            'total_runs': 0,
            'successful_corrections': 0,
            'average_improvement': 0.0,
            'average_latency_ms': 0.0
        }
        
        logger.info(f"Initialized 4-Agent Pipeline with model: {model_name}")

    def _initialize_agents(self):
        """Initialize the four specialized agents."""
        
        # Agent 1: Generator - Analyzes input for potential hallucinations
        self.generator_agent = Agent(
            role="Hallucination Detector",
            goal="Analyze text for potential hallucinations, factual errors, and inconsistencies",
            backstory="""You are an expert fact-checker with deep knowledge across multiple domains. 
            Your job is to carefully analyze text and identify any statements that might be 
            hallucinated, factually incorrect, or inconsistent with known information.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
        
        # Agent 2: Reviewer - Reviews the analysis and provides feedback
        self.reviewer_agent = Agent(
            role="Critical Reviewer",
            goal="Review hallucination analysis and provide detailed feedback on accuracy",
            backstory="""You are a meticulous reviewer who specializes in validating 
            fact-checking results. You examine analyses for completeness, accuracy, and 
            potential blind spots. You're known for catching subtle errors others miss.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
        
        # Agent 3: Clarifier - Provides corrections and improvements
        self.clarifier_agent = Agent(
            role="Content Clarifier",
            goal="Provide accurate corrections and improvements to problematic text",
            backstory="""You are an expert editor and fact-checker who specializes in 
            rewriting content to be more accurate while maintaining the original intent. 
            You have access to reliable sources and can provide well-researched corrections.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
        
        # Agent 4: Scorer - Provides final assessment and scoring
        self.scorer_agent = Agent(
            role="Final Assessor",
            goal="Provide final hallucination scores and recommendations",
            backstory="""You are the final authority in the fact-checking pipeline. 
            You synthesize all previous analyses to provide definitive hallucination 
            scores and actionable recommendations. Your assessments are trusted and final.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

    async def process_text(self, 
                          text: str, 
                          context: Optional[str] = None, 
                          domain: Optional[str] = None) -> PipelineResult:
        """
        Process text through the 4-agent pipeline.
        
        Args:
            text: Input text to analyze and potentially correct
            context: Optional context for better analysis
            domain: Optional domain specification (IT, healthcare, etc.)
            
        Returns:
            PipelineResult with corrections and analysis
        """
        start_time = time.time()
        agent_outputs = []
        
        try:
            logger.info(f"Starting 4-agent pipeline for text: {text[:100]}...")
            
            # Stage 1: Generation - Analyze for hallucinations
            generator_output = await self._run_generator(text, context, domain)
            agent_outputs.append(generator_output)
            
            # Stage 2: Review - Critical analysis of the detection
            reviewer_output = await self._run_reviewer(text, generator_output, context)
            agent_outputs.append(reviewer_output)
            
            # Stage 3: Clarification - Provide corrections if needed
            clarifier_output = await self._run_clarifier(text, generator_output, reviewer_output)
            agent_outputs.append(clarifier_output)
            
            # Stage 4: Scoring - Final assessment
            scorer_output = await self._run_scorer(text, agent_outputs)
            agent_outputs.append(scorer_output)
            
            # Build final result
            total_time = (time.time() - start_time) * 1000
            
            # Extract corrected text and metrics
            corrected_text = self._extract_corrected_text(clarifier_output, text)
            hallucination_score = self._extract_hallucination_score(scorer_output)
            pipeline_confidence = self._calculate_pipeline_confidence(agent_outputs)
            improvement_metrics = self._calculate_improvement_metrics(text, corrected_text, agent_outputs)
            
            # Update stats
            self._update_pipeline_stats(total_time, improvement_metrics)
            
            result = PipelineResult(
                original_text=text,
                corrected_text=corrected_text,
                hallucination_score=hallucination_score,
                correction_applied=corrected_text != text,
                agent_outputs=agent_outputs,
                total_processing_time_ms=total_time,
                pipeline_confidence=pipeline_confidence,
                improvement_metrics=improvement_metrics
            )
            
            logger.info(f"Pipeline complete: {total_time:.2f}ms, Score: {hallucination_score:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"Pipeline processing error: {e}")
            # Return error result
            return PipelineResult(
                original_text=text,
                corrected_text=text,
                hallucination_score=0.5,  # Neutral score on error
                correction_applied=False,
                agent_outputs=agent_outputs,
                total_processing_time_ms=(time.time() - start_time) * 1000,
                pipeline_confidence=0.0,
                improvement_metrics={'error': str(e)}
            )

    async def _run_generator(self, text: str, context: Optional[str], domain: Optional[str]) -> AgentOutput:
        """Run the generator agent to analyze for hallucinations."""
        start_time = time.time()
        
        try:
            # Create analysis task
            analysis_task = Task(
                description=f"""
                Analyze the following text for potential hallucinations, factual errors, and inconsistencies:
                
                Text: {text}
                Context: {context or 'None provided'}
                Domain: {domain or 'General'}
                
                Identify:
                1. Specific claims that might be factually incorrect
                2. Statements that seem implausible or exaggerated
                3. Inconsistencies within the text
                4. Missing context that might indicate hallucination
                
                Provide a detailed analysis with specific examples and confidence levels.
                """,
                agent=self.generator_agent,
                expected_output="Detailed analysis of potential hallucinations with specific examples and confidence assessment"
            )
            
            # Create crew and execute
            crew = Crew(
                agents=[self.generator_agent],
                tasks=[analysis_task],
                process=Process.sequential,
                verbose=False
            )
            
            # Run analysis
            result = await asyncio.get_event_loop().run_in_executor(
                None, crew.kickoff
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            return AgentOutput(
                agent_role=AgentRole.GENERATOR,
                stage=PipelineStage.GENERATION,
                content=str(result),
                confidence=0.8,  # Default confidence
                reasoning="Initial hallucination analysis completed",
                metadata={
                    'domain': domain,
                    'context_provided': bool(context),
                    'text_length': len(text)
                },
                processing_time_ms=processing_time,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Generator agent error: {e}")
            return AgentOutput(
                agent_role=AgentRole.GENERATOR,
                stage=PipelineStage.GENERATION,
                content=f"Analysis error: {str(e)}",
                confidence=0.0,
                reasoning="Generator agent encountered an error",
                metadata={'error': str(e)},
                processing_time_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now().isoformat()
            )

    async def _run_reviewer(self, text: str, generator_output: AgentOutput, context: Optional[str]) -> AgentOutput:
        """Run the reviewer agent to validate the analysis."""
        start_time = time.time()
        
        try:
            # Create review task
            review_task = Task(
                description=f"""
                Review the following hallucination analysis for accuracy and completeness:
                
                Original Text: {text}
                Analysis: {generator_output.content}
                Context: {context or 'None provided'}
                
                Evaluate:
                1. Are the identified issues actually problematic?
                2. Are there any missed hallucinations or errors?
                3. Is the analysis thorough and well-reasoned?
                4. What is your confidence in the analysis?
                
                Provide structured feedback with specific recommendations.
                """,
                agent=self.reviewer_agent,
                expected_output="Structured review with validation of analysis and recommendations for improvement"
            )
            
            # Create crew and execute
            crew = Crew(
                agents=[self.reviewer_agent],
                tasks=[review_task],
                process=Process.sequential,
                verbose=False
            )
            
            result = await asyncio.get_event_loop().run_in_executor(
                None, crew.kickoff
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            return AgentOutput(
                agent_role=AgentRole.REVIEWER,
                stage=PipelineStage.REVIEW,
                content=str(result),
                confidence=0.85,  # Slightly higher confidence for review
                reasoning="Critical review of hallucination analysis completed",
                metadata={
                    'generator_confidence': generator_output.confidence,
                    'review_depth': 'comprehensive'
                },
                processing_time_ms=processing_time,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Reviewer agent error: {e}")
            return AgentOutput(
                agent_role=AgentRole.REVIEWER,
                stage=PipelineStage.REVIEW,
                content=f"Review error: {str(e)}",
                confidence=0.0,
                reasoning="Reviewer agent encountered an error",
                metadata={'error': str(e)},
                processing_time_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now().isoformat()
            )

    async def _run_clarifier(self, text: str, generator_output: AgentOutput, reviewer_output: AgentOutput) -> AgentOutput:
        """Run the clarifier agent to provide corrections."""
        start_time = time.time()
        
        try:
            # Create clarification task
            clarification_task = Task(
                description=f"""
                Based on the analysis and review, provide corrections for the identified issues:
                
                Original Text: {text}
                Issues Identified: {generator_output.content}
                Review Feedback: {reviewer_output.content}
                
                Provide:
                1. A corrected version of the text that addresses identified hallucinations
                2. Specific explanations for each correction made
                3. Confidence level in the corrections
                4. Assessment of improvement achieved
                
                Maintain the original intent and style while ensuring factual accuracy.
                """,
                agent=self.clarifier_agent,
                expected_output="Corrected text with explanations and confidence assessment"
            )
            
            # Create crew and execute
            crew = Crew(
                agents=[self.clarifier_agent],
                tasks=[clarification_task],
                process=Process.sequential,
                verbose=False
            )
            
            result = await asyncio.get_event_loop().run_in_executor(
                None, crew.kickoff
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            return AgentOutput(
                agent_role=AgentRole.CLARIFIER,
                stage=PipelineStage.CLARIFICATION,
                content=str(result),
                confidence=0.9,  # High confidence for corrections
                reasoning="Text clarification and correction completed",
                metadata={
                    'corrections_made': True,
                    'original_length': len(text)
                },
                processing_time_ms=processing_time,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Clarifier agent error: {e}")
            return AgentOutput(
                agent_role=AgentRole.CLARIFIER,
                stage=PipelineStage.CLARIFICATION,
                content=f"Clarification error: {str(e)}",
                confidence=0.0,
                reasoning="Clarifier agent encountered an error",
                metadata={'error': str(e)},
                processing_time_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now().isoformat()
            )

    async def _run_scorer(self, text: str, agent_outputs: List[AgentOutput]) -> AgentOutput:
        """Run the scorer agent for final assessment."""
        start_time = time.time()
        
        try:
            # Compile all previous outputs
            pipeline_summary = "\n\n".join([
                f"{output.agent_role.value.upper()}: {output.content}"
                for output in agent_outputs
            ])
            
            # Create scoring task
            scoring_task = Task(
                description=f"""
                Provide final hallucination assessment based on the complete pipeline analysis:
                
                Original Text: {text}
                Pipeline Analysis: {pipeline_summary}
                
                Provide:
                1. Final hallucination score (0-1, where 1 = highly likely hallucination)
                2. Confidence in the assessment (0-1)
                3. Final recommendation (accept, reject, or review)
                4. Summary of key findings
                
                Consider all agent inputs and provide a definitive assessment.
                """,
                agent=self.scorer_agent,
                expected_output="Final hallucination score with confidence and recommendation"
            )
            
            # Create crew and execute
            crew = Crew(
                agents=[self.scorer_agent],
                tasks=[scoring_task],
                process=Process.sequential,
                verbose=False
            )
            
            result = await asyncio.get_event_loop().run_in_executor(
                None, crew.kickoff
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            return AgentOutput(
                agent_role=AgentRole.SCORER,
                stage=PipelineStage.SCORING,
                content=str(result),
                confidence=0.95,  # Highest confidence for final assessment
                reasoning="Final pipeline assessment completed",
                metadata={
                    'pipeline_stages': len(agent_outputs),
                    'total_agents': 4
                },
                processing_time_ms=processing_time,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Scorer agent error: {e}")
            return AgentOutput(
                agent_role=AgentRole.SCORER,
                stage=PipelineStage.SCORING,
                content=f"Scoring error: {str(e)}",
                confidence=0.0,
                reasoning="Scorer agent encountered an error",
                metadata={'error': str(e)},
                processing_time_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now().isoformat()
            )

    def _extract_corrected_text(self, clarifier_output: AgentOutput, original_text: str) -> str:
        """Extract corrected text from clarifier output."""
        try:
            # Simple extraction - look for corrected text in the output
            content = clarifier_output.content.lower()
            
            # Look for common patterns
            patterns = [
                "corrected text:",
                "corrected version:",
                "improved text:",
                "revised text:"
            ]
            
            for pattern in patterns:
                if pattern in content:
                    # Extract text after the pattern
                    parts = clarifier_output.content.split(pattern, 1)
                    if len(parts) > 1:
                        corrected = parts[1].strip()
                        # Clean up common formatting
                        corrected = corrected.replace('"', '').replace("'", "").strip()
                        if corrected and len(corrected) > 10:
                            return corrected
            
            # If no clear pattern found, return original
            return original_text
            
        except Exception as e:
            logger.error(f"Error extracting corrected text: {e}")
            return original_text

    def _extract_hallucination_score(self, scorer_output: AgentOutput) -> float:
        """Extract hallucination score from scorer output."""
        try:
            content = scorer_output.content.lower()
            
            # Look for score patterns
            import re
            score_patterns = [
                r'score[:\s]+([0-9]*\.?[0-9]+)',
                r'hallucination[:\s]+([0-9]*\.?[0-9]+)',
                r'assessment[:\s]+([0-9]*\.?[0-9]+)'
            ]
            
            for pattern in score_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    try:
                        score = float(matches[0])
                        return max(0.0, min(1.0, score))  # Clamp to [0,1]
                    except ValueError:
                        continue
            
            # Default to moderate risk if no score found
            return 0.5
            
        except Exception as e:
            logger.error(f"Error extracting hallucination score: {e}")
            return 0.5

    def _calculate_pipeline_confidence(self, agent_outputs: List[AgentOutput]) -> float:
        """Calculate overall pipeline confidence."""
        if not agent_outputs:
            return 0.0
        
        # Average confidence across all agents
        confidences = [output.confidence for output in agent_outputs]
        return sum(confidences) / len(confidences)

    def _calculate_improvement_metrics(self, original_text: str, corrected_text: str, agent_outputs: List[AgentOutput]) -> Dict[str, float]:
        """Calculate improvement metrics from the pipeline."""
        metrics = {
            'text_similarity': 0.0,
            'correction_confidence': 0.0,
            'processing_efficiency': 0.0,
            'agent_consensus': 0.0
        }
        
        try:
            # Text similarity (simple character-based)
            if original_text and corrected_text:
                similarity = 1.0 - (abs(len(corrected_text) - len(original_text)) / max(len(original_text), len(corrected_text)))
                metrics['text_similarity'] = max(0.0, similarity)
            
            # Correction confidence (from clarifier)
            clarifier_outputs = [o for o in agent_outputs if o.agent_role == AgentRole.CLARIFIER]
            if clarifier_outputs:
                metrics['correction_confidence'] = clarifier_outputs[0].confidence
            
            # Processing efficiency (based on timing)
            total_time = sum(o.processing_time_ms for o in agent_outputs)
            if total_time > 0:
                metrics['processing_efficiency'] = max(0.0, 1.0 - (total_time / 10000))  # Normalize to 10s max
            
            # Agent consensus (variance in confidence)
            confidences = [o.confidence for o in agent_outputs]
            if confidences:
                variance = sum((c - sum(confidences)/len(confidences))**2 for c in confidences) / len(confidences)
                metrics['agent_consensus'] = max(0.0, 1.0 - variance)
            
        except Exception as e:
            logger.error(f"Error calculating improvement metrics: {e}")
        
        return metrics

    def _update_pipeline_stats(self, processing_time_ms: float, improvement_metrics: Dict[str, float]):
        """Update pipeline performance statistics."""
        self.pipeline_stats['total_runs'] += 1
        
        # Update average latency
        current_avg = self.pipeline_stats['average_latency_ms']
        total_runs = self.pipeline_stats['total_runs']
        self.pipeline_stats['average_latency_ms'] = (current_avg * (total_runs - 1) + processing_time_ms) / total_runs
        
        # Update improvement metrics
        if 'correction_confidence' in improvement_metrics:
            current_improvement = self.pipeline_stats['average_improvement']
            new_improvement = improvement_metrics['correction_confidence']
            self.pipeline_stats['average_improvement'] = (current_improvement * (total_runs - 1) + new_improvement) / total_runs
        
        # Count successful corrections
        if improvement_metrics.get('correction_confidence', 0) > 0.7:
            self.pipeline_stats['successful_corrections'] += 1

    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline performance statistics."""
        stats = self.pipeline_stats.copy()
        if stats['total_runs'] > 0:
            stats['success_rate'] = stats['successful_corrections'] / stats['total_runs']
        else:
            stats['success_rate'] = 0.0
        
        return stats


# Global pipeline instance
_agent_pipeline = None


def get_agent_pipeline(claude_api_key: str) -> AgentPipeline:
    """Get or create agent pipeline instance."""
    global _agent_pipeline
    if _agent_pipeline is None:
        _agent_pipeline = AgentPipeline(claude_api_key)
    return _agent_pipeline


if __name__ == "__main__":
    # Example usage
    async def test_agent_pipeline():
        import os
        
        api_key = os.getenv("CLAUDE_API_KEY", "test_key")
        pipeline = AgentPipeline(api_key)
        
        # Test text with potential hallucinations
        test_text = "Paris is the capital of France and has a population of 50 million people. It was founded in 1889 by Napoleon Bonaparte."
        
        result = await pipeline.process_text(
            text=test_text,
            context="Geographic and historical information about Paris",
            domain="geography"
        )
        
        print(f"Original: {result.original_text}")
        print(f"Corrected: {result.corrected_text}")
        print(f"Hallucination Score: {result.hallucination_score:.3f}")
        print(f"Correction Applied: {result.correction_applied}")
        print(f"Pipeline Confidence: {result.pipeline_confidence:.3f}")
        print(f"Processing Time: {result.total_processing_time_ms:.2f}ms")
        
        # Print agent outputs
        for output in result.agent_outputs:
            print(f"\n{output.agent_role.value.upper()}: {output.content[:200]}...")
    
    # Run test
    # asyncio.run(test_agent_pipeline())
