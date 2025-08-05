"""
Orchestrates the entire case outcome prediction process.

This module integrates the outputs from the mark and goods/services (G&S)
similarity modules to generate a final, holistic prediction of a trademark
opposition case outcome. It uses the Gemini API to synthesize the various
data points into a reasoned prediction.
"""
from itertools import product
from concurrent.futures import ThreadPoolExecutor

from functions.models import (
    CasePredictionRequest,
    CasePredictionOutput,
    MarkSimilarityRequest,
    GsSimilarityRequest,
    GsSimilarityOutput,
)
from functions.case_prediction.mark_similarity import assess_mark_similarity
from functions.case_prediction.gs_similarity import assess_gs_similarity
from functions.utils.clients import get_gemini_client

gemini_client = get_gemini_client()
from google.genai import types


def predict_case_outcome(request: CasePredictionRequest) -> CasePredictionOutput:
    """
    Predicts the outcome of a trademark opposition case.

    Args:
        request: A CasePredictionRequest object containing the full details
                 of the applicant and opponent marks.

    Returns:
        A CasePredictionOutput object with the predicted outcome and reasoning.
    """
    # For simplicity, we'll compare the first applicant and opponent mark.
    # A more robust implementation could handle multiple marks.
    applicant_mark = request.applicant_marks[0]
    opponent_mark = request.opponent_marks[0]

    # 1. Assess Mark Similarity
    mark_sim_request = MarkSimilarityRequest(
        applicant_mark=applicant_mark.mark,
        opponent_mark=opponent_mark.mark,
    )
    mark_similarity_assessment = assess_mark_similarity(mark_sim_request)

    # 2. Assess Goods/Services Similarity for all pairs
    gs_assessments: list[GsSimilarityOutput] = []
    applicant_gs_terms = [term for gs in applicant_mark.goods_services for term in gs.terms]
    opponent_gs_terms = [term for gs in opponent_mark.goods_services for term in gs.terms]

    with ThreadPoolExecutor() as executor:
        gs_futures = {
            executor.submit(
                assess_gs_similarity,
                GsSimilarityRequest(
                    applicant_term=app_term,
                    opponent_term=opp_term,
                    mark_similarity=mark_similarity_assessment,
                ),
            ): (app_term, opp_term)
            for app_term, opp_term in product(applicant_gs_terms, opponent_gs_terms)
        }
        for future in gs_futures:
            gs_assessments.append(future.result())

    # 3. Generate Final Prediction with Gemini
    synthesis_prompt = f"""
    You are a trademark law expert. Based on the following detailed analysis,
    predict the final outcome of this opposition case.

    **Mark Similarity Assessment:**
    - Overall: {mark_similarity_assessment.overall_similarity} (Score: {mark_similarity_assessment.overall_similarity_score:.2f})
    - Reasoning: {mark_similarity_assessment.reasoning}

    **Goods & Services Similarity Assessments:**
    {"".join([f'- G/S Pair: "{gs.applicant_term}" vs "{gs.opponent_term}" -> Similarity: {gs.similarity} (Score: {gs.similarity_score:.2f}), Likelihood of Confusion: {gs.likelihood_of_confusion}, Reasoning: {gs.reasoning}\\n' for gs in gs_assessments])}

    Synthesize all this information to provide a final prediction.
    """

    response = gemini_client.models.generate_content(
        model="gemini-2.5-pro",
        contents=synthesis_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CasePredictionOutput,
        ),
    )

    # Inject the detailed assessments into the final output
    final_prediction = CasePredictionOutput.parse_raw(response.text)
    final_prediction.mark_similarity_assessment = mark_similarity_assessment
    final_prediction.goods_services_assessments = gs_assessments

    return final_prediction