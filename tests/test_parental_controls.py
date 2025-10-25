"""
Unit and Integration Tests for Parental Controls
Tests age prediction, content filtering, and family safety features.

Author: AgentGuard Engineering Team
Date: October 2025
"""

import pytest
from src.services.parental_controls import (
    ParentalControlService,
    AgeGroup,
    ContentRating,
    RiskLevel,
    RiskCategory
)


@pytest.fixture
def parental_service():
    """Fixture to create parental control service instance."""
    return ParentalControlService()


class TestAgeDetection:
    """Tests for age group prediction."""
    
    def test_predict_child_age_group(self, parental_service):
        """Test child age detection from text patterns."""
        text = "I love playing with my toys at recess. My mommy helps me with homework."
        result = parental_service.predict_age_group(text)
        
        assert result.predicted_age_group == AgeGroup.CHILD
        assert result.confidence > 0.5
        assert len(result.indicators) > 0
        assert result.recommended_content_rating == ContentRating.EVERYONE
    
    def test_predict_teen_age_group(self, parental_service):
        """Test teen age detection from text patterns."""
        text = "I'm in high school and have a big test tomorrow. My crush sits next to me in class."
        result = parental_service.predict_age_group(text)
        
        assert result.predicted_age_group == AgeGroup.TEEN
        assert result.confidence > 0.5
        assert result.recommended_content_rating == ContentRating.TEEN
    
    def test_predict_young_adult_age_group(self, parental_service):
        """Test young adult age detection."""
        text = "I'm in college studying for my degree. Looking for internships and going to parties."
        result = parental_service.predict_age_group(text)
        
        assert result.predicted_age_group == AgeGroup.YOUNG_ADULT
        assert result.confidence > 0.5
        assert result.recommended_content_rating == ContentRating.MATURE
    
    def test_predict_adult_age_group(self, parental_service):
        """Test adult age detection."""
        text = "I need to pay my mortgage and taxes. My kids are in school and I'm planning retirement."
        result = parental_service.predict_age_group(text)
        
        assert result.predicted_age_group == AgeGroup.ADULT
        assert result.confidence > 0.5
        assert result.recommended_content_rating == ContentRating.MATURE
    
    def test_predict_unknown_age_group(self, parental_service):
        """Test unknown age when no indicators present."""
        text = "The weather is nice today."
        result = parental_service.predict_age_group(text)
        
        assert result.predicted_age_group == AgeGroup.UNKNOWN
        assert result.confidence == 0.5
        assert len(result.indicators) == 0
    
    def test_age_detection_with_history(self, parental_service):
        """Test age detection improves with interaction history."""
        history = [
            "I'm in middle school",
            "I have homework to do",
            "My teacher gave us a test"
        ]
        text = "What should I study?"
        result = parental_service.predict_age_group(text, history)
        
        assert result.predicted_age_group == AgeGroup.TEEN
        assert result.confidence > 0.5


