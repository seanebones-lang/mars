"""
Parental Controls and Age Prediction Service
Built-in filters for risky behavior and user age detection per GPT-5 2025 safety layers.

Provides family-friendly content filtering and age-appropriate interaction management
for education and family vertical markets.

Author: AgentGuard Engineering Team
Date: October 2025
Version: 1.0.0
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class AgeGroup(Enum):
    """Age group classifications."""
    CHILD = "child"  # 0-12 years
    TEEN = "teen"  # 13-17 years
    YOUNG_ADULT = "young_adult"  # 18-25 years
    ADULT = "adult"  # 26+ years
    UNKNOWN = "unknown"


class ContentRating(Enum):
    """Content rating levels."""
    EVERYONE = "everyone"  # G-rated, all ages
    EVERYONE_10_PLUS = "everyone_10_plus"  # E10+, mild content
    TEEN = "teen"  # T, 13+ appropriate
    MATURE = "mature"  # M, 17+ appropriate
    ADULTS_ONLY = "adults_only"  # AO, 18+ only
    UNRATED = "unrated"


class RiskLevel(Enum):
    """Risk level for content."""
    SAFE = "safe"
    LOW_RISK = "low_risk"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"
    BLOCKED = "blocked"


class RiskCategory(Enum):
    """Categories of risky content."""
    VIOLENCE = "violence"
    PROFANITY = "profanity"
    SEXUAL_CONTENT = "sexual_content"
    SUBSTANCE_USE = "substance_use"
    HATE_SPEECH = "hate_speech"
    BULLYING = "bullying"
    SELF_HARM = "self_harm"
    PERSONAL_INFO_SHARING = "personal_info_sharing"
    STRANGER_DANGER = "stranger_danger"
    INAPPROPRIATE_CONTACT = "inappropriate_contact"


@dataclass
class AgeDetectionResult:
    """Result of age detection analysis."""
    predicted_age_group: AgeGroup
    confidence: float
    indicators: List[str]
    explanation: str
    recommended_content_rating: ContentRating


@dataclass
class ContentFilterResult:
    """Result of content filtering."""
    is_appropriate: bool
    risk_level: RiskLevel
    risk_categories: List[RiskCategory]
    blocked_content: List[str]
    filtered_content: Optional[str]
    explanation: str
    recommendations: List[str]
    age_group: AgeGroup
    content_rating: ContentRating


class ParentalControlService:
    """
    Parental control service for family-friendly AI interactions.
    
    Provides:
    - Age prediction from interaction patterns
    - Content filtering based on age appropriateness
    - Risky behavior detection
    - Educational content recommendations
    - Family safety monitoring
    
    Designed for education and family vertical markets with
    COPPA and FERPA compliance considerations.
    """
    
    # Profanity patterns (mild to severe)
    PROFANITY_PATTERNS = [
        # Mild
        r"\b(damn|hell|crap|darn|heck)\b",
        # Moderate
        r"\b(ass|bastard|bitch|piss)\b",
        # Severe (blocked for all ages)
        r"\b(f[u\*]ck|sh[i\*]t|c[u\*]nt)\b",
    ]
    
    # Violence indicators
    VIOLENCE_PATTERNS = [
        r"\b(kill|murder|stab|shoot|gun|weapon|blood|gore|violence)\b",
        r"\b(attack|assault|fight|beat|hit|punch|kick)\b",
        r"\b(war|battle|combat|death|die|dead)\b",
    ]
    
    # Sexual content indicators
    SEXUAL_CONTENT_PATTERNS = [
        r"\b(sex|sexual|nude|naked|porn|xxx)\b",
        r"\b(breast|penis|vagina|genitals)\b",
        r"\b(intercourse|masturbat|orgasm)\b",
    ]
    
    # Substance use indicators
    SUBSTANCE_USE_PATTERNS = [
        r"\b(drug|cocaine|heroin|meth|marijuana|weed)\b",
        r"\b(alcohol|beer|wine|vodka|drunk|high)\b",
        r"\b(smoke|smoking|cigarette|vape|tobacco)\b",
    ]
    
    # Hate speech indicators
    HATE_SPEECH_PATTERNS = [
        r"\b(hate|racist|sexist|homophobic|bigot)\b",
        r"\b(nazi|kkk|supremacist)\b",
    ]
    
    # Bullying indicators
    BULLYING_PATTERNS = [
        r"\b(bully|loser|stupid|idiot|ugly|fat|worthless)\b",
        r"\b(kill yourself|kys|die)\b",
        r"\b(nobody likes you|everyone hates you)\b",
    ]
    
    # Self-harm indicators
    SELF_HARM_PATTERNS = [
        r"\b(suicide|suicidal|kill myself|end my life)\b",
        r"\b(cut myself|cutting|self.harm)\b",
        r"\b(want to die|better off dead)\b",
    ]
    
    # Personal info sharing (dangerous for children)
    PERSONAL_INFO_PATTERNS = [
        r"\b(my address is|i live at)\b",
        r"\b(my phone number|call me at)\b",
        r"\b(my school is|i go to)\b",
        r"\b(meet me at|come to my house)\b",
    ]
    
    # Age indicators (for age detection)
    AGE_INDICATORS = {
        AgeGroup.CHILD: [
            r"\b(kindergarten|elementary|grade [1-5])\b",
            r"\b(mommy|daddy|mom|dad)\b",
            r"\b(toys|playground|recess)\b",
            r"\b(cartoon|disney|pokemon)\b",
        ],
        AgeGroup.TEEN: [
            r"\b(middle school|high school|grade [6-9]|freshman|sophomore)\b",
            r"\b(homework|test|exam|teacher)\b",
            r"\b(tiktok|snapchat|instagram)\b",
            r"\b(crush|dating|boyfriend|girlfriend)\b",
        ],
        AgeGroup.YOUNG_ADULT: [
            r"\b(college|university|dorm|campus)\b",
            r"\b(major|degree|graduation)\b",
            r"\b(internship|job search|career)\b",
            r"\b(party|club|bar)\b",
        ],
        AgeGroup.ADULT: [
            r"\b(work|job|career|salary|mortgage)\b",
            r"\b(marriage|spouse|kids|children)\b",
            r"\b(retirement|401k|investment)\b",
            r"\b(taxes|insurance|bills)\b",
        ],
    }
    
    def __init__(self):
        """Initialize parental control service."""
        self._compile_patterns()
        logger.info("Parental control service initialized")
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching."""
        self.compiled_profanity = [
            re.compile(p, re.IGNORECASE) for p in self.PROFANITY_PATTERNS
        ]
        self.compiled_violence = [
            re.compile(p, re.IGNORECASE) for p in self.VIOLENCE_PATTERNS
        ]
        self.compiled_sexual = [
            re.compile(p, re.IGNORECASE) for p in self.SEXUAL_CONTENT_PATTERNS
        ]
        self.compiled_substance = [
            re.compile(p, re.IGNORECASE) for p in self.SUBSTANCE_USE_PATTERNS
        ]
        self.compiled_hate = [
            re.compile(p, re.IGNORECASE) for p in self.HATE_SPEECH_PATTERNS
        ]
        self.compiled_bullying = [
            re.compile(p, re.IGNORECASE) for p in self.BULLYING_PATTERNS
        ]
        self.compiled_self_harm = [
            re.compile(p, re.IGNORECASE) for p in self.SELF_HARM_PATTERNS
        ]
        self.compiled_personal_info = [
            re.compile(p, re.IGNORECASE) for p in self.PERSONAL_INFO_PATTERNS
        ]
        
        # Compile age indicators
        self.compiled_age_indicators = {}
        for age_group, patterns in self.AGE_INDICATORS.items():
            self.compiled_age_indicators[age_group] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
    
    def predict_age_group(
        self,
        text: str,
        interaction_history: Optional[List[str]] = None
    ) -> AgeDetectionResult:
        """
        Predict user's age group from interaction patterns.
        
        Args:
            text: Current text to analyze
            interaction_history: Optional list of previous interactions
            
        Returns:
            AgeDetectionResult with predicted age group
        """
        # Combine current text with history
        all_text = text
        if interaction_history:
            all_text = " ".join(interaction_history + [text])
        
        # Score each age group
        age_scores = {}
        age_indicators_found = {}
        
        for age_group, patterns in self.compiled_age_indicators.items():
            matches = []
            for pattern in patterns:
                found = pattern.findall(all_text)
                if found:
                    matches.extend(found)
            
            age_scores[age_group] = len(matches)
            age_indicators_found[age_group] = matches
        
        # Determine predicted age group
        if not any(age_scores.values()):
            predicted_age = AgeGroup.UNKNOWN
            confidence = 0.5
            indicators = []
        else:
            predicted_age = max(age_scores, key=age_scores.get)
            total_indicators = sum(age_scores.values())
            confidence = age_scores[predicted_age] / total_indicators if total_indicators > 0 else 0.5
            indicators = age_indicators_found[predicted_age]
        
        # Recommend content rating
        content_rating = self._age_to_content_rating(predicted_age)
        
        # Generate explanation
        explanation = self._generate_age_explanation(
            predicted_age, confidence, indicators
        )
        
        return AgeDetectionResult(
            predicted_age_group=predicted_age,
            confidence=confidence,
            indicators=indicators[:5],  # Top 5
            explanation=explanation,
            recommended_content_rating=content_rating
        )
    
    def filter_content(
        self,
        content: str,
        age_group: AgeGroup,
        strict_mode: bool = False
    ) -> ContentFilterResult:
        """
        Filter content based on age appropriateness.
        
        Args:
            content: Content to filter
            age_group: Target age group
            strict_mode: If True, apply stricter filtering
            
        Returns:
            ContentFilterResult with filtering assessment
        """
        risk_categories = []
        blocked_content = []
        risk_level = RiskLevel.SAFE
        
        # Check profanity
        profanity_matches = self._check_patterns(content, self.compiled_profanity)
        if profanity_matches:
            risk_categories.append(RiskCategory.PROFANITY)
            blocked_content.extend(profanity_matches)
            risk_level = self._escalate_risk(risk_level, RiskLevel.MEDIUM_RISK)
        
        # Check violence
        violence_matches = self._check_patterns(content, self.compiled_violence)
        if violence_matches:
            risk_categories.append(RiskCategory.VIOLENCE)
            blocked_content.extend(violence_matches)
            risk_level = self._escalate_risk(risk_level, RiskLevel.MEDIUM_RISK)
        
        # Check sexual content
        sexual_matches = self._check_patterns(content, self.compiled_sexual)
        if sexual_matches:
            risk_categories.append(RiskCategory.SEXUAL_CONTENT)
            blocked_content.extend(sexual_matches)
            risk_level = self._escalate_risk(risk_level, RiskLevel.HIGH_RISK)
        
        # Check substance use
        substance_matches = self._check_patterns(content, self.compiled_substance)
        if substance_matches:
            risk_categories.append(RiskCategory.SUBSTANCE_USE)
            blocked_content.extend(substance_matches)
            risk_level = self._escalate_risk(risk_level, RiskLevel.MEDIUM_RISK)
        
        # Check hate speech
        hate_matches = self._check_patterns(content, self.compiled_hate)
        if hate_matches:
            risk_categories.append(RiskCategory.HATE_SPEECH)
            blocked_content.extend(hate_matches)
            risk_level = self._escalate_risk(risk_level, RiskLevel.BLOCKED)
        
        # Check bullying
        bullying_matches = self._check_patterns(content, self.compiled_bullying)
        if bullying_matches:
            risk_categories.append(RiskCategory.BULLYING)
            blocked_content.extend(bullying_matches)
            risk_level = self._escalate_risk(risk_level, RiskLevel.HIGH_RISK)
        
        # Check self-harm (CRITICAL - always block)
        self_harm_matches = self._check_patterns(content, self.compiled_self_harm)
        if self_harm_matches:
            risk_categories.append(RiskCategory.SELF_HARM)
            blocked_content.extend(self_harm_matches)
            risk_level = RiskLevel.BLOCKED
        
        # Check personal info sharing (dangerous for children)
        if age_group in [AgeGroup.CHILD, AgeGroup.TEEN]:
            personal_info_matches = self._check_patterns(content, self.compiled_personal_info)
            if personal_info_matches:
                risk_categories.append(RiskCategory.PERSONAL_INFO_SHARING)
                blocked_content.extend(personal_info_matches)
                risk_level = self._escalate_risk(risk_level, RiskLevel.BLOCKED)
        
        # Determine if content is appropriate for age group
        is_appropriate = self._is_appropriate_for_age(
            risk_level, risk_categories, age_group, strict_mode
        )
        
        # Filter content if needed
        filtered_content = None
        if not is_appropriate and risk_level != RiskLevel.BLOCKED:
            filtered_content = self._apply_content_filter(content, blocked_content)
        
        # Get content rating
        content_rating = self._determine_content_rating(risk_categories)
        
        # Generate explanation
        explanation = self._generate_filter_explanation(
            is_appropriate, risk_level, risk_categories, age_group
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            risk_categories, age_group, is_appropriate
        )
        
        return ContentFilterResult(
            is_appropriate=is_appropriate,
            risk_level=risk_level,
            risk_categories=risk_categories,
            blocked_content=blocked_content[:10],  # Limit to 10
            filtered_content=filtered_content,
            explanation=explanation,
            recommendations=recommendations,
            age_group=age_group,
            content_rating=content_rating
        )
    
    def _check_patterns(self, text: str, patterns: List[re.Pattern]) -> List[str]:
        """Check text against compiled patterns."""
        matches = []
        for pattern in patterns:
            found = pattern.findall(text)
            if found:
                matches.extend([match if isinstance(match, str) else match[0] for match in found])
        return matches
    
    def _escalate_risk(self, current: RiskLevel, new: RiskLevel) -> RiskLevel:
        """Escalate risk level if new risk is higher."""
        risk_order = [
            RiskLevel.SAFE,
            RiskLevel.LOW_RISK,
            RiskLevel.MEDIUM_RISK,
            RiskLevel.HIGH_RISK,
            RiskLevel.BLOCKED
        ]
        
        current_index = risk_order.index(current)
        new_index = risk_order.index(new)
        
        return risk_order[max(current_index, new_index)]
    
    def _is_appropriate_for_age(
        self,
        risk_level: RiskLevel,
        risk_categories: List[RiskCategory],
        age_group: AgeGroup,
        strict_mode: bool
    ) -> bool:
        """Determine if content is appropriate for age group."""
        # Always block BLOCKED content
        if risk_level == RiskLevel.BLOCKED:
            return False
        
        # Self-harm always blocked
        if RiskCategory.SELF_HARM in risk_categories:
            return False
        
        # Age-specific rules
        if age_group == AgeGroup.CHILD:
            # Children: only SAFE content
            return risk_level == RiskLevel.SAFE
        
        elif age_group == AgeGroup.TEEN:
            # Teens: SAFE and LOW_RISK, or MEDIUM_RISK if not strict
            if strict_mode:
                return risk_level in [RiskLevel.SAFE, RiskLevel.LOW_RISK]
            else:
                return risk_level != RiskLevel.HIGH_RISK
        
        elif age_group == AgeGroup.YOUNG_ADULT:
            # Young adults: all except BLOCKED
            return risk_level != RiskLevel.BLOCKED
        
        elif age_group == AgeGroup.ADULT:
            # Adults: all except BLOCKED
            return risk_level != RiskLevel.BLOCKED
        
        else:  # UNKNOWN
            # Default to teen rules
            return risk_level in [RiskLevel.SAFE, RiskLevel.LOW_RISK]
    
    def _apply_content_filter(self, content: str, blocked_terms: List[str]) -> str:
        """Apply content filter by replacing blocked terms."""
        filtered = content
        for term in blocked_terms:
            # Replace with asterisks
            filtered = re.sub(
                re.escape(term),
                '*' * len(term),
                filtered,
                flags=re.IGNORECASE
            )
        return filtered
    
    def _age_to_content_rating(self, age_group: AgeGroup) -> ContentRating:
        """Convert age group to content rating."""
        mapping = {
            AgeGroup.CHILD: ContentRating.EVERYONE,
            AgeGroup.TEEN: ContentRating.TEEN,
            AgeGroup.YOUNG_ADULT: ContentRating.MATURE,
            AgeGroup.ADULT: ContentRating.MATURE,
            AgeGroup.UNKNOWN: ContentRating.EVERYONE_10_PLUS
        }
        return mapping.get(age_group, ContentRating.UNRATED)
    
    def _determine_content_rating(self, risk_categories: List[RiskCategory]) -> ContentRating:
        """Determine content rating based on risk categories."""
        if not risk_categories:
            return ContentRating.EVERYONE
        
        # Severe content
        severe = [
            RiskCategory.SEXUAL_CONTENT,
            RiskCategory.HATE_SPEECH,
            RiskCategory.SELF_HARM
        ]
        if any(cat in risk_categories for cat in severe):
            return ContentRating.ADULTS_ONLY
        
        # Mature content
        mature = [
            RiskCategory.VIOLENCE,
            RiskCategory.SUBSTANCE_USE,
            RiskCategory.BULLYING
        ]
        if any(cat in risk_categories for cat in mature):
            return ContentRating.MATURE
        
        # Teen content
        if RiskCategory.PROFANITY in risk_categories:
            return ContentRating.TEEN
        
        return ContentRating.EVERYONE_10_PLUS
    
    def _generate_age_explanation(
        self,
        age_group: AgeGroup,
        confidence: float,
        indicators: List[str]
    ) -> str:
        """Generate explanation for age prediction."""
        if age_group == AgeGroup.UNKNOWN:
            return "Unable to determine age group from provided interactions."
        
        indicator_text = ", ".join(indicators[:3]) if indicators else "general patterns"
        
        return (
            f"Predicted age group: {age_group.value} "
            f"(confidence: {confidence:.0%}) based on indicators: {indicator_text}"
        )
    
    def _generate_filter_explanation(
        self,
        is_appropriate: bool,
        risk_level: RiskLevel,
        risk_categories: List[RiskCategory],
        age_group: AgeGroup
    ) -> str:
        """Generate explanation for content filtering."""
        if is_appropriate:
            return f"Content is appropriate for {age_group.value} age group."
        
        categories = ", ".join([cat.value for cat in risk_categories])
        
        return (
            f"Content is NOT appropriate for {age_group.value} age group. "
            f"Risk level: {risk_level.value}. "
            f"Detected: {categories}"
        )
    
    def _generate_recommendations(
        self,
        risk_categories: List[RiskCategory],
        age_group: AgeGroup,
        is_appropriate: bool
    ) -> List[str]:
        """Generate recommendations for content handling."""
        recommendations = []
        
        if not is_appropriate:
            recommendations.append("Block or filter this content before displaying to user")
            recommendations.append(f"Content not suitable for {age_group.value} age group")
        
        if RiskCategory.SELF_HARM in risk_categories:
            recommendations.append("CRITICAL: Self-harm content detected - provide crisis resources")
            recommendations.append("Contact: National Suicide Prevention Lifeline 988")
        
        if RiskCategory.BULLYING in risk_categories:
            recommendations.append("Bullying detected - consider alerting parents/guardians")
        
        if RiskCategory.PERSONAL_INFO_SHARING in risk_categories:
            recommendations.append("Personal information sharing detected - educate about online safety")
        
        if RiskCategory.HATE_SPEECH in risk_categories:
            recommendations.append("Hate speech detected - block and report")
        
        return recommendations

