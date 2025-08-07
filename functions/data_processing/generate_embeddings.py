"""
Generates vector embeddings for all unique G&S terms in the processed data.

This script performs the following steps:
1.  Loads the processed data from the JSONL file.
2.  Identifies all unique goods and services terms.
3.  Uses the centralized Gemini client to generate embeddings for all terms
    in a single, efficient batch operation.
4.  Saves the generated embeddings to a new JSON file, mapping each term to its
    corresponding vector. This file is the direct input for creating the
    Vertex AI Vector Search index.
"""
import json
import pandas as pd
import sys
import os

# Add the parent 'functions' directory to the Python path
# to allow for relative imports of modules like 'utils'.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.clients import get_gemini_client

# Path to the processed data
PROCESSED_DATA_PATH = "data/processed_similarity_data.jsonl"
# Path to save the final embeddings file
EMBEDDINGS_FILE_PATH = "data/term_embeddings.json"

# Consistent model name as used elsewhere in the project
MODEL_NAME = "models/embedding-001"

def generate_embeddings():
    """
    Loads processed data, generates embeddings for unique terms, and saves them.
    """
    print("Starting embedding generation...")

    # 1. Load the processed data
    df = pd.read_json(PROCESSED_DATA_PATH, lines=True)

    # 2. Identify all unique terms
    unique_terms = pd.concat([df['term_1'], df['term_2']]).unique()
    print(f"Found {len(unique_terms)} unique terms to embed.")

    # 3. Initialize Gemini client
    gemini_client = get_gemini_client()
    
    # 4. Generate embeddings in batches to respect the API limit of 100 per call.
    print(f"Generating embeddings with {MODEL_NAME} in batches of 100...")
    
    all_embeddings = []
    term_list = unique_terms.tolist()
    batch_size = 100

    for i in range(0, len(term_list), batch_size):
        batch = term_list[i:i + batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(term_list) + batch_size - 1)//batch_size}...")
        result = gemini_client.models.embed_content(
            model=MODEL_NAME,
            contents=batch
        )
        all_embeddings.extend(result.embeddings)

    # 5. Create a dictionary mapping terms to their embeddings
    term_embedding_map = {
        term: embedding.values for term, embedding in zip(unique_terms, all_embeddings)
    }

    # 6. Save the embeddings to a JSON file
    with open(EMBEDDINGS_FILE_PATH, "w") as f:
        json.dump(term_embedding_map, f, indent=2)

    print(f"Successfully generated and saved {len(term_embedding_map)} embeddings.")
    print(f"Embeddings saved to {EMBEDDINGS_FILE_PATH}")


if __name__ == "__main__":
    generate_embeddings()