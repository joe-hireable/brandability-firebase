"""
Assesses the similarity between goods and services (G&S) using the Gemini API.

This module provides a function to compare two G&S terms in the context of
their associated trademarks. It leverages a large language model to analyze
not only the literal meaning but also the commercial relationship (e.g.,
competitive, complementary) between the goods or services.
"""
from functions.models import GsSimilarityRequest, GsSimilarityOutput
from functions.utils.clients import get_gemini_client
from google.genai import types

gemini_client = get_gemini_client()
from google.genai import types


def assess_gs_similarity(request: GsSimilarityRequest) -> GsSimilarityOutput:
    """
    Assesses the similarity between two goods/services terms using Gemini.

    Args:
        request: A GsSimilarityRequest object containing the applicant and
                 opponent G&S terms and the mark similarity context.

    Returns:
        A GsSimilarityOutput object with a detailed G&S similarity assessment.
    """
    prompt = f"""
    Analyze the similarity between the following two goods/services terms,
    considering the provided context of their respective trademarks' similarity.

    - Applicant's Term: "{request.applicant_term}"
    - Opponent's Term: "{request.opponent_term}"

    Context of Mark Similarity:
    - Overall Mark Similarity: {request.mark_similarity.overall_similarity}
      (Score: {request.mark_similarity.overall_similarity_score:.2f})
    - Reasoning: {request.mark_similarity.reasoning}

    Based on this, assess the following:
    1.  The degree of similarity between the goods/services.
    2.  Whether they are competitive or complementary in the marketplace.
    3.  The likelihood of consumer confusion for this specific G/S pair.
    """

    response = gemini_client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GsSimilarityOutput,
        ),
    )

    return GsSimilarityOutput.parse_raw(response.text)