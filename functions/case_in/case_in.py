"""
Case Ingestion Orchestrator.

This module orchestrates the entire case ingestion pipeline, coordinating
the different steps of processing PDF case documents:
1. Chunking the PDF using Vision-Guided Chunking
2. Generating embeddings for the chunks
3. Extracting structured predictive data
4. Storing chunks and structured data in Firestore
5. Upserting embeddings into Vertex AI Vector Search

This orchestrator ensures that each step is performed in the correct order
and handles errors appropriately.
"""

import logging
import os
import tempfile
import uuid

from firebase_admin import storage

from case_in.chunk_pdf import chunk_pdf
from case_in.generate_embeddings import generate_embeddings
from case_in.extract_predictive_data import extract_structured_data
from utils.firestore_helpers import store_data_in_firestore
from utils.vector_search_helpers import (
    get_or_create_vector_search_index,
    get_or_create_index_endpoint,
    deploy_index_to_endpoint,
    upsert_embeddings_to_vector_search,
)

# Configure logging
logger = logging.getLogger(__name__)

# --- Vector Search Configuration ---
INDEX_NAME = "trademark_cases_index"
INDEX_DISPLAY_NAME = "Trademark Cases Index"
ENDPOINT_DISPLAY_NAME = "Trademark Cases Endpoint"
DEPLOYMENT_ID = "trademark_index"
EMBEDDING_DIMENSIONS = 768 # Based on the output of "models/embedding-001"

def process_case_from_storage(bucket_name: str, file_name: str):
    """
    Orchestrates the entire case ingestion process for a file from Cloud Storage.
    
    This function implements the following pipeline:
    1. Download the PDF from Cloud Storage.
    2. Extract chunks using Vision-Guided Chunking.
    3. Generate embeddings for vector search.
    4. Extract structured data for predictive analysis.
    5. Set up Vertex AI Vector Search index and endpoint.
    6. Upsert embeddings to the index.
    7. Store structured data and text chunks in Firestore.
    
    Args:
        bucket_name: The name of the Cloud Storage bucket.
        file_name: The name of the file in the bucket.
    """
    logger.info(f"Processing file: {file_name} from bucket: {bucket_name}")
    
    bucket = storage.bucket(bucket_name)
    blob = bucket.blob(file_name)
    
    # GCS URI for the index files
    gcs_bucket_for_index = f"gs://{bucket_name}/vector_search_index/"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        try:
            # Step 1: Download the PDF from Cloud Storage
            blob.download_to_filename(temp_pdf.name)
            logger.info(f"Downloaded {file_name} to temporary file {temp_pdf.name}")
            
            # Step 2: Extract chunks using Vision-Guided Chunking
            logger.info("Starting Vision-Guided Chunking for vector search embeddings")
            text_chunks = chunk_pdf(temp_pdf.name)
            logger.info(f"Created {len(text_chunks)} chunks for vector search")
            
            if not text_chunks:
                logger.warning("No chunks were created. Aborting ingestion.")
                return

            # Step 3: Generate embeddings for the text chunks
            logger.info("Generating embeddings for vector search")
            embeddings = generate_embeddings(text_chunks)
            logger.info(f"Generated {len(embeddings)} embeddings")
            
            # Step 4: Extract structured data for predictive analysis
            logger.info("Extracting structured data from PDF using Gemini...")
            case_obj = extract_structured_data(temp_pdf.name)
            logger.info(f"Extracted structured data for case: {case_obj.case_reference}")

            # Step 5: Set up Vertex AI Vector Search index and endpoint
            logger.info("Setting up Vertex AI Vector Search...")
            vector_index = get_or_create_vector_search_index(
                index_name=INDEX_NAME,
                index_display_name=INDEX_DISPLAY_NAME,
                contents_delta_uri=gcs_bucket_for_index,
                dimensions=EMBEDDING_DIMENSIONS
            )
            index_endpoint = get_or_create_index_endpoint(
                endpoint_display_name=ENDPOINT_DISPLAY_NAME
            )
            deploy_index_to_endpoint(index_endpoint, vector_index, DEPLOYMENT_ID)

            # Step 6: Upsert embeddings to the index
            logger.info("Upserting embeddings to Vector Search...")
            # Create unique IDs for each chunk to be used in both Firestore and Vector Search
            chunk_ids = [str(uuid.uuid4()) for _ in text_chunks]
            for i, chunk in enumerate(text_chunks):
                chunk["metadata"]["chunk_id"] = chunk_ids[i]

            upsert_embeddings_to_vector_search(vector_index, chunk_ids, embeddings)

            # Step 7: Store structured data and text chunks in Firestore
            logger.info("Storing case data and text chunks in Firestore")
            store_data_in_firestore(case_obj, text_chunks)
            
            logger.info(f"Successfully completed ingestion for {case_obj.case_reference}")
            
        except Exception as e:
            logger.error(f"Case ingestion pipeline failed for {file_name}: {e}", exc_info=True)
            raise
        finally:
            # Clean up temporary file
            temp_pdf.close()
            os.remove(temp_pdf.name)
            logger.info(f"Removed temporary file: {temp_pdf.name}")