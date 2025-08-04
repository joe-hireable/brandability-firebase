"""
Single source of truth (SSoT) for all data models in the LegalTech Predictor system.

This module defines the core Pydantic models used for structured data extraction
from case PDFs via Gemini, as well as the input/output schemas for the API layer.
These models are the canonical schema definitions for the application.
"""
from __future__ import annotations
from typing import Literal, Dict, Optional
from pydantic import BaseModel, Field, conlist

# --- ENUMS ---

Jurisdiction = Literal["UKIPO", "EUIPO"]
MarkType = Literal["WORD", "FIGURATIVE", "WORD_AND_DEVICE", "THREE_DIMENSIONAL"]
ProofOfUseOutcome = Literal["use_proven", "use_not_proven", "not_applicable"]
SimilarityDegree = Literal["identical", "high_degree", "medium_degree", "low_degree", "dissimilar"]
ConceptualSimilarityDegree = Literal["identical", "high_degree", "medium_degree", "low_degree", "dissimilar", "neutral"]
DistinctiveCharacter = Literal["very_high_degree", "high_degree", "medium_degree", "low_degree"]
AverageConsumerAttention = Literal["high", "medium", "low"]
ConfusionType = Literal["direct", "indirect", "both"]
OppositionOutcome = Literal["successful", "partially_successful", "unsuccessful"]
OtherGroundsEnum = Literal["5(3)", "5(4)(a)"]


# --- DATABASE & GEMINI EXTRACTION MODELS ---
# These models define the structured data extracted from case PDFs.

class GoodsServices(BaseModel):
    """Represents the goods and services for a specific class."""
    class_num: int = Field(..., alias="class", ge=1, le=45, description="The Nice Classification class number (1-45)")
    terms: list[str] = Field(..., description="The list of good or service terms")

class ApplicantMark(BaseModel):
    """A mark the applicant is trying to register."""
    mark: str = Field(..., description="The literal text or description of the mark")
    mark_type: MarkType = Field(..., description="The type of the mark")
    goods_services: list[GoodsServices] = Field(..., description="List of goods and services for the applicant's mark")

class OpponentMark(BaseModel):
    """An earlier mark the opponent is relying on."""
    mark: str = Field(..., description="The literal text or description of the mark")
    mark_type: Optional[MarkType] = Field(..., description="The type of the mark")
    registration_number: Optional[str] = Field(..., description="The registration number of the opponent's mark")
    filing_date: Optional[str] = Field(..., description="The filing date of the opponent's mark in DD/MM/YYYY format")
    registration_date: Optional[str] = Field(..., description="The registration date of the opponent's mark in DD/MM/YYYY format")
    priority_date: Optional[str] = Field(..., description="The priority date of the opponent's mark in DD/MM/YYYY format")
    goods_services: Optional[list[GoodsServices]] = Field(..., description="List of goods and services for the opponent's mark")

class GoodsServicesComparison(BaseModel):
    """Comparison between a specific applicant and opponent G&S term."""
    applicant_term: str = Field(..., description="The applicant's good or service term being compared")
    opponent_term: str = Field(..., description="The opponent's good or service term being compared")
    similarity: SimilarityDegree = Field(..., description="The assessed degree of similarity")

class MarkComparison(BaseModel):
    """Comparison of the marks on visual, aural, and conceptual levels."""
    visual_similarity: SimilarityDegree = Field(..., description="Degree of visual similarity")
    aural_similarity: SimilarityDegree = Field(..., description="Degree of aural similarity")
    conceptual_similarity: ConceptualSimilarityDegree = Field(..., description="Degree of conceptual similarity")
    dominant_component: str | None = Field(None, description="The component of the mark identified as being dominant in the legal analysis.")

class Precedent(BaseModel):
    """A precedent case cited in the decision."""
    case_name: str = Field(..., description="The name of the cited case")
    case_reference: str = Field(..., description="The reference number of the cited case")
    summary: str | None = Field(None, description="A brief summary of the precedent's relevance")
    relevance_score: float | None = Field(None, ge=0.0, le=1.0, description="Relevance score (0.0 to 1.0) for this precedent")

class DecisionRationale(BaseModel):
    """Rationale behind the decision, including key factors and cited precedents."""
    key_factors: list[str] = Field(..., description="Key factors that influenced the decision")
    precedents_cited: Optional[list[Precedent]] = Field(None, description="A list of precedent cases cited in the decision")

