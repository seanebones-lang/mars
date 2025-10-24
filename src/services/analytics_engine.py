"""
Advanced Analytics Engine for AgentGuard
Provides trend analysis, pattern recognition, and predictive hallucination detection.

October 2025 Enhancement: AI-powered analytics for proactive hallucination prevention.
"""

import logging
import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import classification_report
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, deque
import warnings

# Suppress sklearn warnings
warnings.filterwarnings("ignore", category=UserWarning)

logger = logging.getLogger(__name__)


@dataclass
class AnalyticsConfig:
    """Configuration for analytics engine."""
    trend_window_hours: int = 24
    anomaly_threshold: float = 0.1
    pattern_min_samples: int = 10
    prediction_horizon_hours: int = 6
    max_data_points: int = 10000
    enable_real_time_analysis: bool = True
    enable_predictive_modeling: bool = True
    enable_anomaly_detection: bool = True


@dataclass
class TrendData:
    """Trend analysis data point."""
    timestamp: datetime
    hallucination_score: float
    confidence: float
    model_type: str
    domain: str
    language: str
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class AnalyticsInsight:
    """Analytics insight or finding."""
    insight_type: str  # 'trend', 'anomaly', 'pattern', 'prediction'
    severity: str  # 'low', 'medium', 'high', 'critical'
    title: str
    description: str
    confidence: float
    data_points: int
    timestamp: datetime
    recommendations: List[str]
    metadata: Dict[str, Any] = None


@dataclass
class PredictionResult:
    """Predictive analysis result."""
    prediction_type: str
    predicted_value: float
    confidence_interval: Tuple[float, float]
    time_horizon_hours: int
    features_importance: Dict[str, float]
    model_accuracy: float
    timestamp: datetime


