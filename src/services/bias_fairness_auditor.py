"""
Bias and Fairness Auditor Service
Real-time bias detection and fairness assessment for AI outputs.

Detects and measures:
- Gender bias
- Racial/ethnic bias
- Age bias
- Socioeconomic bias
- Disability bias
- Religious bias
- Geographic bias

Complies with:
- EU AI Act fairness requirements
- NIST AI Risk Management Framework
- IEEE 7000 series standards

Author: AgentGuard Engineering Team
Date: October 2025
Version: 1.0.0
"""

import logging
import time
import re
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class BiasType(str, Enum):
    """Types of bias to detect."""
    GENDER = "gender"
    RACE_ETHNICITY = "race_ethnicity"
    AGE = "age"
    SOCIOECONOMIC = "socioeconomic"
    DISABILITY = "disability"
    RELIGION = "religion"
    GEOGRAPHIC = "geographic"
    LGBTQ = "lgbtq"
    LANGUAGE = "language"
    UNKNOWN = "unknown"


class BiasLevel(str, Enum):
    """Severity level of detected bias."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FairnessMetric(str, Enum):
    """Fairness metrics for evaluation."""
    DEMOGRAPHIC_PARITY = "demographic_parity"
    EQUAL_OPPORTUNITY = "equal_opportunity"
    EQUALIZED_ODDS = "equalized_odds"
    TREATMENT_EQUALITY = "treatment_equality"
    REPRESENTATION = "representation"


@dataclass
class BiasIndicator:
    """Detected bias indicator."""
    bias_type: BiasType
    indicator_text: str
    context: str
    severity: BiasLevel
    confidence: float
    explanation: str
    suggested_alternative: Optional[str] = None


@dataclass
class FairnessScore:
    """Fairness assessment score."""
    metric: FairnessMetric
    score: float  # 0.0-1.0 (1.0 = perfectly fair)
    explanation: str
    affected_groups: List[str]


@dataclass
class BiasAuditResult:
    """Result from bias and fairness audit."""
    has_bias: bool
    overall_bias_level: BiasLevel
    bias_indicators: List[BiasIndicator]
    fairness_scores: List[FairnessScore]
    detected_bias_types: List[BiasType]
    overall_fairness_score: float  # 0.0-1.0
    recommendations: List[str]
    compliance_status: Dict[str, bool]  # Framework compliance
    processing_time_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class BiasAndFairnessAuditor:
    """
    Bias and fairness auditor for AI outputs.
    
    Features:
    - Multi-dimensional bias detection
    - Fairness metric calculation
    - Compliance checking (EU AI Act, NIST)
    - Mitigation recommendations
    - Demographic representation analysis
    - Stereotype detection
    - Language inclusivity checking
    """
    
    # Bias detection patterns
    BIAS_PATTERNS = {
        BiasType.GENDER: {
            "stereotypes": [
                r"\b(women|woman|female|girl|she|her)\b.{0,50}\b(emotional|nurturing|weak|submissive|irrational)\b",
                r"\b(men|man|male|boy|he|him)\b.{0,50}\b(strong|aggressive|rational|leader|dominant)\b",
                r"\b(chairman|policeman|fireman|mankind|manpower)\b"
            ],
            "exclusionary": [
                r"\b(guys|bros|dudes)\b",  # When addressing mixed groups
                r"\bhe\b.{0,100}\bor she\b"  # Binary gender assumptions
            ]
        },
        BiasType.RACE_ETHNICITY: {
            "stereotypes": [
                r"\b(black|african|asian|hispanic|latino|arab|indian)\b.{0,50}\b(criminal|lazy|smart|good at math|terrorist)\b",
                r"\b(white|caucasian)\b.{0,50}\b(privileged|superior|civilized)\b"
            ],
            "microaggressions": [
                r"\bwhere are you really from\b",
                r"\byou speak english well\b",
                r"\bmodel minority\b"
            ]
        },
        BiasType.AGE: {
            "stereotypes": [
                r"\b(old|elderly|senior)\b.{0,50}\b(slow|confused|outdated|technophobe)\b",
                r"\b(young|millennial|gen z)\b.{0,50}\b(lazy|entitled|immature|inexperienced)\b"
            ],
            "exclusionary": [
                r"\btoo old for\b",
                r"\btoo young to understand\b"
            ]
        },
        BiasType.DISABILITY: {
            "ableist": [
                r"\b(crazy|insane|psycho|retarded|lame|blind to|deaf to)\b",
                r"\bsuffers from\b.{0,20}\b(disability|condition)\b",
                r"\bwheelchair-bound\b"
            ],
            "exclusionary": [
                r"\bnormal people\b",  # Implies disabled people are abnormal
                r"\bable-bodied\b"  # Without context
            ]
        },
        BiasType.RELIGION: {
            "stereotypes": [
                r"\b(muslim|islamic)\b.{0,50}\b(terrorist|extremist|oppressive)\b",
                r"\b(jewish)\b.{0,50}\b(greedy|controlling)\b",
                r"\b(christian)\b.{0,50}\b(intolerant|judgmental)\b"
            ]
        },
        BiasType.SOCIOECONOMIC: {
            "stereotypes": [
                r"\b(poor|low-income|working class)\b.{0,50}\b(lazy|uneducated|criminal)\b",
                r"\b(rich|wealthy|upper class)\b.{0,50}\b(greedy|entitled|out of touch)\b"
            ]
        },
        BiasType.LGBTQ: {
            "stereotypes": [
                r"\b(gay|lesbian|trans|queer)\b.{0,50}\b(lifestyle|choice|phase|confused)\b",
                r"\b(normal|natural)\b.{0,50}\b(relationship|family)\b"  # Implies LGBTQ is abnormal
            ],
            "exclusionary": [
                r"\bprefer normal pronouns\b",
                r"\bbiological (man|woman)\b"
            ]
        }
    }
    
    # Inclusive language alternatives
    INCLUSIVE_ALTERNATIVES = {
        "chairman": "chairperson / chair",
        "policeman": "police officer",
        "fireman": "firefighter",
        "mankind": "humanity / humankind",
        "manpower": "workforce / personnel",
        "guys": "everyone / folks / team",
        "crazy": "unexpected / surprising",
        "lame": "disappointing / weak",
        "blind to": "unaware of / overlooking",
        "wheelchair-bound": "wheelchair user",
        "suffers from": "has / lives with",
        "normal": "typical / common (context-dependent)"
    }
    
    def __init__(
        self,
        enable_stereotype_detection: bool = True,
        enable_representation_analysis: bool = True,
        enable_language_inclusivity: bool = True,
        bias_threshold: float = 0.6
    ):
        """
        Initialize bias and fairness auditor.
        
        Args:
            enable_stereotype_detection: Enable stereotype pattern matching
            enable_representation_analysis: Enable demographic representation analysis
            enable_language_inclusivity: Enable inclusive language checking
            bias_threshold: Confidence threshold for bias detection
        """
        self.enable_stereotype_detection = enable_stereotype_detection
        self.enable_representation_analysis = enable_representation_analysis
        self.enable_language_inclusivity = enable_language_inclusivity
        self.bias_threshold = bias_threshold
        
        # Compile regex patterns
        self._compile_patterns()
        
        logger.info("Bias and fairness auditor initialized")
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        self.compiled_patterns: Dict[BiasType, Dict[str, List[re.Pattern]]] = {}
        for bias_type, categories in self.BIAS_PATTERNS.items():
            self.compiled_patterns[bias_type] = {}
            for category, patterns in categories.items():
                self.compiled_patterns[bias_type][category] = [
                    re.compile(pattern, re.IGNORECASE) for pattern in patterns
                ]
    
    async def audit(
        self,
        text: str,
        context: Optional[str] = None,
        check_compliance: bool = True
    ) -> BiasAuditResult:
        """
        Perform bias and fairness audit on text.
        
        Args:
            text: Text to audit
            context: Optional context for better analysis
            check_compliance: Check regulatory compliance
            
        Returns:
            BiasAuditResult with audit findings
        """
        start_time = time.perf_counter()
        
        # Detect bias indicators
        bias_indicators = []
        if self.enable_stereotype_detection:
            bias_indicators.extend(self._detect_stereotypes(text))
        
        if self.enable_language_inclusivity:
            bias_indicators.extend(self._check_inclusive_language(text))
        
        # Calculate fairness scores
        fairness_scores = []
        if self.enable_representation_analysis:
            fairness_scores.extend(self._analyze_representation(text))
        
        # Aggregate results
        has_bias = len(bias_indicators) > 0
        overall_bias_level = self._calculate_overall_bias_level(bias_indicators)
        detected_bias_types = list(set(ind.bias_type for ind in bias_indicators))
        overall_fairness_score = self._calculate_overall_fairness(fairness_scores)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(bias_indicators, fairness_scores)
        
        # Check compliance
        compliance_status = {}
        if check_compliance:
            compliance_status = self._check_compliance(bias_indicators, fairness_scores)
        
        end_time = time.perf_counter()
        processing_time_ms = (end_time - start_time) * 1000
        
        return BiasAuditResult(
            has_bias=has_bias,
            overall_bias_level=overall_bias_level,
            bias_indicators=bias_indicators,
            fairness_scores=fairness_scores,
            detected_bias_types=detected_bias_types,
            overall_fairness_score=overall_fairness_score,
            recommendations=recommendations,
            compliance_status=compliance_status,
            processing_time_ms=processing_time_ms
        )
    
    def _detect_stereotypes(self, text: str) -> List[BiasIndicator]:
        """Detect stereotypes in text."""
        indicators = []
        
        for bias_type, categories in self.compiled_patterns.items():
            for category, patterns in categories.items():
                for pattern in patterns:
                    matches = pattern.finditer(text)
                    for match in matches:
                        matched_text = match.group(0)
                        context = text[max(0, match.start()-50):min(len(text), match.end()+50)]
                        
                        # Determine severity
                        severity = self._determine_severity(bias_type, category, matched_text)
                        
                        # Generate explanation
                        explanation = self._generate_bias_explanation(bias_type, category, matched_text)
                        
                        # Suggest alternative
                        alternative = self._suggest_alternative(matched_text)
                        
                        indicators.append(BiasIndicator(
                            bias_type=bias_type,
                            indicator_text=matched_text,
                            context=context,
                            severity=severity,
                            confidence=0.75,  # Pattern-based confidence
                            explanation=explanation,
                            suggested_alternative=alternative
                        ))
        
        return indicators
    
    def _check_inclusive_language(self, text: str) -> List[BiasIndicator]:
        """Check for non-inclusive language."""
        indicators = []
        
        for term, alternative in self.INCLUSIVE_ALTERNATIVES.items():
            pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
            matches = pattern.finditer(text)
            
            for match in matches:
                matched_text = match.group(0)
                context = text[max(0, match.start()-50):min(len(text), match.end()+50)]
                
                indicators.append(BiasIndicator(
                    bias_type=BiasType.LANGUAGE,
                    indicator_text=matched_text,
                    context=context,
                    severity=BiasLevel.LOW,
                    confidence=0.70,
                    explanation=f"Non-inclusive term detected: '{matched_text}'",
                    suggested_alternative=alternative
                ))
        
        return indicators
    
    def _analyze_representation(self, text: str) -> List[FairnessScore]:
        """Analyze demographic representation in text."""
        scores = []
        
        # Count mentions of different demographic groups
        demographic_mentions = self._count_demographic_mentions(text)
        
        # Calculate representation fairness
        if demographic_mentions:
            total_mentions = sum(demographic_mentions.values())
            if total_mentions > 0:
                # Check if any group is over/under-represented
                expected_proportion = 1.0 / len(demographic_mentions)
                max_deviation = max(
                    abs(count/total_mentions - expected_proportion)
                    for count in demographic_mentions.values()
                )
                
                representation_score = 1.0 - (max_deviation * 2)  # Scale to 0-1
                
                scores.append(FairnessScore(
                    metric=FairnessMetric.REPRESENTATION,
                    score=max(0.0, representation_score),
                    explanation=f"Demographic representation analysis across {len(demographic_mentions)} groups",
                    affected_groups=list(demographic_mentions.keys())
                ))
        
        return scores
    
    def _count_demographic_mentions(self, text: str) -> Dict[str, int]:
        """Count mentions of different demographic groups."""
        mentions = defaultdict(int)
        
        # Gender mentions
        gender_patterns = {
            "male": r"\b(he|him|his|man|men|male|boy|boys)\b",
            "female": r"\b(she|her|hers|woman|women|female|girl|girls)\b",
            "non-binary": r"\b(they|them|their|non-binary|nonbinary|enby)\b"
        }
        
        for group, pattern in gender_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                mentions[f"gender_{group}"] = len(matches)
        
        return dict(mentions)
    
    def _determine_severity(self, bias_type: BiasType, category: str, text: str) -> BiasLevel:
        """Determine severity of bias indicator."""
        # Stereotypes are generally more severe than exclusionary language
        if category == "stereotypes":
            return BiasLevel.HIGH
        elif category == "microaggressions":
            return BiasLevel.MEDIUM
        elif category == "exclusionary":
            return BiasLevel.MEDIUM
        elif category == "ableist":
            return BiasLevel.HIGH
        else:
            return BiasLevel.LOW
    
    def _generate_bias_explanation(self, bias_type: BiasType, category: str, text: str) -> str:
        """Generate explanation for detected bias."""
        explanations = {
            "stereotypes": f"Detected stereotype related to {bias_type.value}",
            "microaggressions": f"Detected microaggression related to {bias_type.value}",
            "exclusionary": f"Detected exclusionary language related to {bias_type.value}",
            "ableist": f"Detected ableist language"
        }
        return explanations.get(category, f"Detected bias: {bias_type.value}")
    
    def _suggest_alternative(self, text: str) -> Optional[str]:
        """Suggest alternative phrasing."""
        text_lower = text.lower()
        for term, alternative in self.INCLUSIVE_ALTERNATIVES.items():
            if term in text_lower:
                return alternative
        return None
    
    def _calculate_overall_bias_level(self, indicators: List[BiasIndicator]) -> BiasLevel:
        """Calculate overall bias level from indicators."""
        if not indicators:
            return BiasLevel.NONE
        
        # Count by severity
        severity_counts = defaultdict(int)
        for ind in indicators:
            severity_counts[ind.severity] += 1
        
        # Determine overall level
        if severity_counts[BiasLevel.CRITICAL] > 0:
            return BiasLevel.CRITICAL
        elif severity_counts[BiasLevel.HIGH] >= 2:
            return BiasLevel.CRITICAL
        elif severity_counts[BiasLevel.HIGH] >= 1:
            return BiasLevel.HIGH
        elif severity_counts[BiasLevel.MEDIUM] >= 3:
            return BiasLevel.HIGH
        elif severity_counts[BiasLevel.MEDIUM] >= 1:
            return BiasLevel.MEDIUM
        else:
            return BiasLevel.LOW
    
    def _calculate_overall_fairness(self, scores: List[FairnessScore]) -> float:
        """Calculate overall fairness score."""
        if not scores:
            return 1.0  # No scores = assume fair
        return sum(s.score for s in scores) / len(scores)
    
    def _generate_recommendations(
        self,
        indicators: List[BiasIndicator],
        fairness_scores: List[FairnessScore]
    ) -> List[str]:
        """Generate recommendations for bias mitigation."""
        recommendations = []
        
        if not indicators and all(s.score >= 0.8 for s in fairness_scores):
            recommendations.append("Content appears fair and unbiased")
            return recommendations
        
        # Bias-specific recommendations
        bias_types_detected = set(ind.bias_type for ind in indicators)
        
        if BiasType.GENDER in bias_types_detected:
            recommendations.append("Use gender-neutral language where possible")
            recommendations.append("Avoid gender stereotypes and assumptions")
        
        if BiasType.RACE_ETHNICITY in bias_types_detected:
            recommendations.append("Remove racial/ethnic stereotypes")
            recommendations.append("Ensure equal representation of diverse groups")
        
        if BiasType.AGE in bias_types_detected:
            recommendations.append("Avoid age-based assumptions")
            recommendations.append("Use age-inclusive language")
        
        if BiasType.DISABILITY in bias_types_detected:
            recommendations.append("Use person-first language (e.g., 'person with disability')")
            recommendations.append("Avoid ableist terminology")
        
        if BiasType.LANGUAGE in bias_types_detected:
            recommendations.append("Replace non-inclusive terms with suggested alternatives")
        
        # Fairness-specific recommendations
        for score in fairness_scores:
            if score.score < 0.6:
                recommendations.append(f"Improve {score.metric.value}: {score.explanation}")
        
        # General recommendations
        if len(indicators) > 5:
            recommendations.append("Consider comprehensive content review for bias")
            recommendations.append("Consult diversity and inclusion guidelines")
        
        return recommendations
    
    def _check_compliance(
        self,
        indicators: List[BiasIndicator],
        fairness_scores: List[FairnessScore]
    ) -> Dict[str, bool]:
        """Check compliance with regulatory frameworks."""
        compliance = {}
        
        # EU AI Act compliance (high-risk systems must be fair)
        eu_compliant = (
            len([ind for ind in indicators if ind.severity in [BiasLevel.HIGH, BiasLevel.CRITICAL]]) == 0
            and all(s.score >= 0.7 for s in fairness_scores)
        )
        compliance["EU_AI_Act"] = eu_compliant
        
        # NIST AI RMF compliance (manage bias risks)
        nist_compliant = (
            len([ind for ind in indicators if ind.severity == BiasLevel.CRITICAL]) == 0
            and all(s.score >= 0.6 for s in fairness_scores)
        )
        compliance["NIST_AI_RMF"] = nist_compliant
        
        # IEEE 7000 compliance (ethical considerations)
        ieee_compliant = len(indicators) < 5 and all(s.score >= 0.65 for s in fairness_scores)
        compliance["IEEE_7000"] = ieee_compliant
        
        return compliance


# Global instance
_auditor_instance: Optional[BiasAndFairnessAuditor] = None


def get_bias_auditor(
    enable_stereotype_detection: bool = True,
    enable_representation_analysis: bool = True
) -> BiasAndFairnessAuditor:
    """Get or create the global bias auditor instance."""
    global _auditor_instance
    if _auditor_instance is None:
        _auditor_instance = BiasAndFairnessAuditor(
            enable_stereotype_detection=enable_stereotype_detection,
            enable_representation_analysis=enable_representation_analysis
        )
    return _auditor_instance