class Case(BaseModel):
    """A structured representation of a trademark opposition case decision."""
    case_reference: Optional[str] = Field(..., description="The unique identifier for the case, e.g., 'O/0959/23'")
    decision_date: Optional[str] = Field(..., description="The date the decision was issued in DD/MM/YYYY format")
    decision_maker: Optional[str] = Field(..., description="The name of the Hearing Officer or Judge")
    jurisdiction: Optional[Jurisdiction] = Field(None, description="The legal jurisdiction of the decision")
    application_number: str = Field(..., description="The application number of the contested trademark")
    applicant_name: str = Field(..., description="The name of the party applying for the trademark")
    opponent_name: str = Field(..., description="The name of the party opposing the trademark application")
    applicant_marks: list[ApplicantMark] = Field(..., description="An array of marks the applicant is trying to register")
    opponent_marks: list[OpponentMark] = Field(..., description="An array of earlier marks the opponent is relying on")
    grounds_for_opposition: list[str] = Field(..., description="The legal grounds for the opposition")
    proof_of_use_requested: bool = Field(..., description="Whether proof of use was requested")
    proof_of_use_outcome: Optional[ProofOfUseOutcome] = Field(None, description="The outcome of the proof of use assessment")
    goods_services_comparison: list[GoodsServicesComparison] = Field(..., description="An array of G&S comparisons")
    mark_comparison: MarkComparison = Field(..., description="The detailed comparison of the marks")
    distinctive_character: DistinctiveCharacter = Field(..., description="The assessed distinctive character of the earlier mark")
    average_consumer_attention: AverageConsumerAttention = Field(..., description="The assessed level of attention of the average consumer")
    likelihood_of_confusion: bool = Field(..., description="The final assessment on the likelihood of confusion")
    confusion_type: ConfusionType = Field(None, description="The type of confusion found, if any")
    opposition_outcome: Optional[OppositionOutcome] = Field(None, description="The final outcome of the opposition")
    other_grounds: Optional[list[OtherGroundsEnum]] = Field(None, description="Other legal grounds for opposition, if any")
    decision_rationale: Optional[DecisionRationale] = Field(None, description="The rationale for the decision")
    global_assessment_notes: Optional[str] = Field(None, description="A summary of the hearing officer's final global assessment and reasoning.")


# --- API MODELS ---
# These models define the request and response schemas for the API endpoints.

class MarkSimilarityRequest(BaseModel):
    """Input for the /mark_similarity endpoint."""
    applicant_mark: str = Field(..., description="The applicant's wordmark")
    opponent_mark: str = Field(..., description="The opponent's wordmark")
    mark_image_url: str | None = Field(None, description="URL to the figurative mark image, if applicable")

class MarkSimilarityOutput(BaseModel):
    """Output from the /mark_similarity endpoint."""
    visual: SimilarityDegree = Field(..., description="Visual similarity category")
    aural: SimilarityDegree = Field(..., description="Aural similarity category")
    conceptual: ConceptualSimilarityDegree = Field(..., description="Conceptual similarity category")
    overall_similarity: SimilarityDegree = Field(..., description="Overall similarity category considering all dimensions")
    visual_score: float = Field(..., ge=0.0, le=1.0, description="Visual similarity score (0.0 to 1.0)")
    aural_score: float = Field(..., ge=0.0, le=1.0, description="Aural similarity score (0.0 to 1.0)")
    conceptual_score: float = Field(..., ge=0.0, le=1.0, description="Conceptual similarity score (0.0 to 1.0)")
    overall_similarity_score: float = Field(..., ge=0.0, le=1.0, description="Overall similarity score (0.0 to 1.0)")
    reasoning: str = Field(..., description="Reasoning for the overall assessment")

class GsSimilarityRequest(BaseModel):
    """Input for the /gs_similarity endpoint."""
    applicant_term: str = Field(..., description="The applicant's good/service term")
    opponent_term: str = Field(..., description="The opponent's good/service term")
    mark_similarity: MarkSimilarityOutput = Field(..., description="The context of mark similarity from the /mark_similarity endpoint")

class GsSimilarityOutput(BaseModel):
    """Output from the /gs_similarity endpoint."""
    similarity: SimilarityDegree = Field(..., description="The degree of similarity between the goods/services")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score (0.0 to 1.0)")
    is_competitive: bool = Field(..., description="Whether the goods/services compete in the marketplace")
    is_complementary: bool = Field(..., description="Whether the goods/services are complementary or used together")
    likelihood_of_confusion: bool = Field(..., description="Whether there is a likelihood of confusion for this G/S pair")
    confusion_type: ConfusionType | None = Field(None, description="Type of confusion (null if no likelihood)")
    reasoning: str = Field(..., description="Reasoning for the assessment")

class CasePredictionRequest(BaseModel):
    """Input for the /case_prediction endpoint."""
    applicant_marks: list[ApplicantMark] = Field(..., description="The applicant's full mark details")
    opponent_marks: list[OpponentMark] = Field(..., description="The opponent's full mark details")

class CasePredictionOutput(BaseModel):
    """Output from the /case_prediction endpoint."""
    predicted_outcome: OppositionOutcome = Field(..., description="The predicted outcome category")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0 to 1.0) for the prediction")
    detailed_reasoning: str = Field(..., description="Detailed reasoning supporting the predicted outcome and confidence")
    mark_similarity_assessment: MarkSimilarityOutput = Field(..., description="The detailed mark similarity assessment")
    goods_services_assessments: list[GsSimilarityOutput] = Field(..., description="A list of the individual goods and services similarity assessments")