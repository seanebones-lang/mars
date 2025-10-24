"""
RAG-Enhanced Judge that uses graph database for contextual hallucination detection.
Combines traditional detection with historical pattern matching and similar case retrieval.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.judges.ensemble_judge import EnsembleJudge
from src.models.schemas import AgentTestRequest, HallucinationReport
from src.services.graph_database import get_graph_database, GraphDatabaseService

logger = logging.getLogger(__name__)


class RAGEnhancedJudge:
    """
    Enhanced judge that combines ensemble detection with RAG-based contextual analysis.
    Uses graph database to find similar cases and improve detection accuracy.
    """
    
    def __init__(self, claude_api_key: str):
        self.ensemble_judge = EnsembleJudge(claude_api_key)
        self.graph_db = get_graph_database()
        self.claude_api_key = claude_api_key
        
    async def evaluate(self, request: AgentTestRequest, 
                      agent_id: str = "unknown",
                      agent_name: str = "Unknown Agent",
                      use_rag: bool = True) -> HallucinationReport:
        """
        Evaluate agent response with RAG enhancement.
        
        Args:
            request: The agent test request
            agent_id: Identifier for the agent
            agent_name: Human-readable agent name
            use_rag: Whether to use RAG for contextual enhancement
            
        Returns:
            Enhanced hallucination report with contextual insights
        """
        
        # Step 1: Run standard ensemble detection
        base_result = await self.ensemble_judge.evaluate(request)
        
        # Step 2: RAG Enhancement (if enabled and available)
        rag_insights = {}
        if use_rag:
            try:
                rag_insights = await self._get_rag_insights(
                    request.agent_output,
                    request.ground_truth or "",
                    base_result
                )
            except Exception as e:
                logger.warning(f"RAG enhancement failed: {e}")
        
        # Step 3: Combine results and adjust confidence
        enhanced_result = await self._enhance_with_rag(base_result, rag_insights)
        
        # Step 4: Store in graph database for future RAG
        try:
            await self._store_result(
                agent_id=agent_id,
                agent_name=agent_name,
                request=request,
                result=enhanced_result,
                rag_insights=rag_insights
            )
        except Exception as e:
            logger.warning(f"Failed to store result in graph database: {e}")
        
        return enhanced_result
    
    async def _get_rag_insights(self, agent_output: str, ground_truth: str, 
                              base_result: HallucinationReport) -> Dict[str, Any]:
        """Get RAG-based contextual insights."""
        
        insights = {
            "similar_cases": [],
            "pattern_matches": [],
            "confidence_adjustment": 0.0,
            "contextual_explanation": "",
            "suggested_corrections": []
        }
        
        try:
            # Find similar responses in graph database
            similar_responses = await self.graph_db.find_similar_responses(
                query_text=ground_truth,
                response_text=agent_output,
                limit=5,
                similarity_threshold=0.7
            )
            
            insights["similar_cases"] = similar_responses
            
            # Get hallucination patterns
            patterns = await self.graph_db.get_hallucination_patterns(limit=20)
            
            # Check if current response matches known patterns
            pattern_matches = []
            for pattern in patterns:
                if pattern["pattern"].lower() in agent_output.lower():
                    pattern_matches.append({
                        "pattern": pattern["pattern"],
                        "frequency": pattern["frequency"],
                        "severity": pattern["severity"],
                        "confidence_boost": 0.1 * (pattern["frequency"] / 10)  # More frequent = higher confidence
                    })
            
            insights["pattern_matches"] = pattern_matches
            
            # Calculate confidence adjustment based on similar cases
            if similar_responses:
                similar_risks = [case["hallucination_risk"] for case in similar_responses]
                avg_similar_risk = sum(similar_risks) / len(similar_risks)
                
                # Adjust confidence based on consistency with similar cases
                risk_difference = abs(base_result.hallucination_risk - avg_similar_risk)
                if risk_difference < 0.1:  # Very similar
                    insights["confidence_adjustment"] = 0.15
                elif risk_difference < 0.2:  # Somewhat similar
                    insights["confidence_adjustment"] = 0.05
                else:  # Different from historical cases
                    insights["confidence_adjustment"] = -0.05
            
            # Boost confidence for known patterns
            if pattern_matches:
                pattern_boost = sum(match["confidence_boost"] for match in pattern_matches)
                insights["confidence_adjustment"] += min(pattern_boost, 0.2)  # Cap at 0.2
            
            # Generate contextual explanation
            insights["contextual_explanation"] = self._generate_contextual_explanation(
                similar_responses, pattern_matches, base_result
            )
            
            # Get suggested corrections for high-risk responses
            if base_result.hallucination_risk > 0.6:
                insights["suggested_corrections"] = await self._get_suggested_corrections(
                    agent_output, pattern_matches
                )
        
        except Exception as e:
            logger.error(f"Error getting RAG insights: {e}")
        
        return insights
    
    def _generate_contextual_explanation(self, similar_cases: List[Dict], 
                                       pattern_matches: List[Dict],
                                       base_result: HallucinationReport) -> str:
        """Generate contextual explanation based on RAG insights."""
        
        explanations = []
        
        if similar_cases:
            similar_count = len(similar_cases)
            avg_risk = sum(case["hallucination_risk"] for case in similar_cases) / similar_count
            explanations.append(
                f"Found {similar_count} similar responses with average risk of {avg_risk:.1%}."
            )
        
        if pattern_matches:
            high_freq_patterns = [p for p in pattern_matches if p["frequency"] > 5]
            if high_freq_patterns:
                pattern_names = [p["pattern"] for p in high_freq_patterns]
                explanations.append(
                    f"Contains known hallucination patterns: {', '.join(pattern_names)}."
                )
        
        if not explanations:
            explanations.append("No similar cases or known patterns found in historical data.")
        
        return " ".join(explanations)
    
    async def _get_suggested_corrections(self, agent_output: str, 
                                       pattern_matches: List[Dict]) -> List[str]:
        """Get suggested corrections based on known patterns."""
        
        corrections = []
        
        # Simple pattern-based corrections
        correction_map = {
            "quantum router": "network router",
            "flux capacitor": "network interface card",
            "telepathic delivery": "standard shipping",
            "unlimited vacation": "standard PTO policy",
            "free Tesla": "standard benefits package",
            "time travel": "standard processing time",
            "mind reading": "data analysis",
            "magic": "advanced technology"
        }
        
        for pattern_match in pattern_matches:
            pattern = pattern_match["pattern"]
            if pattern.lower() in correction_map:
                correction = correction_map[pattern.lower()]
                corrected_text = agent_output.replace(pattern, correction)
                corrections.append(corrected_text)
        
        return corrections[:3]  # Limit to top 3 suggestions
    
    async def _enhance_with_rag(self, base_result: HallucinationReport, 
                              rag_insights: Dict[str, Any]) -> HallucinationReport:
        """Enhance base result with RAG insights."""
        
        # Adjust confidence based on RAG insights
        confidence_adjustment = rag_insights.get("confidence_adjustment", 0.0)
        new_uncertainty = max(0.0, min(1.0, base_result.uncertainty - confidence_adjustment))
        
        # Enhance details with RAG information
        enhanced_details = base_result.details.copy()
        enhanced_details.update({
            "rag_similar_cases_count": len(rag_insights.get("similar_cases", [])),
            "rag_pattern_matches": rag_insights.get("pattern_matches", []),
            "rag_contextual_explanation": rag_insights.get("contextual_explanation", ""),
            "rag_confidence_adjustment": confidence_adjustment,
            "rag_suggested_corrections": rag_insights.get("suggested_corrections", [])
        })
        
        # Create enhanced report
        enhanced_result = HallucinationReport(
            hallucination_risk=base_result.hallucination_risk,
            uncertainty=new_uncertainty,
            needs_review=base_result.needs_review,
            details=enhanced_details
        )
        
        return enhanced_result
    
    async def _store_result(self, agent_id: str, agent_name: str,
                          request: AgentTestRequest, result: HallucinationReport,
                          rag_insights: Dict[str, Any]):
        """Store result in graph database for future RAG."""
        
        # Extract hallucinated segments
        hallucinated_segments = result.details.get("hallucinated_segments", [])
        
        # Calculate processing time (mock for now)
        processing_time_ms = result.details.get("processing_time_ms", 1000.0)
        
        # Store in graph database
        await self.graph_db.store_agent_response(
            agent_id=agent_id,
            agent_name=agent_name,
            query_text=request.ground_truth or "No ground truth provided",
            response_text=request.agent_output,
            hallucination_risk=result.hallucination_risk,
            confidence=1.0 - result.uncertainty,
            processing_time_ms=processing_time_ms,
            hallucinated_segments=hallucinated_segments,
            metadata={
                "rag_enhanced": True,
                "similar_cases_count": len(rag_insights.get("similar_cases", [])),
                "pattern_matches_count": len(rag_insights.get("pattern_matches", [])),
                "confidence_adjustment": rag_insights.get("confidence_adjustment", 0.0)
            }
        )
    
    async def get_analytics_data(self, days: int = 30) -> Dict[str, Any]:
        """Get analytics data for dashboard."""
        
        try:
            # Get agent performance metrics
            agent_metrics = await self.graph_db.get_agent_performance_metrics(days=days)
            
            # Get hallucination patterns
            patterns = await self.graph_db.get_hallucination_patterns(limit=10)
            
            # Get time series data
            time_series = await self.graph_db.get_time_series_data(days=days)
            
            return {
                "agent_metrics": agent_metrics,
                "hallucination_patterns": patterns,
                "time_series": time_series,
                "summary": {
                    "total_agents": len(agent_metrics.get("agents", [])) if isinstance(agent_metrics, dict) else 1,
                    "total_patterns": len(patterns),
                    "data_points": len(time_series)
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting analytics data: {e}")
            return {
                "agent_metrics": {"agents": []},
                "hallucination_patterns": [],
                "time_series": [],
                "summary": {"total_agents": 0, "total_patterns": 0, "data_points": 0}
            }


# Global RAG-enhanced judge instance
_rag_judge: Optional[RAGEnhancedJudge] = None

def get_rag_enhanced_judge(claude_api_key: str) -> RAGEnhancedJudge:
    """Get or create RAG-enhanced judge instance."""
    global _rag_judge
    if _rag_judge is None:
        _rag_judge = RAGEnhancedJudge(claude_api_key)
    return _rag_judge
