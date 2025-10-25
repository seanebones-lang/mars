"""
Parental Controls API Router
REST API endpoints for family-friendly content filtering and age prediction.

Author: AgentGuard Engineering Team
Date: October 2025
Version: 1.0.0
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..services.parental_controls import (
    ParentalControlService,
    AgeGroup,
    ContentRating,
    RiskLevel,
    RiskCategory,
    AgeDetectionResult,
    ContentFilterResult
)

router = APIRouter(
    prefix="/parental-controls",
    tags=["parental_controls"],
    responses={404: {"description": "Not found"}}
)

# Initialize service
parental_service = ParentalControlService()


# Request/Response Models
class AgeDetectionRequest(BaseModel):
    text: str = Field(..., description="Current text to analyze for age prediction")
    interaction_history: Optional[List[str]] = Field(
        None,
        description="Optional list of previous user interactions for better prediction"
    )


class AgeDetectionResponse(BaseModel):
    predicted_age_group: str
    confidence: float
    indicators: List[str]
    explanation: str
    recommended_content_rating: str

    @classmethod
    def from_result(cls, result: AgeDetectionResult):
        return cls(
            predicted_age_group=result.predicted_age_group.value,
            confidence=result.confidence,
            indicators=result.indicators,
            explanation=result.explanation,
            recommended_content_rating=result.recommended_content_rating.value
        )


class ContentFilterRequest(BaseModel):
    content: str = Field(..., description="Content to filter for age appropriateness")
    age_group: str = Field(
        ...,
        description="Target age group (child, teen, young_adult, adult, unknown)"
    )
    strict_mode: bool = Field(
        False,
        description="If True, apply stricter filtering rules"
    )


class ContentFilterResponse(BaseModel):
    is_appropriate: bool
    risk_level: str
    risk_categories: List[str]
    blocked_content: List[str]
    filtered_content: Optional[str]
    explanation: str
    recommendations: List[str]
    age_group: str
    content_rating: str

    @classmethod
    def from_result(cls, result: ContentFilterResult):
        return cls(
            is_appropriate=result.is_appropriate,
            risk_level=result.risk_level.value,
            risk_categories=[cat.value for cat in result.risk_categories],
            blocked_content=result.blocked_content,
            filtered_content=result.filtered_content,
            explanation=result.explanation,
            recommendations=result.recommendations,
            age_group=result.age_group.value,
            content_rating=result.content_rating.value
        )


class BatchContentFilterRequest(BaseModel):
    contents: List[str] = Field(..., description="List of content items to filter")
    age_group: str = Field(..., description="Target age group for all items")
    strict_mode: bool = Field(False, description="Apply strict filtering")


class BatchContentFilterResponse(BaseModel):
    results: List[ContentFilterResponse]
    summary: dict


# API Endpoints
@router.post(
    "/predict-age",
    response_model=AgeDetectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict User Age Group",
    description="Predict user's age group from interaction patterns for content personalization"
)
async def predict_age_group(request: AgeDetectionRequest):
    """
    Predict user's age group from text and interaction history.
    
    Uses pattern matching and linguistic analysis to estimate age group:
    - child (0-12 years)
    - teen (13-17 years)
    - young_adult (18-25 years)
    - adult (26+ years)
    - unknown (insufficient data)
    
    Returns confidence score and indicators used for prediction.
    """
    try:
        result = parental_service.predict_age_group(
            text=request.text,
            interaction_history=request.interaction_history
        )
        return AgeDetectionResponse.from_result(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Age prediction failed: {str(e)}"
        )


@router.post(
    "/filter-content",
    response_model=ContentFilterResponse,
    status_code=status.HTTP_200_OK,
    summary="Filter Content for Age Appropriateness",
    description="Filter content based on age group and detect risky behaviors"
)
async def filter_content(request: ContentFilterRequest):
    """
    Filter content for age appropriateness and safety.
    
    Checks for:
    - Profanity and inappropriate language
    - Violence and graphic content
    - Sexual content
    - Substance use references
    - Hate speech and discrimination
    - Bullying and harassment
    - Self-harm indicators (CRITICAL)
    - Personal information sharing (for children/teens)
    
    Returns filtered content with risk assessment and recommendations.
    """
    try:
        # Validate age group
        try:
            age_group = AgeGroup(request.age_group.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid age_group. Must be one of: {[e.value for e in AgeGroup]}"
            )
        
        result = parental_service.filter_content(
            content=request.content,
            age_group=age_group,
            strict_mode=request.strict_mode
        )
        return ContentFilterResponse.from_result(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content filtering failed: {str(e)}"
        )


@router.post(
    "/filter-batch",
    response_model=BatchContentFilterResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch Filter Multiple Content Items",
    description="Filter multiple content items in a single request for efficiency"
)
async def filter_content_batch(request: BatchContentFilterRequest):
    """
    Filter multiple content items in batch for efficiency.
    
    Useful for:
    - Filtering conversation history
    - Bulk content moderation
    - Real-time chat filtering
    - Educational content review
    
    Returns individual results plus summary statistics.
    """
    try:
        # Validate age group
        try:
            age_group = AgeGroup(request.age_group.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid age_group. Must be one of: {[e.value for e in AgeGroup]}"
            )
        
        results = []
        blocked_count = 0
        high_risk_count = 0
        categories_found = set()
        
        for content in request.contents:
            result = parental_service.filter_content(
                content=content,
                age_group=age_group,
                strict_mode=request.strict_mode
            )
            results.append(ContentFilterResponse.from_result(result))
            
            if not result.is_appropriate:
                blocked_count += 1
            if result.risk_level in [RiskLevel.HIGH_RISK, RiskLevel.BLOCKED]:
                high_risk_count += 1
            categories_found.update(result.risk_categories)
        
        summary = {
            "total_items": len(request.contents),
            "blocked_items": blocked_count,
            "high_risk_items": high_risk_count,
            "appropriate_items": len(request.contents) - blocked_count,
            "risk_categories_found": [cat.value for cat in categories_found],
            "age_group": age_group.value,
            "strict_mode": request.strict_mode
        }
        
        return BatchContentFilterResponse(
            results=results,
            summary=summary
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch filtering failed: {str(e)}"
        )


@router.get(
    "/age-groups",
    response_model=List[dict],
    status_code=status.HTTP_200_OK,
    summary="Get Available Age Groups",
    description="List all available age groups and their descriptions"
)
async def get_age_groups():
    """Get list of available age groups with descriptions."""
    return [
        {
            "value": AgeGroup.CHILD.value,
            "label": "Child (0-12 years)",
            "description": "Elementary school age, requires maximum protection",
            "recommended_rating": ContentRating.EVERYONE.value
        },
        {
            "value": AgeGroup.TEEN.value,
            "label": "Teen (13-17 years)",
            "description": "Middle/high school age, moderate content allowed",
            "recommended_rating": ContentRating.TEEN.value
        },
        {
            "value": AgeGroup.YOUNG_ADULT.value,
            "label": "Young Adult (18-25 years)",
            "description": "College age, most content allowed",
            "recommended_rating": ContentRating.MATURE.value
        },
        {
            "value": AgeGroup.ADULT.value,
            "label": "Adult (26+ years)",
            "description": "Full adult, all appropriate content allowed",
            "recommended_rating": ContentRating.MATURE.value
        },
        {
            "value": AgeGroup.UNKNOWN.value,
            "label": "Unknown",
            "description": "Age cannot be determined, use conservative filtering",
            "recommended_rating": ContentRating.EVERYONE_10_PLUS.value
        }
    ]


@router.get(
    "/content-ratings",
    response_model=List[dict],
    status_code=status.HTTP_200_OK,
    summary="Get Content Rating System",
    description="List all content ratings and their meanings"
)
async def get_content_ratings():
    """Get content rating system information."""
    return [
        {
            "value": ContentRating.EVERYONE.value,
            "label": "Everyone (E)",
            "description": "Content suitable for all ages",
            "age_range": "All ages"
        },
        {
            "value": ContentRating.EVERYONE_10_PLUS.value,
            "label": "Everyone 10+ (E10+)",
            "description": "Content suitable for ages 10 and up, mild content",
            "age_range": "10+ years"
        },
        {
            "value": ContentRating.TEEN.value,
            "label": "Teen (T)",
            "description": "Content suitable for ages 13 and up",
            "age_range": "13+ years"
        },
        {
            "value": ContentRating.MATURE.value,
            "label": "Mature (M)",
            "description": "Content suitable for ages 17 and up",
            "age_range": "17+ years"
        },
        {
            "value": ContentRating.ADULTS_ONLY.value,
            "label": "Adults Only (AO)",
            "description": "Content suitable only for adults 18 and up",
            "age_range": "18+ years"
        },
        {
            "value": ContentRating.UNRATED.value,
            "label": "Unrated",
            "description": "Content has not been rated",
            "age_range": "Unknown"
        }
    ]


@router.get(
    "/risk-categories",
    response_model=List[dict],
    status_code=status.HTTP_200_OK,
    summary="Get Risk Categories",
    description="List all risk categories monitored by the system"
)
async def get_risk_categories():
    """Get list of risk categories monitored by parental controls."""
    return [
        {
            "value": RiskCategory.VIOLENCE.value,
            "label": "Violence",
            "description": "Violent content, weapons, gore",
            "severity": "medium-high"
        },
        {
            "value": RiskCategory.PROFANITY.value,
            "label": "Profanity",
            "description": "Inappropriate language, swearing",
            "severity": "low-medium"
        },
        {
            "value": RiskCategory.SEXUAL_CONTENT.value,
            "label": "Sexual Content",
            "description": "Sexual references, nudity, adult content",
            "severity": "high"
        },
        {
            "value": RiskCategory.SUBSTANCE_USE.value,
            "label": "Substance Use",
            "description": "Drug, alcohol, tobacco references",
            "severity": "medium"
        },
        {
            "value": RiskCategory.HATE_SPEECH.value,
            "label": "Hate Speech",
            "description": "Discriminatory, racist, or hateful content",
            "severity": "critical"
        },
        {
            "value": RiskCategory.BULLYING.value,
            "label": "Bullying",
            "description": "Harassment, intimidation, cyberbullying",
            "severity": "high"
        },
        {
            "value": RiskCategory.SELF_HARM.value,
            "label": "Self-Harm",
            "description": "Suicide, self-injury references (ALWAYS BLOCKED)",
            "severity": "critical"
        },
        {
            "value": RiskCategory.PERSONAL_INFO_SHARING.value,
            "label": "Personal Info Sharing",
            "description": "Sharing addresses, phone numbers, location",
            "severity": "high (for children/teens)"
        },
        {
            "value": RiskCategory.STRANGER_DANGER.value,
            "label": "Stranger Danger",
            "description": "Interactions with unknown individuals",
            "severity": "high (for children/teens)"
        },
        {
            "value": RiskCategory.INAPPROPRIATE_CONTACT.value,
            "label": "Inappropriate Contact",
            "description": "Grooming, predatory behavior",
            "severity": "critical"
        }
    ]


@router.get(
    "/health",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check parental control service health"
)
async def health_check():
    """Health check endpoint for parental control service."""
    return {
        "status": "healthy",
        "service": "parental_controls",
        "version": "1.0.0",
        "features": [
            "age_prediction",
            "content_filtering",
            "batch_filtering",
            "risk_detection",
            "crisis_intervention"
        ]
    }

