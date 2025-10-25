"""
Tests for Bias and Fairness Auditor
Test suite for bias detection and fairness assessment.

Author: AgentGuard Engineering Team
Date: October 2025
Version: 1.0.0
"""

import pytest
from src.services.bias_fairness_auditor import (
    BiasAndFairnessAuditor,
    BiasType,
    BiasLevel,
    FairnessMetric
)


class TestBiasAuditor:
    """Test suite for BiasAndFairnessAuditor."""
    
    @pytest.fixture
    def auditor(self):
        """Create auditor instance for testing."""
        return BiasAndFairnessAuditor(
            enable_stereotype_detection=True,
            enable_representation_analysis=True,
            enable_language_inclusivity=True
        )
    
    @pytest.mark.asyncio
    async def test_neutral_text(self, auditor):
        """Test that neutral text passes audit."""
        result = await auditor.audit(
            "The software engineer completed the project on time."
        )
        assert result.has_bias is False
        assert result.overall_bias_level == BiasLevel.NONE
    
    @pytest.mark.asyncio
    async def test_gender_stereotype_detection(self, auditor):
        """Test detection of gender stereotypes."""
        result = await auditor.audit(
            "Women are naturally more emotional and nurturing than men."
        )
        assert result.has_bias is True
        assert BiasType.GENDER in result.detected_bias_types
        assert any(ind.severity in [BiasLevel.HIGH, BiasLevel.CRITICAL] for ind in result.bias_indicators)
    
    @pytest.mark.asyncio
    async def test_non_inclusive_language(self, auditor):
        """Test detection of non-inclusive language."""
        result = await auditor.audit(
            "The chairman called a meeting with the policeman and fireman."
        )
        assert result.has_bias is True
        assert BiasType.LANGUAGE in result.detected_bias_types or BiasType.GENDER in result.detected_bias_types
    
    @pytest.mark.asyncio
    async def test_ableist_language(self, auditor):
        """Test detection of ableist language."""
        result = await auditor.audit(
            "That idea is crazy and lame. Are you blind to the obvious issues?"
        )
        assert result.has_bias is True
        assert any(ind.bias_type == BiasType.DISABILITY for ind in result.bias_indicators)
    
    @pytest.mark.asyncio
    async def test_age_bias_detection(self, auditor):
        """Test detection of age-related bias."""
        result = await auditor.audit(
            "Elderly people are slow and confused with technology."
        )
        assert result.has_bias is True
        assert BiasType.AGE in result.detected_bias_types
    
    @pytest.mark.asyncio
    async def test_alternative_suggestions(self, auditor):
        """Test that alternatives are suggested."""
        result = await auditor.audit(
            "The chairman addressed all the guys on the team."
        )
        assert result.has_bias is True
        assert any(ind.suggested_alternative is not None for ind in result.bias_indicators)
    
    @pytest.mark.asyncio
    async def test_fairness_scoring(self, auditor):
        """Test fairness score calculation."""
        result = await auditor.audit(
            "He completed the task while she assisted."
        )
        assert 0.0 <= result.overall_fairness_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_recommendations_generation(self, auditor):
        """Test that recommendations are generated."""
        result = await auditor.audit(
            "Women are emotional and men are strong."
        )
        assert len(result.recommendations) > 0
        assert any("gender" in rec.lower() for rec in result.recommendations)
    
    @pytest.mark.asyncio
    async def test_compliance_checking(self, auditor):
        """Test regulatory compliance checking."""
        result = await auditor.audit(
            "The engineer completed the project.",
            check_compliance=True
        )
        assert "EU_AI_Act" in result.compliance_status
        assert "NIST_AI_RMF" in result.compliance_status
        assert "IEEE_7000" in result.compliance_status
    
    @pytest.mark.asyncio
    async def test_multiple_bias_types(self, auditor):
        """Test detection of multiple bias types."""
        result = await auditor.audit(
            "The elderly chairman told the guys that women are too emotional for leadership."
        )
        assert result.has_bias is True
        assert len(result.detected_bias_types) >= 2
    
    @pytest.mark.asyncio
    async def test_severity_levels(self, auditor):
        """Test that severity levels are assigned correctly."""
        result = await auditor.audit(
            "Women are naturally weak and submissive."
        )
        assert any(ind.severity in [BiasLevel.HIGH, BiasLevel.CRITICAL] for ind in result.bias_indicators)
    
    @pytest.mark.asyncio
    async def test_confidence_scores(self, auditor):
        """Test confidence scores are within range."""
        result = await auditor.audit(
            "The chairman led the meeting."
        )
        for indicator in result.bias_indicators:
            assert 0.0 <= indicator.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_processing_time(self, auditor):
        """Test that processing time is recorded."""
        result = await auditor.audit(
            "Test content for processing time."
        )
        assert result.processing_time_ms > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

