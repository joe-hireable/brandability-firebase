"""
Cloud Functions for Firebase API.
"""
import logging

from firebase_functions import https_fn, options
from flask import jsonify

from case_prediction import (
    mark_aural_similarity,
    mark_conceptual_similarity,
    mark_visual_similarity,
    gs_similarity,
)
from models import GsSimilarityRequest

log = logging.getLogger(__name__)


@https_fn.on_request(cors=options.CorsOptions(cors_origins="*", cors_methods=["get", "post"]))
def calculate_visual_similarity(req: https_fn.Request) -> https_fn.Response:
    """
    HTTP function to calculate visual similarity between two marks.
    """
    applicant_mark = req.get_json().get("applicant_mark")
    opponent_mark = req.get_json().get("opponent_mark")

    if not applicant_mark or not opponent_mark:
        return https_fn.Response("Missing applicant_mark or opponent_mark", status=400)

    score, degree = mark_visual_similarity.calculate_visual_similarity(
        applicant_mark, opponent_mark
    )

    return jsonify({"score": score, "degree": degree})


@https_fn.on_request(cors=options.CorsOptions(cors_origins="*", cors_methods=["get", "post"]))
def calculate_aural_similarity(req: https_fn.Request) -> https_fn.Response:
    """
    HTTP function to calculate aural similarity between two marks.
    """
    applicant_mark = req.get_json().get("applicant_mark")
    opponent_mark = req.get_json().get("opponent_mark")

    if not applicant_mark or not opponent_mark:
        return https_fn.Response("Missing applicant_mark or opponent_mark", status=400)

    score, degree = mark_aural_similarity.calculate_aural_similarity(
        applicant_mark, opponent_mark
    )

    return jsonify({"score": score, "degree": degree})


@https_fn.on_request(cors=options.CorsOptions(cors_origins="*", cors_methods=["get", "post"]))
def calculate_conceptual_similarity(req: https_fn.Request) -> https_fn.Response:
    """
    HTTP function to calculate conceptual similarity between two marks.
    """
    applicant_mark = req.get_json().get("applicant_mark")
    opponent_mark = req.get_json().get("opponent_mark")

    if not applicant_mark or not opponent_mark:
        return https_fn.Response("Missing applicant_mark or opponent_mark", status=400)

    score, degree, reasoning = mark_conceptual_similarity.calculate_conceptual_similarity(
        applicant_mark, opponent_mark
    )

    return jsonify({"score": score, "degree": degree, "reasoning": reasoning})


@https_fn.on_request(cors=options.CorsOptions(cors_origins="*", cors_methods=["get", "post"]))
def calculate_gs_similarity(req: https_fn.Request) -> https_fn.Response:
    """
    HTTP function to assess goods and services similarity.
    """
    try:
        data = req.get_json()
        gs_request = GsSimilarityRequest(**data)
    except Exception as e:
        log.error(f"Error parsing request body: {e}", exc_info=True)
        return https_fn.Response(f"Invalid request body: {e}", status=400)

    try:
        result, _, _ = gs_similarity.assess_gs_similarity(gs_request)
        return jsonify(result.model_dump())
    except Exception as e:
        log.error(f"Error assessing G&S similarity: {e}", exc_info=True)
        return https_fn.Response("Internal server error", status=500)