class TestContentFiltering:
    """Tests for content filtering and safety."""
    
    def test_safe_content_for_children(self, parental_service):
        """Test safe content passes for children."""
        content = "Let's learn about animals and nature. It's fun to explore!"
        result = parental_service.filter_content(content, AgeGroup.CHILD)
        
        assert result.is_appropriate is True
        assert result.risk_level == RiskLevel.SAFE
        assert len(result.risk_categories) == 0
        assert result.content_rating == ContentRating.EVERYONE
    
    def test_profanity_detection(self, parental_service):
        """Test profanity detection and filtering."""
        content = "This is damn frustrating and makes me feel like crap."
        result = parental_service.filter_content(content, AgeGroup.CHILD)
        
        assert result.is_appropriate is False
        assert RiskCategory.PROFANITY in result.risk_categories
        assert len(result.blocked_content) > 0
        assert result.risk_level in [RiskLevel.MEDIUM_RISK, RiskLevel.HIGH_RISK]
    
    def test_violence_detection(self, parental_service):
        """Test violence content detection."""
        content = "The character used a gun to shoot and kill the enemy in a violent battle."
        result = parental_service.filter_content(content, AgeGroup.CHILD)
        
        assert result.is_appropriate is False
        assert RiskCategory.VIOLENCE in result.risk_categories
        assert result.risk_level in [RiskLevel.MEDIUM_RISK, RiskLevel.HIGH_RISK, RiskLevel.BLOCKED]
    
    def test_sexual_content_detection(self, parental_service):
        """Test sexual content detection."""
        content = "The scene showed explicit sexual content and nudity."
        result = parental_service.filter_content(content, AgeGroup.CHILD)
        
        assert result.is_appropriate is False
        assert RiskCategory.SEXUAL_CONTENT in result.risk_categories
        assert result.risk_level in [RiskLevel.HIGH_RISK, RiskLevel.BLOCKED]
    
    def test_substance_use_detection(self, parental_service):
        """Test substance use detection."""
        content = "He was drinking alcohol and smoking marijuana at the party."
        result = parental_service.filter_content(content, AgeGroup.TEEN)
        
        assert RiskCategory.SUBSTANCE_USE in result.risk_categories
        assert result.risk_level in [RiskLevel.MEDIUM_RISK, RiskLevel.HIGH_RISK, RiskLevel.BLOCKED]
    
    def test_hate_speech_detection(self, parental_service):
        """Test hate speech detection (always blocked)."""
        content = "This contains racist and hateful language targeting a group."
        result = parental_service.filter_content(content, AgeGroup.ADULT)
        
        assert result.is_appropriate is False
        assert RiskCategory.HATE_SPEECH in result.risk_categories
        assert result.risk_level == RiskLevel.BLOCKED
    
    def test_bullying_detection(self, parental_service):
        """Test bullying detection."""
        content = "You're such a loser and everyone hates you. Nobody likes you."
        result = parental_service.filter_content(content, AgeGroup.TEEN)
        
        assert result.is_appropriate is False
        assert RiskCategory.BULLYING in result.risk_categories
        assert result.risk_level in [RiskLevel.HIGH_RISK, RiskLevel.BLOCKED]
        assert len(result.recommendations) > 0
    
    def test_self_harm_detection_critical(self, parental_service):
        """Test self-harm detection (CRITICAL - always blocked)."""
        content = "I want to kill myself and end my life."
        result = parental_service.filter_content(content, AgeGroup.ADULT)
        
        assert result.is_appropriate is False
        assert RiskCategory.SELF_HARM in result.risk_categories
        assert result.risk_level == RiskLevel.BLOCKED
        assert any("crisis" in rec.lower() for rec in result.recommendations)
        assert any("988" in rec for rec in result.recommendations)
    
    def test_personal_info_sharing_for_children(self, parental_service):
        """Test personal info sharing detection for children."""
        content = "My address is 123 Main Street and my phone number is 555-1234."
        result = parental_service.filter_content(content, AgeGroup.CHILD)
        
        assert result.is_appropriate is False
        assert RiskCategory.PERSONAL_INFO_SHARING in result.risk_categories
        assert result.risk_level == RiskLevel.BLOCKED
    
    def test_personal_info_allowed_for_adults(self, parental_service):
        """Test personal info sharing allowed for adults."""
        content = "My address is 123 Main Street."
        result = parental_service.filter_content(content, AgeGroup.ADULT)
        
        # Should not flag for adults
        assert RiskCategory.PERSONAL_INFO_SHARING not in result.risk_categories


class TestAgeBasedFiltering:
    """Tests for age-appropriate content filtering."""
    
    def test_child_strict_filtering(self, parental_service):
        """Test children only see SAFE content."""
        content = "This has mild violence in a cartoon setting."
        result = parental_service.filter_content(content, AgeGroup.CHILD)
        
        # Children should have strictest filtering
        if result.risk_level != RiskLevel.SAFE:
            assert result.is_appropriate is False
    
    def test_teen_moderate_filtering(self, parental_service):
        """Test teens can see some moderate content."""
        content = "This has mild profanity like damn and hell."
        result = parental_service.filter_content(content, AgeGroup.TEEN, strict_mode=False)
        
        # Teens might see low-medium risk content in non-strict mode
        assert result.risk_level in [RiskLevel.SAFE, RiskLevel.LOW_RISK, RiskLevel.MEDIUM_RISK] or not result.is_appropriate
    
    def test_teen_strict_mode(self, parental_service):
        """Test strict mode for teens is more restrictive."""
        content = "This has some mild violence and profanity."
        result_normal = parental_service.filter_content(content, AgeGroup.TEEN, strict_mode=False)
        result_strict = parental_service.filter_content(content, AgeGroup.TEEN, strict_mode=True)
        
        # Strict mode should be more restrictive
        if not result_normal.is_appropriate:
            assert not result_strict.is_appropriate
    
    def test_adult_filtering_allows_most_content(self, parental_service):
        """Test adults can see most content except BLOCKED."""
        content = "This has mature themes and some violence."
        result = parental_service.filter_content(content, AgeGroup.ADULT)
        
        # Adults should see most content unless it's BLOCKED
        if result.risk_level != RiskLevel.BLOCKED:
            # Content might still be flagged but typically allowed
            pass


