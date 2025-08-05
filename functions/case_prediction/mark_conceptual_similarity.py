"""
Calculates the conceptual similarity between two trademarks using the Gemini API.

This module leverages a large language model to assess the semantic and
conceptual relationship between two wordmarks. This is crucial for identifying
trademarks that may be visually and aurally different but evoke similar ideas
or meanings, a key factor in likelihood of confusion analysis.
"""
from pydantic import BaseModel, Field

from google.genai import types

from functions.models import ConceptualSimilarityDegree
from functions.utils.clients import gemini_client


class ConceptualSimilarityResponse(BaseModel):
    """
    Pydantic model for the structured response from the Gemini API.
    """
    score: float = Field(..., ge=0.0, le=1.0, description="A score from 0.0 (completely dissimilar) to 1.0 (identical in concept).")
    degree: ConceptualSimilarityDegree = Field(..., description="The qualitative degree of conceptual similarity.")
    reasoning: str = Field(..., description="A brief explanation for the assessed similarity.")


def calculate_conceptual_similarity(applicant_mark: str, opponent_mark: str) -> tuple[float, ConceptualSimilarityDegree, str]:
    """
    Calculates the conceptual similarity score and degree between two marks using Gemini.

    Args:
        applicant_mark: The applicant's wordmark.
        opponent_mark: The opponent's wordmark.

    Returns:
        A tuple containing the conceptual similarity score (0.0 to 1.0),
        the corresponding similarity degree, and the reasoning.
    """
    prompt = f"""
    Analyze the conceptual similarity between the following two trademarks:
    1. "{applicant_mark}"
    2. "{opponent_mark}"

    Consider their meanings, connotations, and the overall ideas they evoke.
    Provide a similarity score, a qualitative degree, and a brief reasoning.
    """

    response = gemini_client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ConceptualSimilarityResponse,
        ),
    )

    parsed_response = ConceptualSimilarityResponse.parse_raw(response.text)

    return parsed_response.score, parsed_response.degree, parsed_response.reasoning