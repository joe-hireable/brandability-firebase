"""
Similarity assessment module for trademark prediction system.

This module provides the core functions for assessing trademark similarity and
predicting case outcomes. It serves as the public API for the case_prediction
package, exporting the main orchestrator functions.
"""

from .mark_similarity import assess_mark_similarity
from .gs_similarity import assess_gs_similarity
from .case_prediction import predict_case_outcome

__all__ = [
    "assess_mark_similarity",
    "assess_gs_similarity",
    "predict_case_outcome",
]