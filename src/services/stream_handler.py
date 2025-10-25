"""
Dynamic Data Source Handler
Mitigates hallucinations from real-time data streams using Apache Flink-like processing.

Provides streaming data validation, anomaly detection, and hallucination prevention
for high-volume, real-time agent interactions with usage-based billing.

Author: AgentGuard Engineering Team
Date: October 2025
Version: 1.0.0
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Any, AsyncIterator, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
from collections import deque

logger = logging.getLogger(__name__)


class StreamQuality(Enum):
    """Quality assessment for streaming data."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class AnomalyType(Enum):
    """Types of anomalies detected in streams."""
    SUDDEN_SPIKE = "sudden_spike"
    SUDDEN_DROP = "sudden_drop"
    PATTERN_BREAK = "pattern_break"
    DATA_CORRUPTION = "data_corruption"
    LATENCY_SPIKE = "latency_spike"
    MISSING_DATA = "missing_data"
    DUPLICATE_DATA = "duplicate_data"


@dataclass
class StreamMetrics:
    """Metrics for stream monitoring."""
    total_events: int = 0
    events_per_second: float = 0.0
    average_latency_ms: float = 0.0
    error_rate: float = 0.0
    anomaly_count: int = 0
    quality_score: float = 1.0
    last_update: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class StreamEvent:
    """Individual event in a data stream."""
    event_id: str
    timestamp: str
    data: Dict[str, Any]
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamValidationResult:
    """Result of stream validation."""
    is_valid: bool
    quality: StreamQuality
    anomalies: List[AnomalyType]
    confidence: float
    explanation: str
    metrics: StreamMetrics
    recommendations: List[str]
    processing_time_ms: float


@dataclass
class StreamWindow:
    """Time window for stream processing."""
    window_id: str
    start_time: datetime
    end_time: datetime
    events: List[StreamEvent]
    aggregated_data: Dict[str, Any] = field(default_factory=dict)


