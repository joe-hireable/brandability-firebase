import sys
import os

# Add the functions directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from case_prediction.gs_similarity import assess_gs_similarity
from models import GsSimilarityRequest, GoodService

def test_similarity():
    """
    Tests the G&S similarity between 'software' and 'computer programs'.
    """
    request = GsSimilarityRequest(
        applicant_term=GoodService(term="croissants", class_num=30),
        opponent_term=GoodService(term="doughnuts", class_num=30),
    )

    # NOTE: This test requires authentication with Google Cloud5 and Vertex AI,
    # and the necessary environment variables (VECTOR_SEARCH_ENDPOINT_NAME,
    # DEPLOYED_INDEX_ID) must be set.
    try:
        result, rag_examples, prompt = assess_gs_similarity(request)

        print("\n--- RAG EXAMPLES ---")
        print(rag_examples)
        print("\n--- GEMINI PROMPT ---")
        print(prompt)
        print("\n--- SIMILARITY RESULT ---")
        print(f"Testing G&S similarity:")
        print(f"  Applicant Term: '{request.applicant_term.term}' (Class {request.applicant_term.class_num})")
        print(f"  Opponent Term:  '{request.opponent_term.term}' (Class {request.opponent_term.class_num})")
        print(f"  -------------------------------------------")
        print(f"  Similarity Score: {result.similarity_score:.2f}")
        print(f"  Similarity Degree: {result.similarity}")
        print(f"  Reasoning: {result.reasoning}")

    except RuntimeError as e:
        print(f"Error running test: {e}")
        print("Please ensure you have authenticated and set the required environment variables.")


if __name__ == "__main__":
    test_similarity()