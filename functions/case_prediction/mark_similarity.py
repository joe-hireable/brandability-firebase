"""
Orchestrates the calculation of visual, aural, and conceptual similarity for trademarks.

This module combines the outputs of the individual similarity modules
(visual, aural, conceptual) into a single, comprehensive assessment.
It calculates a weighted overall similarity score and uses the Gemini API
to generate a final, reasoned analysis.
"""
from concurrent.futures import ThreadPoolExecutor

from models import MarkSimilarityRequest, MarkSimilarityOutput, SimilarityDegree
from .mark_visual_similarity import calculate_visual_similarity
from .mark_aural_similarity import calculate_aural_similarity
from .mark_conceptual_similarity import calculate_conceptual_similarity
from utils.clients import get_gemini_client

gemini_client = get_gemini_client()


def _map_score_to_degree(score: float) -> SimilarityDegree:
    """Maps a similarity score (0.0-1.0) to a qualitative degree."""
    if score >= 0.95:
        return "identical"
    if score >= 0.75:
        return "high_degree"
    if score >= 0.55:
        return "medium_degree"
    if score >= 0.40:
        return "low_degree"
    return "dissimilar"


def assess_mark_similarity(request: MarkSimilarityRequest) -> MarkSimilarityOutput:
    """
    Calculates the overall similarity between two marks across multiple dimensions.

    Args:
        request: A MarkSimilarityRequest object containing the applicant and opponent marks.

    Returns:
        A MarkSimilarityOutput object with a detailed similarity assessment.
    """
    applicant_mark = request.applicant_mark
    opponent_mark = request.opponent_mark

    # Run similarity calculations in parallel
    with ThreadPoolExecutor() as executor:
        future_visual = executor.submit(calculate_visual_similarity, applicant_mark, opponent_mark)
        future_aural = executor.submit(calculate_aural_similarity, applicant_mark, opponent_mark)
        future_conceptual = executor.submit(calculate_conceptual_similarity, applicant_mark, opponent_mark)

        visual_score, visual_degree = future_visual.result()
        aural_score, aural_degree = future_aural.result()
        conceptual_score, conceptual_degree, conceptual_reasoning = future_conceptual.result()

    # Define weights for each similarity dimension
    weights = {"visual": 0.4, "aural": 0.4, "conceptual": 0.2}

    # Calculate weighted overall score
    overall_score = (
        visual_score * weights["visual"] +
        aural_score * weights["aural"] +
        conceptual_score * weights["conceptual"]
    )

    overall_degree = _map_score_to_degree(overall_score)

    # Generate final reasoning with Gemini
    reasoning_prompt = f"""
    Based on the following analysis, provide a concise, final reasoning for the overall similarity assessment between "{applicant_mark}" and "{opponent_mark}":

    - Visual Similarity: {visual_degree} (Score: {visual_score:.2f})
    - Aural Similarity: {aural_degree} (Score: {aural_score:.2f})
    - Conceptual Similarity: {conceptual_degree} (Score: {conceptual_score:.2f})
      - Reasoning: {conceptual_reasoning}

    The weighted overall similarity score is {overall_score:.2f}, which is considered '{overall_degree}'.
    """

    response = gemini_client.models.generate_content(
        model="gemini-2.5-pro",
        contents=reasoning_prompt,
    )
    final_reasoning = response.text

    return MarkSimilarityOutput(
        visual=visual_degree,
        aural=aural_degree,
        conceptual=conceptual_degree,
        overall_similarity=overall_degree,
        visual_score=visual_score,
        aural_score=aural_score,
        conceptual_score=conceptual_score,
        overall_similarity_score=overall_score,
        reasoning=final_reasoning,
    )