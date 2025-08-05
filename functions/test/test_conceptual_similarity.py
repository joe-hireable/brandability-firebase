import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from functions.case_prediction.mark_conceptual_similarity import calculate_conceptual_similarity

def test_similarity():
    """
    Tests the conceptual similarity between 'COOLBRAND' and 'Kool Brand'.
    """
    applicant_mark = "COOLBRAND"
    opponent_mark = "Kool Brand"

    score, degree, reasoning = calculate_conceptual_similarity(applicant_mark, opponent_mark)

    print(f"Testing conceptual similarity:")
    print(f"  Applicant Mark: '{applicant_mark}'")
    print(f"  Opponent Mark:  '{opponent_mark}'")
    print(f"  -----------------------------")
    print(f"  Similarity Score: {score:.2f}")
    print(f"  Similarity Degree: {degree}")
    print(f"  Reasoning: {reasoning}")

if __name__ == "__main__":
    test_similarity()