class TrendAnalyzer:
    """
    Analyzes trends in hallucination detection data.
    
    Features:
    - Time series trend analysis
    - Seasonal pattern detection
    - Anomaly identification
    - Comparative analysis across models/domains
    """
    
    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.data_buffer = deque(maxlen=config.max_data_points)
        self.trend_cache = {}
        
    def add_data_point(self, data: TrendData):
        """Add new data point for analysis."""
        self.data_buffer.append(data)
        
        # Clear cache if we have new data
        if len(self.data_buffer) % 100 == 0:  # Clear cache every 100 points
            self.trend_cache.clear()

    def analyze_trends(self, 
                      time_window_hours: Optional[int] = None,
                      group_by: str = 'hour') -> Dict[str, Any]:
        """
        Analyze trends in hallucination detection.
        
        Args:
            time_window_hours: Analysis window (default: config value)
            group_by: Grouping granularity ('hour', 'day', 'week')
            
        Returns:
            Dictionary with trend analysis results
        """
        try:
            window_hours = time_window_hours or self.config.trend_window_hours
            cutoff_time = datetime.now() - timedelta(hours=window_hours)
            
            # Filter data to time window
            recent_data = [
                d for d in self.data_buffer 
                if d.timestamp >= cutoff_time
            ]
            
            if len(recent_data) < 5:
                return {'error': 'Insufficient data for trend analysis'}
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame([
                {
                    'timestamp': d.timestamp,
                    'hallucination_score': d.hallucination_score,
                    'confidence': d.confidence,
                    'model_type': d.model_type,
                    'domain': d.domain,
                    'language': d.language
                }
                for d in recent_data
            ])
            
            # Group by time period
            if group_by == 'hour':
                df['time_group'] = df['timestamp'].dt.floor('H')
            elif group_by == 'day':
                df['time_group'] = df['timestamp'].dt.floor('D')
            else:  # week
                df['time_group'] = df['timestamp'].dt.floor('W')
            
            # Calculate trend metrics
            grouped = df.groupby('time_group').agg({
                'hallucination_score': ['mean', 'std', 'count'],
                'confidence': ['mean', 'std']
            }).reset_index()
            
            # Flatten column names
            grouped.columns = ['time_group', 'avg_hallucination', 'std_hallucination', 'count',
                             'avg_confidence', 'std_confidence']
            
            # Calculate trend direction
            if len(grouped) >= 2:
                recent_avg = grouped['avg_hallucination'].tail(3).mean()
                earlier_avg = grouped['avg_hallucination'].head(3).mean()
                trend_direction = 'increasing' if recent_avg > earlier_avg else 'decreasing'
                trend_magnitude = abs(recent_avg - earlier_avg)
            else:
                trend_direction = 'stable'
                trend_magnitude = 0.0
            
            # Identify patterns by model type and domain
            model_trends = df.groupby('model_type')['hallucination_score'].agg(['mean', 'count']).to_dict('index')
            domain_trends = df.groupby('domain')['hallucination_score'].agg(['mean', 'count']).to_dict('index')
            language_trends = df.groupby('language')['hallucination_score'].agg(['mean', 'count']).to_dict('index')
            
            return {
                'time_window_hours': window_hours,
                'total_data_points': len(recent_data),
                'trend_direction': trend_direction,
                'trend_magnitude': trend_magnitude,
                'overall_stats': {
                    'avg_hallucination_score': df['hallucination_score'].mean(),
                    'std_hallucination_score': df['hallucination_score'].std(),
                    'avg_confidence': df['confidence'].mean(),
                    'high_risk_percentage': (df['hallucination_score'] > 0.7).mean() * 100
                },
                'time_series': grouped.to_dict('records'),
                'model_breakdown': model_trends,
                'domain_breakdown': domain_trends,
                'language_breakdown': language_trends,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Trend analysis error: {e}")
            return {'error': str(e)}

    def detect_anomalies(self, contamination: float = 0.1) -> List[AnalyticsInsight]:
        """
        Detect anomalies in hallucination patterns.
        
        Args:
            contamination: Expected proportion of anomalies
            
        Returns:
            List of anomaly insights
        """
        try:
            if len(self.data_buffer) < 20:
                return []
            
            # Prepare features for anomaly detection
            features = []
            timestamps = []
            
            for data in self.data_buffer:
                feature_vector = [
                    data.hallucination_score,
                    data.confidence,
                    hash(data.model_type) % 1000 / 1000.0,  # Normalize hash
                    hash(data.domain) % 1000 / 1000.0,
                    data.timestamp.hour / 24.0,  # Hour of day
                    data.timestamp.weekday() / 7.0  # Day of week
                ]
                features.append(feature_vector)
                timestamps.append(data.timestamp)
            
            # Standardize features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Detect anomalies using Isolation Forest
            iso_forest = IsolationForest(contamination=contamination, random_state=42)
            anomaly_labels = iso_forest.fit_predict(features_scaled)
            anomaly_scores = iso_forest.score_samples(features_scaled)
            
            # Create insights for anomalies
            insights = []
            for i, (label, score, timestamp, data) in enumerate(zip(
                anomaly_labels, anomaly_scores, timestamps, self.data_buffer
            )):
                if label == -1:  # Anomaly detected
                    severity = 'high' if score < -0.5 else 'medium'
                    
                    insight = AnalyticsInsight(
                        insight_type='anomaly',
                        severity=severity,
                        title=f'Anomalous hallucination pattern detected',
                        description=f'Unusual pattern in {data.model_type} model for {data.domain} domain',
                        confidence=abs(score),
                        data_points=1,
                        timestamp=timestamp,
                        recommendations=[
                            'Review model performance for this domain',
                            'Check for data quality issues',
                            'Consider model retraining if pattern persists'
                        ],
                        metadata={
                            'anomaly_score': score,
                            'hallucination_score': data.hallucination_score,
                            'model_type': data.model_type,
                            'domain': data.domain
                        }
                    )
                    insights.append(insight)
            
            return insights
            
        except Exception as e:
            logger.error(f"Anomaly detection error: {e}")
            return []

    def identify_patterns(self) -> List[AnalyticsInsight]:
        """
        Identify recurring patterns in hallucination data.
        
        Returns:
            List of pattern insights
        """
        try:
            if len(self.data_buffer) < self.config.pattern_min_samples:
                return []
            
            insights = []
            
            # Pattern 1: Time-based patterns
            hourly_scores = defaultdict(list)
            for data in self.data_buffer:
                hourly_scores[data.timestamp.hour].append(data.hallucination_score)
            
            # Find hours with consistently high scores
            high_risk_hours = []
            for hour, scores in hourly_scores.items():
                if len(scores) >= 3 and np.mean(scores) > 0.6:
                    high_risk_hours.append((hour, np.mean(scores)))
            
            if high_risk_hours:
                high_risk_hours.sort(key=lambda x: x[1], reverse=True)
                top_hour, avg_score = high_risk_hours[0]
                
                insight = AnalyticsInsight(
                    insight_type='pattern',
                    severity='medium' if avg_score > 0.7 else 'low',
                    title=f'High hallucination risk during hour {top_hour}:00',
                    description=f'Consistently elevated hallucination scores (avg: {avg_score:.3f}) detected during this time period',
                    confidence=0.8,
                    data_points=len(hourly_scores[top_hour]),
                    timestamp=datetime.now(),
                    recommendations=[
                        'Monitor model performance during this time period',
                        'Consider additional validation during peak risk hours',
                        'Investigate potential causes (data quality, system load, etc.)'
                    ],
                    metadata={'hour': top_hour, 'average_score': avg_score}
                )
                insights.append(insight)
            
            # Pattern 2: Model-domain combinations
            model_domain_scores = defaultdict(list)
            for data in self.data_buffer:
                key = f"{data.model_type}_{data.domain}"
                model_domain_scores[key].append(data.hallucination_score)
            
            # Find problematic combinations
            for combination, scores in model_domain_scores.items():
                if len(scores) >= 5 and np.mean(scores) > 0.65:
                    model_type, domain = combination.split('_', 1)
                    
                    insight = AnalyticsInsight(
                        insight_type='pattern',
                        severity='high' if np.mean(scores) > 0.75 else 'medium',
                        title=f'High hallucination risk: {model_type} + {domain}',
                        description=f'Model-domain combination shows elevated hallucination risk (avg: {np.mean(scores):.3f})',
                        confidence=0.85,
                        data_points=len(scores),
                        timestamp=datetime.now(),
                        recommendations=[
                            f'Review {model_type} model performance on {domain} domain',
                            'Consider domain-specific fine-tuning',
                            'Implement additional validation for this combination'
                        ],
                        metadata={
                            'model_type': model_type,
                            'domain': domain,
                            'average_score': np.mean(scores),
                            'score_std': np.std(scores)
                        }
                    )
                    insights.append(insight)
            
            return insights
            
        except Exception as e:
            logger.error(f"Pattern identification error: {e}")
            return []


class PredictiveAnalyzer:
    """
    Predictive analytics for hallucination detection.
    
    Features:
    - Time series forecasting
    - Risk prediction
    - Model performance prediction
    - Proactive alerting
    """
    
    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.models = {}
        self.feature_scalers = {}
        
    def train_prediction_model(self, 
                             historical_data: List[TrendData],
                             target_variable: str = 'hallucination_score') -> Dict[str, Any]:
        """
        Train predictive model on historical data.
        
        Args:
            historical_data: Historical trend data
            target_variable: Variable to predict
            
        Returns:
            Training results and model performance
        """
        try:
            if len(historical_data) < 50:
                return {'error': 'Insufficient data for model training'}
            
            # Prepare features and targets
            features = []
            targets = []
            
            for i, data in enumerate(historical_data[:-1]):  # Exclude last point
                # Create feature vector
                feature_vector = [
                    data.hallucination_score,
                    data.confidence,
                    data.timestamp.hour,
                    data.timestamp.weekday(),
                    hash(data.model_type) % 1000,
                    hash(data.domain) % 1000,
                    hash(data.language) % 1000
                ]
                
                # Look ahead for target (next data point)
                if i + 1 < len(historical_data):
                    target_value = getattr(historical_data[i + 1], target_variable)
                    
                    features.append(feature_vector)
                    targets.append(target_value)
            
            if len(features) < 20:
                return {'error': 'Insufficient feature data'}
            
            # Convert to numpy arrays
            X = np.array(features)
            y = np.array(targets)
            
            # Split data
            split_idx = int(0.8 * len(X))
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train Random Forest model
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            
            # Convert regression to classification (high/low risk)
            y_train_class = (y_train > 0.5).astype(int)
            y_test_class = (y_test > 0.5).astype(int)
            
            model.fit(X_train_scaled, y_train_class)
            
            # Evaluate model
            y_pred = model.predict(X_test_scaled)
            accuracy = (y_pred == y_test_class).mean()
            
            # Store model and scaler
            model_key = f"{target_variable}_predictor"
            self.models[model_key] = model
            self.feature_scalers[model_key] = scaler
            
            # Feature importance
            feature_names = [
                'hallucination_score', 'confidence', 'hour', 'weekday',
                'model_type_hash', 'domain_hash', 'language_hash'
            ]
            feature_importance = dict(zip(feature_names, model.feature_importances_))
            
            return {
                'model_key': model_key,
                'accuracy': accuracy,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'feature_importance': feature_importance,
                'target_variable': target_variable
            }
            
        except Exception as e:
            logger.error(f"Prediction model training error: {e}")
            return {'error': str(e)}

    def predict_future_risk(self, 
                          current_data: TrendData,
                          hours_ahead: int = 6) -> Optional[PredictionResult]:
        """
        Predict future hallucination risk.
        
        Args:
            current_data: Current data point
            hours_ahead: Hours to predict ahead
            
        Returns:
            Prediction result or None if model not available
        """
        try:
            model_key = "hallucination_score_predictor"
            
            if model_key not in self.models:
                return None
            
            model = self.models[model_key]
            scaler = self.feature_scalers[model_key]
            
            # Create feature vector for prediction
            future_time = current_data.timestamp + timedelta(hours=hours_ahead)
            feature_vector = [
                current_data.hallucination_score,
                current_data.confidence,
                future_time.hour,
                future_time.weekday(),
                hash(current_data.model_type) % 1000,
                hash(current_data.domain) % 1000,
                hash(current_data.language) % 1000
            ]
            
            # Scale features
            X = scaler.transform([feature_vector])
            
            # Make prediction
            prediction_proba = model.predict_proba(X)[0]
            prediction_class = model.predict(X)[0]
            
            # Convert back to score (approximate)
            predicted_score = prediction_proba[1]  # Probability of high risk
            
            # Estimate confidence interval (simplified)
            confidence_margin = 0.1 * (1 - max(prediction_proba))
            confidence_interval = (
                max(0.0, predicted_score - confidence_margin),
                min(1.0, predicted_score + confidence_margin)
            )
            
            return PredictionResult(
                prediction_type='hallucination_risk',
                predicted_value=predicted_score,
                confidence_interval=confidence_interval,
                time_horizon_hours=hours_ahead,
                features_importance={
                    'current_score': feature_vector[0],
                    'confidence': feature_vector[1],
                    'time_factors': feature_vector[2:4],
                    'context_factors': feature_vector[4:]
                },
                model_accuracy=0.8,  # Would be stored from training
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Risk prediction error: {e}")
            return None


class AnalyticsEngine:
    """
    Main analytics engine coordinating all analysis components.
    
    Provides comprehensive analytics including trends, anomalies,
    patterns, and predictions for hallucination detection.
    """
    
    def __init__(self, config: Optional[AnalyticsConfig] = None):
        """
        Initialize analytics engine.
        
        Args:
            config: Analytics configuration
        """
        self.config = config or AnalyticsConfig()
        
        # Initialize analyzers
        self.trend_analyzer = TrendAnalyzer(self.config)
        self.predictive_analyzer = PredictiveAnalyzer(self.config)
        
        # Analytics state
        self.insights_cache = []
        self.last_analysis_time = None
        
        logger.info("Analytics engine initialized")

    async def process_detection_result(self, 
                                     hallucination_score: float,
                                     confidence: float,
                                     model_type: str,
                                     domain: str = "general",
                                     language: str = "en",
                                     user_id: Optional[str] = None,
                                     metadata: Optional[Dict[str, Any]] = None):
        """
        Process a new detection result for analytics.
        
        Args:
            hallucination_score: Detected hallucination score
            confidence: Detection confidence
            model_type: Type of model used
            domain: Content domain
            language: Content language
            user_id: Optional user identifier
            metadata: Additional metadata
        """
        try:
            # Create trend data point
            trend_data = TrendData(
                timestamp=datetime.now(),
                hallucination_score=hallucination_score,
                confidence=confidence,
                model_type=model_type,
                domain=domain,
                language=language,
                user_id=user_id,
                metadata=metadata or {}
            )
            
            # Add to trend analyzer
            self.trend_analyzer.add_data_point(trend_data)
            
            # Trigger real-time analysis if enabled
            if self.config.enable_real_time_analysis:
                await self._run_real_time_analysis()
                
        except Exception as e:
            logger.error(f"Detection result processing error: {e}")

    async def _run_real_time_analysis(self):
        """Run real-time analysis on recent data."""
        try:
            # Only run analysis every few minutes to avoid overhead
            if (self.last_analysis_time and 
                datetime.now() - self.last_analysis_time < timedelta(minutes=5)):
                return
            
            # Detect anomalies
            if self.config.enable_anomaly_detection:
                anomaly_insights = self.trend_analyzer.detect_anomalies()
                self.insights_cache.extend(anomaly_insights)
            
            # Identify patterns
            pattern_insights = self.trend_analyzer.identify_patterns()
            self.insights_cache.extend(pattern_insights)
            
            # Keep only recent insights
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.insights_cache = [
                insight for insight in self.insights_cache
                if insight.timestamp >= cutoff_time
            ]
            
            self.last_analysis_time = datetime.now()
            
        except Exception as e:
            logger.error(f"Real-time analysis error: {e}")

    async def generate_analytics_report(self, 
                                      time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Generate comprehensive analytics report.
        
        Args:
            time_window_hours: Analysis time window
            
        Returns:
            Comprehensive analytics report
        """
        try:
            # Trend analysis
            trend_analysis = self.trend_analyzer.analyze_trends(time_window_hours)
            
            # Recent insights
            recent_insights = [
                asdict(insight) for insight in self.insights_cache
                if insight.timestamp >= datetime.now() - timedelta(hours=time_window_hours)
            ]
            
            # Summary statistics
            total_insights = len(recent_insights)
            critical_insights = len([i for i in recent_insights if i['severity'] == 'critical'])
            high_insights = len([i for i in recent_insights if i['severity'] == 'high'])
            
            # Recommendations
            recommendations = self._generate_recommendations(recent_insights, trend_analysis)
            
            return {
                'report_timestamp': datetime.now().isoformat(),
                'time_window_hours': time_window_hours,
                'summary': {
                    'total_insights': total_insights,
                    'critical_insights': critical_insights,
                    'high_priority_insights': high_insights,
                    'data_points_analyzed': trend_analysis.get('total_data_points', 0)
                },
                'trend_analysis': trend_analysis,
                'insights': recent_insights,
                'recommendations': recommendations,
                'analytics_config': asdict(self.config)
            }
            
        except Exception as e:
            logger.error(f"Analytics report generation error: {e}")
            return {
                'error': str(e),
                'report_timestamp': datetime.now().isoformat()
            }

    def _generate_recommendations(self, 
                                insights: List[Dict[str, Any]], 
                                trend_analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        try:
            # High-level trend recommendations
            if trend_analysis.get('trend_direction') == 'increasing':
                recommendations.append(
                    "Hallucination rates are increasing - consider model retraining or validation improvements"
                )
            
            # High risk percentage recommendations
            overall_stats = trend_analysis.get('overall_stats', {})
            high_risk_pct = overall_stats.get('high_risk_percentage', 0)
            
            if high_risk_pct > 20:
                recommendations.append(
                    f"High risk detections at {high_risk_pct:.1f}% - implement additional safeguards"
                )
            
            # Model-specific recommendations
            model_breakdown = trend_analysis.get('model_breakdown', {})
            for model, stats in model_breakdown.items():
                if stats['mean'] > 0.6:
                    recommendations.append(
                        f"Model '{model}' showing elevated hallucination scores - review performance"
                    )
            
            # Domain-specific recommendations
            domain_breakdown = trend_analysis.get('domain_breakdown', {})
            for domain, stats in domain_breakdown.items():
                if stats['mean'] > 0.6:
                    recommendations.append(
                        f"Domain '{domain}' showing elevated hallucination scores - consider domain-specific tuning"
                    )
            
            # Insight-based recommendations
            critical_insights = [i for i in insights if i['severity'] in ['critical', 'high']]
            if len(critical_insights) > 5:
                recommendations.append(
                    "Multiple critical insights detected - immediate investigation recommended"
                )
            
            # Default recommendations if none generated
            if not recommendations:
                recommendations.append("System performance appears normal - continue monitoring")
            
        except Exception as e:
            logger.error(f"Recommendation generation error: {e}")
            recommendations.append("Error generating recommendations - manual review suggested")
        
        return recommendations

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get quick analytics summary."""
        return {
            'total_data_points': len(self.trend_analyzer.data_buffer),
            'recent_insights': len(self.insights_cache),
            'last_analysis': self.last_analysis_time.isoformat() if self.last_analysis_time else None,
            'config': asdict(self.config)
        }


# Global analytics engine instance
_analytics_engine = None


def get_analytics_engine() -> AnalyticsEngine:
    """Get or create analytics engine instance."""
    global _analytics_engine
    if _analytics_engine is None:
        _analytics_engine = AnalyticsEngine()
    return _analytics_engine


if __name__ == "__main__":
    # Example usage
    async def test_analytics_engine():
        engine = AnalyticsEngine()
        
        # Simulate some detection results
        import random
        
        models = ['claude', 'statistical', 'ensemble']
        domains = ['general', 'technical', 'creative']
        languages = ['en', 'es', 'fr']
        
        for i in range(100):
            await engine.process_detection_result(
                hallucination_score=random.uniform(0.1, 0.9),
                confidence=random.uniform(0.6, 0.95),
                model_type=random.choice(models),
                domain=random.choice(domains),
                language=random.choice(languages)
            )
        
        # Generate report
        report = await engine.generate_analytics_report()
        print(f"Analytics Report: {json.dumps(report, indent=2, default=str)}")
        
        # Get summary
        summary = engine.get_analytics_summary()
        print(f"Analytics Summary: {json.dumps(summary, indent=2, default=str)}")
    
    # Run test
    # asyncio.run(test_analytics_engine())
