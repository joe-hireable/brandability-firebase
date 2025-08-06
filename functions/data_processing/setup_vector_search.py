"""
Sets up and populates the Vertex AI Vector Search index for G&S terms.

This script orchestrates the creation and deployment of the Vector Search index
by leveraging the helper functions in `utils.vector_search_helpers`.

It performs the following high-level steps:
1.  Loads the pre-generated term embeddings from the JSON file.
2.  Defines the configuration for the index and its public endpoint.
3.  Calls the helper functions to create or get the index and endpoint.
4.  Deploys the index to the endpoint.
5.  Formats the embeddings into the required `IndexDatapoint` structure.
6.  Upserts the embeddings to the index, making them available for search.
"""
import json
import sys
import os

# Add the parent 'functions' directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.vector_search_helpers import (
    get_or_create_vector_search_index,
    get_or_create_index_endpoint,
    deploy_index_to_endpoint,
    upsert_embeddings_to_vector_search,
)

# --- Configuration ---
# Load environment variables from .env.test
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env.test'))

EMBEDDINGS_FILE_PATH = "data/term_embeddings.json"
GCS_BUCKET = os.getenv("GCS_BUCKET")
if not GCS_BUCKET:
    raise ValueError("GCS_BUCKET environment variable not set. Please set it in .env.test")

GCS_VECTOR_SEARCH_DIR = "vector_search_index"
GCS_BUCKET_URI = f"gs://{GCS_BUCKET}/{GCS_VECTOR_SEARCH_DIR}"
INDEX_NAME = "goods-and-services-similarity-index"
INDEX_DISPLAY_NAME = "Goods and Services Similarity Index"
ENDPOINT_DISPLAY_NAME = "Goods and Services Similarity Endpoint"
DEPLOYMENT_ID = "gs_similarity_deployment_v1"
EMBEDDING_DIMENSIONS = 3072 # Based on the 'embedding-001' model

def setup_vector_search():
    """
    Main function to orchestrate the setup of the Vector Search index.
    """
    print("--- Starting Vertex AI Vector Search Setup ---")

    # 1. Load the generated embeddings
    print(f"Loading embeddings from {EMBEDDINGS_FILE_PATH}...")
    with open(EMBEDDINGS_FILE_PATH, "r") as f:
        term_embeddings = json.load(f)

    embedding_ids = list(term_embeddings.keys())
    embeddings = list(term_embeddings.values())
    
    # 2. Get or create the Vector Search Index
    print(f"Getting or creating index: {INDEX_DISPLAY_NAME}")
    index = get_or_create_vector_search_index(
        index_name=INDEX_NAME,
        index_display_name=INDEX_DISPLAY_NAME,
        contents_delta_uri=GCS_BUCKET_URI,
        dimensions=EMBEDDING_DIMENSIONS,
    )

    # 3. Get or create the Index Endpoint
    print(f"Getting or creating endpoint: {ENDPOINT_DISPLAY_NAME}")
    endpoint = get_or_create_index_endpoint(
        endpoint_display_name=ENDPOINT_DISPLAY_NAME
    )

    # 4. Deploy the Index to the Endpoint
    print(f"Deploying index to endpoint...")
    deploy_index_to_endpoint(
        endpoint=endpoint,
        index=index,
        deployment_id=DEPLOYMENT_ID
    )

    # 5. Upsert the embeddings to the index
    print("Upserting embeddings to the index...")
    upsert_embeddings_to_vector_search(
        index=index,
        embedding_ids=embedding_ids,
        embeddings=embeddings
    )

    print("\n--- Vertex AI Vector Search Setup Complete! ---")
    print(f"Index Resource Name: {index.resource_name}")
    print(f"Endpoint Resource Name: {endpoint.resource_name}")
    print("Your index is now populated and ready for querying.")


if __name__ == "__main__":
    setup_vector_search()