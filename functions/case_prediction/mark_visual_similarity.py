"""
Calculates the visual similarity between two trademarks using the Levenshtein distance.

This module provides a function to assess how visually similar two wordmarks are,
which is a key factor in trademark confusion analysis. It uses the `rapidfuzz`
library for an efficient implementation of the Levenshtein algorithm.
"""
from rapidfuzz.fuzz import ratio

from models import SimilarityDegree


def _map_score_to_degree(score: float) -> SimilarityDegree:
    """Maps a similarity score (0-100) to a qualitative degree."""
    if score >= 95:
        return "identical"
    if score >= 80:
        return "high_degree"
    if score >= 65:
        return "medium_degree"
    if score >= 50:
        return "low_degree"
    return "dissimilar"


def calculate_visual_similarity(applicant_mark: str, opponent_mark: str) -> tuple[float, SimilarityDegree]:
    """
    Calculates the visual similarity score and degree between two marks.

    Args:
        applicant_mark: The applicant's wordmark.
        opponent_mark: The opponent's wordmark.

    Returns:
        A tuple containing the visual similarity score (0.0 to 1.0)
        and the corresponding similarity degree.
    """
    # Calculate similarity ratio (0-100 scale)
    similarity_score_100 = ratio(applicant_mark.lower(), opponent_mark.lower())

    # Normalize score to 0.0-1.0
    normalized_score = similarity_score_100 / 100.0

    # Map score to degree
    degree = _map_score_to_degree(similarity_score_100)

    return normalized_score, degree