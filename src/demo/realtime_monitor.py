"""
Real-time monitoring service that orchestrates agent simulation and hallucination detection.
Integrates the demo orchestrator with the detection pipeline and WebSocket broadcasting.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import mlflow
from contextlib import asynccontextmanager

from .orchestrator import DemoOrchestrator, AgentResponse
from ..judges.ensemble_judge import EnsembleJudge
from ..models.schemas import AgentTestRequest, HallucinationReport
from ..api.websocket import get_connection_manager
from ..services.webhook_service import get_webhook_service, WebhookAlert

logger = logging.getLogger(__name__)


class RealtimeMonitor:
    """
    Real-time monitoring service that coordinates agent simulation,
    hallucination detection, and live result broadcasting.
    """
    
    def __init__(self, claude_api_key: str):
        self.orchestrator = DemoOrchestrator()
        self.judge = EnsembleJudge(claude_api_key)
        self.connection_manager = get_connection_manager()
        self.webhook_service = get_webhook_service()
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.processed_responses: set = set()  # Track processed response IDs
        self.stats = {
            "total_responses": 0,
            "flagged_responses": 0,
            "start_time": None,
            "agents": {}
        }
        
    async def start_monitoring(self, 
                             response_interval: float = 3.0,
                             jitter: float = 2.0) -> None:
        """
        Start real-time monitoring with agent simulation.
        
        Args:
            response_interval: Base time between agent responses
            jitter: Random variation in response timing
        """
        if self.is_monitoring:
            logger.warning("Monitoring already active")
            return
            
        self.is_monitoring = True
        self.stats["start_time"] = datetime.utcnow()
        self.stats["total_responses"] = 0
        self.stats["flagged_responses"] = 0
        
        logger.info("Starting real-time monitoring")
        
        # Start monitoring task
        self.monitoring_task = asyncio.create_task(
            self._monitoring_loop(response_interval, jitter)
        )
        
        # Broadcast monitoring started
        await self.connection_manager.broadcast({
            "type": "monitoring_started",
            "timestamp": datetime.utcnow().isoformat(),
            "agents": list(self.orchestrator.agents.keys()),
            "config": {
                "response_interval": response_interval,
                "jitter": jitter
            }
        })
    
    async def stop_monitoring(self) -> None:
        """Stop real-time monitoring."""
        if not self.is_monitoring:
            logger.warning("Monitoring not active")
            return
            
        self.is_monitoring = False
        self.orchestrator.stop_simulation()
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
        
        # Clear processed responses for fresh start
        self.processed_responses.clear()
        
        logger.info("Stopped real-time monitoring")
        
        # Broadcast monitoring stopped
        await self.connection_manager.broadcast({
            "type": "monitoring_stopped",
            "timestamp": datetime.utcnow().isoformat(),
            "stats": self.get_session_stats()
        })
    
    async def _monitoring_loop(self, response_interval: float, jitter: float) -> None:
        """Main monitoring loop that processes agent responses."""
        try:
            async for agent_response in self.orchestrator.start_simulation(response_interval, jitter):
                if not self.is_monitoring:
                    break
                
                # Process the agent response
                await self._process_agent_response(agent_response)
                
        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            await self.connection_manager.broadcast({
                "type": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Monitoring error: {str(e)}"
            })
        finally:
            self.is_monitoring = False
    
    async def _process_agent_response(self, agent_response: AgentResponse) -> None:
        """Process a single agent response through the detection pipeline."""
        # Check for duplicates
        response_id = agent_response.unique_id or f"{agent_response.agent_id}-{agent_response.timestamp}"
        if response_id in self.processed_responses:
            logger.warning(f"Skipping duplicate response: {response_id}")
            return
        
        self.processed_responses.add(response_id)
        
        # Clean up old processed IDs (keep only last 1000)
        if len(self.processed_responses) > 1000:
            # Remove oldest 200 entries
            old_ids = list(self.processed_responses)[:200]
            for old_id in old_ids:
                self.processed_responses.discard(old_id)
        
        start_time = datetime.utcnow()
        
        try:
            # Create test request for the ensemble judge
            test_request = AgentTestRequest(
                agent_output=agent_response.output,
                ground_truth="Evaluate this response for factual accuracy, fabrications, and hallucinations based on your knowledge. Flag any suspicious claims, made-up technology, incorrect facts, or unrealistic statements.",
                conversation_history=[]
            )
            
            # Run hallucination detection
            detection_result = await self.judge.evaluate(test_request)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update statistics
            self.stats["total_responses"] += 1
            if detection_result.hallucination_risk > 0.5:
                self.stats["flagged_responses"] += 1
            
            agent_stats = self.stats["agents"].get(agent_response.agent_id, {"responses": 0, "flagged": 0})
            agent_stats["responses"] += 1
            if detection_result.hallucination_risk > 0.5:
                agent_stats["flagged"] += 1
            self.stats["agents"][agent_response.agent_id] = agent_stats
            
            # Generate mitigation if needed
            mitigation = None
            if detection_result.hallucination_risk > 0.5:
                mitigation = await self._generate_mitigation(agent_response.output, detection_result)
            
            # Prepare real-time data for broadcasting
            realtime_data = {
                "type": "detection_result",
                "agent_id": agent_response.agent_id,
                "query": agent_response.query,
                "output": agent_response.output,
                "hallucination_risk": detection_result.hallucination_risk,
                "flagged": detection_result.hallucination_risk > 0.5,
                "confidence": 1 - detection_result.uncertainty,
                "flagged_segments": detection_result.details.get("hallucinated_segments", []),
                "mitigation": mitigation,
                "timestamp": agent_response.timestamp,
                "claude_explanation": detection_result.details.get("claude_explanation", ""),
                "processing_time_ms": int(processing_time * 1000),
                "expected_hallucination": agent_response.expected_hallucination,
                "detection_accuracy": (detection_result.hallucination_risk > 0.5) == agent_response.expected_hallucination
            }
            
            # Send webhook alerts for high-risk detections
            if detection_result.hallucination_risk > 0.5:
                await self._send_webhook_alert(agent_response, detection_result, processing_time)
            
            # Log to MLflow
            await self._log_to_mlflow(agent_response, detection_result, processing_time)
            
            # Broadcast to all connected clients
            await self.connection_manager.broadcast(realtime_data)
            
            logger.info(
                f"Processed {agent_response.agent_id}: "
                f"risk={detection_result.hallucination_risk:.3f}, "
                f"flagged={detection_result.hallucination_risk > 0.5}, "
                f"time={processing_time:.3f}s"
            )
            
        except Exception as e:
            logger.error(f"Error processing agent response: {e}")
            await self.connection_manager.broadcast({
                "type": "processing_error",
                "timestamp": datetime.utcnow().isoformat(),
                "agent_id": agent_response.agent_id,
                "error": str(e)
            })
    
    async def _generate_mitigation(self, agent_output: str, detection_result: HallucinationReport) -> Optional[str]:
        """Generate a mitigation suggestion for hallucinated content."""
        try:
            # Simple rule-based mitigation for demo
            mitigations = {
                "quantum router": "standard network router",
                "flux capacitor": "network interface card", 
                "telepathic delivery": "standard shipping",
                "unlimited vacation": "standard PTO policy per employee handbook",
                "free Tesla": "standard benefits package as outlined in employee handbook",
                "time travel": "standard scheduling",
                "interdimensional": "standard",
                "quantum defragmentation": "standard database optimization",
                "thought-based transactions": "standard payment methods",
                "AI-powered telepathic": "standard automated"
            }
            
            mitigation = agent_output
            flagged_segments = detection_result.details.get("hallucinated_segments", [])
            
            for segment in flagged_segments:
                for hallucination, correction in mitigations.items():
                    if hallucination.lower() in segment.lower():
                        mitigation = mitigation.replace(segment, correction)
                        break
            
            if mitigation != agent_output:
                return mitigation
            else:
                return "Please verify this information with official documentation and established procedures."
                
        except Exception as e:
            logger.error(f"Error generating mitigation: {e}")
            return "Please review this response for accuracy."
    
    async def _send_webhook_alert(self, 
                                agent_response: AgentResponse, 
                                detection_result: HallucinationReport,
                                processing_time: float) -> None:
        """Send webhook alert for high-risk hallucination detection."""
        try:
            # Determine severity based on risk level
            if detection_result.hallucination_risk >= 0.9:
                severity = "critical"
            elif detection_result.hallucination_risk >= 0.7:
                severity = "high"
            else:
                severity = "medium"
            
            # Create webhook alert
            alert = WebhookAlert(
                alert_id=f"hal-{agent_response.unique_id}",
                alert_type="hallucination",
                severity=severity,
                title=f"Hallucination Detected: {agent_response.agent_id}",
                message=f"Agent '{agent_response.agent_id}' produced a response with {detection_result.hallucination_risk:.1%} hallucination risk. Response: '{agent_response.output[:100]}{'...' if len(agent_response.output) > 100 else ''}'",
                agent_id=agent_response.agent_id,
                agent_name=agent_response.agent_id.replace('_', ' ').title(),
                hallucination_risk=detection_result.hallucination_risk,
                confidence=1 - detection_result.uncertainty,
                timestamp=agent_response.timestamp,
                details={
                    "query": agent_response.query,
                    "full_output": agent_response.output,
                    "claude_explanation": detection_result.details.get("claude_explanation", ""),
                    "flagged_segments": detection_result.details.get("hallucinated_segments", []),
                    "processing_time_ms": processing_time * 1000,
                    "expected_hallucination": agent_response.expected_hallucination,
                    "detection_accuracy": (detection_result.hallucination_risk > 0.5) == agent_response.expected_hallucination
                },
                requires_acknowledgment=severity in ["high", "critical"]
            )
            
            # Send alert via webhook service
            async with self.webhook_service:
                results = await self.webhook_service.send_alert(alert)
                
                # Log webhook results
                successful_webhooks = [k for k, v in results.items() if v]
                if successful_webhooks:
                    logger.info(f"Webhook alerts sent successfully: {successful_webhooks}")
                else:
                    logger.warning("No webhook alerts were sent successfully")
                    
        except Exception as e:
            logger.error(f"Error sending webhook alert: {e}")
    
    async def _log_to_mlflow(self, 
                           agent_response: AgentResponse, 
                           detection_result: HallucinationReport,
                           processing_time: float) -> None:
        """Log detection results to MLflow for tracking and analysis."""
        try:
            with mlflow.start_run():
                # Log parameters
                mlflow.log_param("agent_id", agent_response.agent_id)
                mlflow.log_param("expected_hallucination", agent_response.expected_hallucination)
                mlflow.log_param("output_length", len(agent_response.output))
                
                # Log metrics
                mlflow.log_metric("hallucination_risk", detection_result.hallucination_risk)
                mlflow.log_metric("uncertainty", detection_result.uncertainty)
                mlflow.log_metric("processing_time_seconds", processing_time)
                mlflow.log_metric("claude_score", detection_result.details.get("claude_score", 0))
                mlflow.log_metric("statistical_score", detection_result.details.get("statistical_score", 0))
                
                # Log accuracy
                is_correct = (detection_result.hallucination_risk > 0.5) == agent_response.expected_hallucination
                mlflow.log_metric("detection_accuracy", 1.0 if is_correct else 0.0)
                
        except Exception as e:
            logger.error(f"Error logging to MLflow: {e}")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics."""
        if self.stats["start_time"]:
            session_duration = (datetime.utcnow() - self.stats["start_time"]).total_seconds()
        else:
            session_duration = 0
            
        return {
            "total_responses": self.stats["total_responses"],
            "flagged_responses": self.stats["flagged_responses"],
            "flagged_rate": self.stats["flagged_responses"] / max(1, self.stats["total_responses"]),
            "session_duration_seconds": session_duration,
            "responses_per_minute": (self.stats["total_responses"] / max(1, session_duration)) * 60,
            "agents": self.stats["agents"],
            "is_monitoring": self.is_monitoring
        }
    
    def is_active(self) -> bool:
        """Check if monitoring is currently active."""
        return self.is_monitoring
    
    async def send_test_response(self, agent_id: str, custom_output: str) -> None:
        """Send a custom test response for interactive demo mode."""
        if agent_id not in self.orchestrator.agents:
            raise ValueError(f"Unknown agent: {agent_id}")
            
        # Create a custom agent response
        test_response = AgentResponse(
            agent_id=agent_id,
            query="Custom test query",
            output=custom_output,
            expected_hallucination=False,  # Unknown for custom input
            timestamp=datetime.utcnow().isoformat(),
            confidence=0.8,
            response_time_ms=100
        )
        
        # Process it through the detection pipeline
        await self._process_agent_response(test_response)


# Global monitor instance
_monitor_instance: Optional[RealtimeMonitor] = None


def get_realtime_monitor(claude_api_key: str) -> RealtimeMonitor:
    """Get or create the global realtime monitor instance."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = RealtimeMonitor(claude_api_key)
    return _monitor_instance
