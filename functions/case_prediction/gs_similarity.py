"""
Assesses the similarity between goods and services (G&S) using a
Retrieval-Augmented Generation (RAG) approach with Vertex AI Vector Search.

This module uses a multi-step process:
1.  Generates an embedding for the input G&S terms.
2.  Queries a pre-populated Vector Search index to find the most similar
    real-world examples from a dataset of 21,000+ EUIPO cases.
3.  Constructs a detailed "few-shot" prompt, augmenting the original request
    with the retrieved examples.
4.  Calls the Gemini API with this augmented prompt to get a final,
    context-aware similarity assessment.
"""
import os
import json
import logging
from typing import List, Dict, Any

from google.cloud import aiplatform

from models import GsSimilarityRequest, GsSimilarityOutput
from utils.clients import get_gemini_client
from google.genai import types

# --- Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

gemini_client = get_gemini_client()

# --- Environment Variables ---
# These are the resource names from the `setup_vector_search.py` script output
try:
    VECTOR_SEARCH_ENDPOINT_NAME = os.environ["VECTOR_SEARCH_ENDPOINT_NAME"]
    DEPLOYED_INDEX_ID = os.environ["DEPLOYED_INDEX_ID"]
except KeyError:
    raise RuntimeError(
        "Required environment variables VECTOR_SEARCH_ENDPOINT_NAME or "
        "DEPLOYED_INDEX_ID are not set."
    )

# --- Constants ---
EMBEDDING_MODEL_NAME = "embedding-001"
NUM_NEIGHBORS = 5  # Number of similar examples to retrieve


# --- AI and Vector Search Functions ---

def get_embedding(text: str) -> List[float]:
    """Generates an embedding for a given text using the Gemini API."""
    response = gemini_client.models.embed_content(
        model=EMBEDDING_MODEL_NAME,
        contents=text
    )
    return response.embeddings[0].values

def find_similar_examples(
    applicant_term: str, opponent_term: str
) -> str:
    """
    Finds similar G&S pairs from the dataset using Vector Search.
    """
    logger.info(f"Finding similar examples for: '{applicant_term}' vs '{opponent_term}'")
    
    # Initialize the Vector Search endpoint
    endpoint = aiplatform.MatchingEngineIndexEndpoint(
        index_endpoint_name=VECTOR_SEARCH_ENDPOINT_NAME
    )

    # Generate embeddings for both terms
    applicant_embedding = get_embedding(applicant_term)
    opponent_embedding = get_embedding(opponent_term)

    # Query for neighbors for both terms
    response = endpoint.find_neighbors(
        queries=[applicant_embedding, opponent_embedding],
        deployed_index_id=DEPLOYED_INDEX_ID,
        num_neighbors=NUM_NEIGHBORS,
    )

    # Collect unique examples from the neighbors
    seen_examples = set()
    few_shot_examples = []
    for neighbor_list in response:
        for neighbor in neighbor_list:
            neighbor_term = neighbor.id
            # Since we're using Vertex AI Vector Search, we can directly use the neighbor information
            # In a more complete implementation, you might want to fetch additional details about the examples
            # from a database or another source, but for now we'll just use the neighbor term
            if neighbor_term not in seen_examples:
                few_shot_examples.append(
                    f"- Similar term from database: '{neighbor_term}' (Distance: {neighbor.distance:.4f})"
                )
                seen_examples.add(neighbor_term)
    
    if not few_shot_examples:
        logger.warning("No relevant examples found in the database.")
        return "No relevant examples found in the database."

    logger.info(f"Retrieved {len(few_shot_examples)} RAG examples:\n" + "\n".join(few_shot_examples))
    return "\n".join(few_shot_examples)


def assess_gs_similarity(request: GsSimilarityRequest) -> tuple[GsSimilarityOutput, str, str]:
    """
    Assesses the similarity between two goods/services terms using a RAG approach.

    Returns:
        A tuple containing:
        - GsSimilarityOutput: The similarity assessment result.
        - str: The few-shot examples retrieved from Vector Search.
        - str: The full prompt sent to the Gemini model.
    """
    # 1. Retrieval: Find similar examples from our dataset
    similar_examples = find_similar_examples(
        request.applicant_term.term, request.opponent_term.term
    )

    # 2. Augmentation: Construct the prompt with the retrieved examples
    prompt = f"""
    You are an expert in trademark law, specializing in assessing the similarity
    between goods and services (G&S). Your task is to analyze a new G&S pair
    based on real-world examples from past cases.

    Here are some relevant examples of real goods/services comparisons from our database:
    {similar_examples}

    Now, analyze the following new case with the above examples as context:

    - Applicant's Term: "{request.applicant_term.term}" (Class {request.applicant_term.class_num})
    - Opponent's Term: "{request.opponent_term.term}" (Class {request.opponent_term.class_num})

    Based on all of this information, provide a detailed assessment.
    """

    # 3. Generation: Call the Gemini API with the augmented prompt
    logger.info(f"Constructed Gemini Prompt:\n---\n{prompt}\n---")
    response = gemini_client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GsSimilarityOutput,
        ),
    )

    result = GsSimilarityOutput.model_validate_json(response.text)
    return result, similar_examples, prompt