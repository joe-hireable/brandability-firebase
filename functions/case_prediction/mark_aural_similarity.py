"""
Calculates the aural similarity between two trademarks using phonetic algorithms.

This module assesses how phonetically similar two wordmarks are, which is a
key factor in trademark confusion analysis. It uses the `jellyfish` library
to generate Double Metaphone codes and compares them using the Jaro-Winkler
distance to account for variations in pronunciation.
"""
import jellyfish

from functions.models import SimilarityDegree


def _map_score_to_degree(score: float) -> SimilarityDegree:
    """Maps a similarity score (0.0-1.0) to a qualitative degree."""
    if score >= 0.95:
        return "identical"
    if score >= 0.85:
        return "high_degree"
    if score >= 0.70:
        return "medium_degree"
    if score >= 0.55:
        return "low_degree"
    return "dissimilar"


def calculate_aural_similarity(applicant_mark: str, opponent_mark: str) -> tuple[float, SimilarityDegree]:
    """
    Calculates the aural similarity score and degree between two marks.

    Args:
        applicant_mark: The applicant's wordmark.
        opponent_mark: The opponent's wordmark.

    Returns:
        A tuple containing the aural similarity score (0.0 to 1.0)
        and the corresponding similarity degree.
    """
    # Generate Double Metaphone codes for each mark
    applicant_metaphone = jellyfish.metaphone(applicant_mark)
    opponent_metaphone = jellyfish.metaphone(opponent_mark)

    # If either metaphone is empty, fall back to a direct string comparison
    if not applicant_metaphone or not opponent_metaphone:
        similarity_score = jellyfish.jaro_winkler_similarity(applicant_mark, opponent_mark)
    else:
        # Calculate Jaro-Winkler similarity between the metaphone codes
        similarity_score = jellyfish.jaro_winkler_similarity(applicant_metaphone, opponent_metaphone)

    # Map score to degree
    degree = _map_score_to_degree(similarity_score)

    return similarity_score, degree