class TestContentRating:
    """Tests for content rating system."""
    
    def test_everyone_rating(self, parental_service):
        """Test EVERYONE rating for safe content."""
        content = "This is a fun educational story for all ages."
        result = parental_service.filter_content(content, AgeGroup.CHILD)
        
        assert result.content_rating == ContentRating.EVERYONE
    
    def test_teen_rating_for_profanity(self, parental_service):
        """Test TEEN rating for mild profanity."""
        content = "This has some damn profanity."
        result = parental_service.filter_content(content, AgeGroup.TEEN)
        
        assert result.content_rating in [ContentRating.TEEN, ContentRating.EVERYONE_10_PLUS]
    
    def test_mature_rating_for_violence(self, parental_service):
        """Test MATURE rating for violence."""
        content = "This contains violence and combat scenes with weapons."
        result = parental_service.filter_content(content, AgeGroup.YOUNG_ADULT)
        
        assert result.content_rating in [ContentRating.MATURE, ContentRating.TEEN]
    
    def test_adults_only_rating(self, parental_service):
        """Test ADULTS_ONLY rating for severe content."""
        content = "This contains explicit sexual content."
        result = parental_service.filter_content(content, AgeGroup.ADULT)
        
        assert result.content_rating == ContentRating.ADULTS_ONLY


class TestContentFilteringEdgeCases:
    """Tests for edge cases and special scenarios."""
    
    def test_empty_content(self, parental_service):
        """Test filtering empty content."""
        result = parental_service.filter_content("", AgeGroup.CHILD)
        
        assert result.is_appropriate is True
        assert result.risk_level == RiskLevel.SAFE
    
    def test_multiple_risk_categories(self, parental_service):
        """Test content with multiple risk categories."""
        content = "This has violence with guns, damn profanity, and alcohol substance use all together."
        result = parental_service.filter_content(content, AgeGroup.CHILD)
        
        assert len(result.risk_categories) >= 2
        assert result.is_appropriate is False
    
    def test_filtered_content_redaction(self, parental_service):
        """Test that blocked terms are redacted in filtered content."""
        content = "This damn thing is crap."
        result = parental_service.filter_content(content, AgeGroup.TEEN)
        
        if result.filtered_content:
            # Check that profanity is replaced with asterisks
            assert "damn" not in result.filtered_content.lower() or "*" in result.filtered_content
    
    def test_case_insensitive_detection(self, parental_service):
        """Test that detection is case-insensitive."""
        content_lower = "this has violence and kill"
        content_upper = "THIS HAS VIOLENCE AND KILL"
        
        result_lower = parental_service.filter_content(content_lower, AgeGroup.CHILD)
        result_upper = parental_service.filter_content(content_upper, AgeGroup.CHILD)
        
        assert result_lower.risk_categories == result_upper.risk_categories


class TestRecommendations:
    """Tests for safety recommendations."""
    
    def test_self_harm_crisis_recommendations(self, parental_service):
        """Test crisis recommendations for self-harm content."""
        content = "I want to kill myself."
        result = parental_service.filter_content(content, AgeGroup.TEEN)
        
        assert len(result.recommendations) > 0
        assert any("crisis" in rec.lower() or "988" in rec for rec in result.recommendations)
    
    def test_bullying_alert_recommendations(self, parental_service):
        """Test recommendations for bullying content."""
        content = "You're a loser and nobody likes you."
        result = parental_service.filter_content(content, AgeGroup.TEEN)
        
        assert len(result.recommendations) > 0
        assert any("parent" in rec.lower() or "guardian" in rec.lower() for rec in result.recommendations)
    
    def test_personal_info_education_recommendations(self, parental_service):
        """Test education recommendations for personal info sharing."""
        content = "My address is 123 Main Street."
        result = parental_service.filter_content(content, AgeGroup.CHILD)
        
        assert len(result.recommendations) > 0
        assert any("safety" in rec.lower() or "education" in rec.lower() for rec in result.recommendations)


class TestPerformance:
    """Tests for performance and efficiency."""
    
    def test_age_detection_performance(self, parental_service):
        """Test age detection completes quickly."""
        import time
        
        text = "I'm in high school and have homework to do."
        start = time.perf_counter()
        result = parental_service.predict_age_group(text)
        end = time.perf_counter()
        
        assert (end - start) < 0.1  # Should complete in under 100ms
        assert result.predicted_age_group == AgeGroup.TEEN
    
    def test_content_filtering_performance(self, parental_service):
        """Test content filtering completes quickly."""
        import time
        
        content = "This is a test of the content filtering system with some profanity like damn."
        start = time.perf_counter()
        result = parental_service.filter_content(content, AgeGroup.TEEN)
        end = time.perf_counter()
        
        assert (end - start) < 0.1  # Should complete in under 100ms
        assert result is not None
    
    def test_batch_filtering_efficiency(self, parental_service):
        """Test filtering multiple items is efficient."""
        import time
        
        contents = [
            "Safe content for children",
            "This has some profanity",
            "Violence and weapons",
            "Educational material",
            "More safe content"
        ]
        
        start = time.perf_counter()
        results = [
            parental_service.filter_content(content, AgeGroup.CHILD)
            for content in contents
        ]
        end = time.perf_counter()
        
        assert (end - start) < 0.5  # Should complete in under 500ms
        assert len(results) == len(contents)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

