import sys
import os

# Add the functions directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from case_prediction import gs_similarity
from models import GsSimilarityRequest, GoodService

def test_gs_similarity():
    """
    Tests the goods and services similarity between 'coffee' and 'tea'.
    """
    request = GsSimilarityRequest(
        applicant_term=GoodService(term="coffee", class_num=30),
        opponent_term=GoodService(term="tea", class_num=30),
    )

    result, _, _ = gs_similarity.assess_gs_similarity(request)

    print(f"Testing G&S similarity:")
    print(f"  Applicant: '{request.applicant_term.term}' (Class {request.applicant_term.class_num})")
    print(f"  Opponent:  '{request.opponent_term.term}' (Class {request.opponent_term.class_num})")
    print(f"  -----------------------------")
    print(f"  Similarity Score: {result.similarity_score:.2f}")
    print(f"  Similarity Degree: {result.similarity}")
    print(f"  Reasoning: {result.reasoning}")

if __name__ == "__main__":
    test_gs_similarity()