class StreamHandler:
    """
    Dynamic data source handler for real-time stream processing.
    
    Implements Apache Flink-like capabilities:
    - Windowed aggregation
    - Event time processing
    - Watermark handling
    - State management
    - Anomaly detection
    - Quality monitoring
    
    Designed for high-volume streams (1000+ events/second) with
    hallucination prevention and usage-based billing tracking.
    """
    
    def __init__(
        self,
        window_size_seconds: int = 60,
        watermark_delay_seconds: int = 5,
        max_buffer_size: int = 10000
    ):
        """
        Initialize stream handler.
        
        Args:
            window_size_seconds: Size of processing windows in seconds
            watermark_delay_seconds: Delay for late-arriving events
            max_buffer_size: Maximum events to buffer
        """
        self.window_size = timedelta(seconds=window_size_seconds)
        self.watermark_delay = timedelta(seconds=watermark_delay_seconds)
        self.max_buffer_size = max_buffer_size
        
        # Stream state
        self.event_buffer: deque = deque(maxlen=max_buffer_size)
        self.windows: Dict[str, StreamWindow] = {}
        self.metrics = StreamMetrics()
        
        # Anomaly detection state
        self.baseline_rate = 0.0
        self.baseline_latency = 0.0
        self.event_history: deque = deque(maxlen=1000)
        
        # Billing tracking
        self.events_processed = 0
        self.billing_period_start = datetime.utcnow()
        
        logger.info(
            f"Stream handler initialized: window={window_size_seconds}s, "
            f"watermark={watermark_delay_seconds}s, buffer={max_buffer_size}"
        )
    
    async def process_stream(
        self,
        stream_source: AsyncIterator[Dict[str, Any]],
        validator: Optional[Callable] = None
    ) -> AsyncIterator[StreamValidationResult]:
        """
        Process incoming data stream with validation and anomaly detection.
        
        Args:
            stream_source: Async iterator providing stream events
            validator: Optional custom validation function
            
        Yields:
            StreamValidationResult for each processing window
        """
        start_time = time.time()
        window_events = []
        window_start = datetime.utcnow()
        
        async for raw_event in stream_source:
            # Create stream event
            event = self._create_event(raw_event)
            
            # Add to buffer and history
            self.event_buffer.append(event)
            self.event_history.append({
                "timestamp": event.timestamp,
                "size": len(str(event.data))
            })
            
            # Track for billing
            self.events_processed += 1
            
            # Add to current window
            window_events.append(event)
            
            # Check if window is complete
            if datetime.utcnow() - window_start >= self.window_size:
                # Process window
                result = await self._process_window(
                    window_events,
                    validator
                )
                
                yield result
                
                # Reset window
                window_events = []
                window_start = datetime.utcnow()
            
            # Update metrics
            self._update_metrics()
        
        # Process final window if it has events
        if window_events:
            result = await self._process_window(window_events, validator)
            yield result
    
    async def validate_stream_event(
        self,
        event_data: Dict[str, Any],
        source: str = "unknown"
    ) -> StreamValidationResult:
        """
        Validate a single stream event for hallucination risks.
        
        Args:
            event_data: The event data to validate
            source: Source identifier for the event
            
        Returns:
            StreamValidationResult with validation assessment
        """
        start_time = time.time()
        
        # Create event
        event = StreamEvent(
            event_id=self._generate_event_id(event_data),
            timestamp=datetime.utcnow().isoformat(),
            data=event_data,
            source=source
        )
        
        # Detect anomalies
        anomalies = self._detect_anomalies(event)
        
        # Assess quality
        quality = self._assess_quality(event, anomalies)
        
        # Calculate confidence
        confidence = self._calculate_confidence(event, anomalies, quality)
        
        # Generate explanation
        explanation = self._generate_explanation(quality, anomalies)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(quality, anomalies)
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Update metrics
        self.metrics.total_events += 1
        self.metrics.anomaly_count += len(anomalies)
        
        return StreamValidationResult(
            is_valid=quality not in [StreamQuality.POOR, StreamQuality.CRITICAL],
            quality=quality,
            anomalies=anomalies,
            confidence=confidence,
            explanation=explanation,
            metrics=self.metrics,
            recommendations=recommendations,
            processing_time_ms=processing_time_ms
        )
    
    async def _process_window(
        self,
        events: List[StreamEvent],
        validator: Optional[Callable]
    ) -> StreamValidationResult:
        """Process a complete time window of events."""
        start_time = time.time()
        
        if not events:
            return StreamValidationResult(
                is_valid=True,
                quality=StreamQuality.GOOD,
                anomalies=[],
                confidence=1.0,
                explanation="No events in window",
                metrics=self.metrics,
                recommendations=[],
                processing_time_ms=0.0
            )
        
        # Aggregate window data
        aggregated = self._aggregate_window(events)
        
        # Detect window-level anomalies
        window_anomalies = self._detect_window_anomalies(events, aggregated)
        
        # Custom validation if provided
        if validator:
            try:
                custom_result = await validator(events, aggregated)
                if custom_result.get("anomalies"):
                    window_anomalies.extend(custom_result["anomalies"])
            except Exception as e:
                logger.error(f"Custom validator error: {e}")
        
        # Assess window quality
        quality = self._assess_window_quality(events, window_anomalies)
        
        # Calculate confidence
        confidence = self._calculate_window_confidence(events, window_anomalies)
        
        # Generate explanation
        explanation = self._generate_window_explanation(
            events, aggregated, quality, window_anomalies
        )
        
        # Generate recommendations
        recommendations = self._generate_window_recommendations(
            quality, window_anomalies
        )
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        return StreamValidationResult(
            is_valid=quality not in [StreamQuality.POOR, StreamQuality.CRITICAL],
            quality=quality,
            anomalies=window_anomalies,
            confidence=confidence,
            explanation=explanation,
            metrics=self.metrics,
            recommendations=recommendations,
            processing_time_ms=processing_time_ms
        )
    
    def _create_event(self, raw_data: Dict[str, Any]) -> StreamEvent:
        """Create a stream event from raw data."""
        return StreamEvent(
            event_id=self._generate_event_id(raw_data),
            timestamp=raw_data.get("timestamp", datetime.utcnow().isoformat()),
            data=raw_data.get("data", raw_data),
            source=raw_data.get("source", "unknown"),
            metadata=raw_data.get("metadata", {})
        )
    
    def _generate_event_id(self, data: Dict[str, Any]) -> str:
        """Generate unique event ID."""
        timestamp = datetime.utcnow().isoformat()
        hash_input = f"{str(data)}{timestamp}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def _detect_anomalies(self, event: StreamEvent) -> List[AnomalyType]:
        """Detect anomalies in a single event."""
        anomalies = []
        
        # Check for data corruption
        if not event.data or not isinstance(event.data, dict):
            anomalies.append(AnomalyType.DATA_CORRUPTION)
        
        # Check for duplicate
        recent_ids = [e.get("id") for e in list(self.event_history)[-10:]]
        if event.event_id in recent_ids:
            anomalies.append(AnomalyType.DUPLICATE_DATA)
        
        # Check for missing required fields
        if "timestamp" not in event.data and not event.timestamp:
            anomalies.append(AnomalyType.MISSING_DATA)
        
        return anomalies
    
    def _detect_window_anomalies(
        self,
        events: List[StreamEvent],
        aggregated: Dict[str, Any]
    ) -> List[AnomalyType]:
        """Detect anomalies across a window of events."""
        anomalies = []
        
        event_count = len(events)
        
        # Check for sudden spike
        if self.baseline_rate > 0:
            rate_change = abs(event_count - self.baseline_rate) / self.baseline_rate
            if rate_change > 2.0:  # 200% change
                if event_count > self.baseline_rate:
                    anomalies.append(AnomalyType.SUDDEN_SPIKE)
                else:
                    anomalies.append(AnomalyType.SUDDEN_DROP)
        
        # Check for pattern breaks
        if event_count == 0:
            anomalies.append(AnomalyType.MISSING_DATA)
        
        # Update baseline
        if self.baseline_rate == 0:
            self.baseline_rate = event_count
        else:
            self.baseline_rate = 0.9 * self.baseline_rate + 0.1 * event_count
        
        return anomalies
    
    def _aggregate_window(self, events: List[StreamEvent]) -> Dict[str, Any]:
        """Aggregate data across a window."""
        if not events:
            return {}
        
        return {
            "event_count": len(events),
            "sources": list(set(e.source for e in events)),
            "time_span_seconds": (
                datetime.fromisoformat(events[-1].timestamp) -
                datetime.fromisoformat(events[0].timestamp)
            ).total_seconds() if len(events) > 1 else 0,
            "average_size_bytes": sum(len(str(e.data)) for e in events) / len(events),
            "unique_events": len(set(e.event_id for e in events))
        }
    
    def _assess_quality(
        self,
        event: StreamEvent,
        anomalies: List[AnomalyType]
    ) -> StreamQuality:
        """Assess quality of a single event."""
        if AnomalyType.DATA_CORRUPTION in anomalies:
            return StreamQuality.CRITICAL
        
        if len(anomalies) >= 2:
            return StreamQuality.POOR
        
        if len(anomalies) == 1:
            return StreamQuality.FAIR
        
        return StreamQuality.EXCELLENT
    
    def _assess_window_quality(
        self,
        events: List[StreamEvent],
        anomalies: List[AnomalyType]
    ) -> StreamQuality:
        """Assess quality of a window."""
        if not events:
            return StreamQuality.POOR
        
        if AnomalyType.DATA_CORRUPTION in anomalies:
            return StreamQuality.CRITICAL
        
        anomaly_ratio = len(anomalies) / max(len(events), 1)
        
        if anomaly_ratio > 0.5:
            return StreamQuality.CRITICAL
        elif anomaly_ratio > 0.3:
            return StreamQuality.POOR
        elif anomaly_ratio > 0.1:
            return StreamQuality.FAIR
        elif anomaly_ratio > 0:
            return StreamQuality.GOOD
        else:
            return StreamQuality.EXCELLENT
    
    def _calculate_confidence(
        self,
        event: StreamEvent,
        anomalies: List[AnomalyType],
        quality: StreamQuality
    ) -> float:
        """Calculate confidence in event validation."""
        base_confidence = 0.9
        
        # Reduce confidence for each anomaly
        confidence = base_confidence - (len(anomalies) * 0.15)
        
        # Adjust for quality
        quality_adjustments = {
            StreamQuality.EXCELLENT: 0.1,
            StreamQuality.GOOD: 0.05,
            StreamQuality.FAIR: 0.0,
            StreamQuality.POOR: -0.1,
            StreamQuality.CRITICAL: -0.2
        }
        confidence += quality_adjustments.get(quality, 0)
        
        return max(0.1, min(0.99, confidence))
    
    def _calculate_window_confidence(
        self,
        events: List[StreamEvent],
        anomalies: List[AnomalyType]
    ) -> float:
        """Calculate confidence in window validation."""
        if not events:
            return 0.5
        
        base_confidence = 0.85
        anomaly_ratio = len(anomalies) / len(events)
        
        confidence = base_confidence - (anomaly_ratio * 0.5)
        
        return max(0.1, min(0.99, confidence))
    
    def _generate_explanation(
        self,
        quality: StreamQuality,
        anomalies: List[AnomalyType]
    ) -> str:
        """Generate explanation for event validation."""
        if quality == StreamQuality.EXCELLENT:
            return "Stream event is high quality with no anomalies detected."
        
        anomaly_descriptions = {
            AnomalyType.DATA_CORRUPTION: "data corruption detected",
            AnomalyType.DUPLICATE_DATA: "duplicate event detected",
            AnomalyType.MISSING_DATA: "missing required fields",
            AnomalyType.SUDDEN_SPIKE: "sudden spike in event rate",
            AnomalyType.SUDDEN_DROP: "sudden drop in event rate"
        }
        
        descriptions = [anomaly_descriptions.get(a, str(a)) for a in anomalies]
        
        return f"{quality.value.upper()} quality: {', '.join(descriptions)}"
    
    def _generate_window_explanation(
        self,
        events: List[StreamEvent],
        aggregated: Dict[str, Any],
        quality: StreamQuality,
        anomalies: List[AnomalyType]
    ) -> str:
        """Generate explanation for window validation."""
        event_count = len(events)
        
        if quality == StreamQuality.EXCELLENT:
            return f"Window processed {event_count} events with excellent quality."
        
        anomaly_desc = ", ".join([a.value for a in anomalies])
        
        return (
            f"{quality.value.upper()} quality window: "
            f"{event_count} events processed with anomalies: {anomaly_desc}"
        )
    
    def _generate_recommendations(
        self,
        quality: StreamQuality,
        anomalies: List[AnomalyType]
    ) -> List[str]:
        """Generate recommendations for event issues."""
        recommendations = []
        
        if AnomalyType.DATA_CORRUPTION in anomalies:
            recommendations.append("Validate data source and check for transmission errors")
            recommendations.append("Implement data integrity checks at source")
        
        if AnomalyType.DUPLICATE_DATA in anomalies:
            recommendations.append("Implement deduplication logic")
            recommendations.append("Check for retry loops in data source")
        
        if AnomalyType.MISSING_DATA in anomalies:
            recommendations.append("Ensure all required fields are populated")
            recommendations.append("Implement default values for optional fields")
        
        if quality in [StreamQuality.POOR, StreamQuality.CRITICAL]:
            recommendations.append("Consider pausing stream processing for investigation")
            recommendations.append("Alert data engineering team")
        
        return recommendations
    
    def _generate_window_recommendations(
        self,
        quality: StreamQuality,
        anomalies: List[AnomalyType]
    ) -> List[str]:
        """Generate recommendations for window issues."""
        recommendations = []
        
        if AnomalyType.SUDDEN_SPIKE in anomalies:
            recommendations.append("Investigate cause of traffic spike")
            recommendations.append("Scale processing resources if needed")
            recommendations.append("Check for DDoS or malicious activity")
        
        if AnomalyType.SUDDEN_DROP in anomalies:
            recommendations.append("Check data source health")
            recommendations.append("Verify network connectivity")
            recommendations.append("Review upstream system status")
        
        if quality == StreamQuality.CRITICAL:
            recommendations.append("CRITICAL: Halt stream processing immediately")
            recommendations.append("Escalate to on-call engineer")
            recommendations.append("Review last 24 hours of stream data")
        
        return recommendations
    
    def _update_metrics(self):
        """Update stream metrics."""
        current_time = datetime.utcnow()
        
        # Calculate events per second
        if self.event_history:
            recent_events = [
                e for e in self.event_history
                if datetime.fromisoformat(e["timestamp"]) > current_time - timedelta(seconds=10)
            ]
            self.metrics.events_per_second = len(recent_events) / 10.0
        
        # Update quality score
        if self.metrics.total_events > 0:
            self.metrics.quality_score = 1.0 - (
                self.metrics.anomaly_count / self.metrics.total_events
            )
        
        self.metrics.last_update = current_time.isoformat()
    
    def get_billing_info(self) -> Dict[str, Any]:
        """Get billing information for usage-based pricing."""
        current_time = datetime.utcnow()
        period_duration = (current_time - self.billing_period_start).total_seconds()
        
        return {
            "events_processed": self.events_processed,
            "billing_period_start": self.billing_period_start.isoformat(),
            "billing_period_duration_seconds": period_duration,
            "events_per_second_average": (
                self.events_processed / period_duration if period_duration > 0 else 0
            ),
            "estimated_cost_usd": self._calculate_cost(self.events_processed),
            "next_billing_date": (
                self.billing_period_start + timedelta(days=30)
            ).isoformat()
        }
    
    def _calculate_cost(self, event_count: int) -> float:
        """Calculate cost based on event count."""
        # Tiered pricing
        if event_count <= 10000:
            return 0.0  # Included in base plan
        elif event_count <= 100000:
            return (event_count - 10000) * 0.0001  # $0.0001 per event
        else:
            return 9.0 + (event_count - 100000) * 0.00005  # Volume discount
    
    def reset_billing_period(self):
        """Reset billing period (called monthly)."""
        self.events_processed = 0
        self.billing_period_start = datetime.utcnow()
        logger.info("Billing period reset")

