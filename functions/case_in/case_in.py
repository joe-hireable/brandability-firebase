"""
Case Ingestion Orchestrator.

This module orchestrates the entire case ingestion pipeline, coordinating
the different steps of processing PDF case documents:
1. Chunking the PDF using Vision-Guided Chunking
2. Generating embeddings for the chunks
3. Extracting structured predictive data
4. Storing all results in Firestore

This orchestrator ensures that each step is performed in the correct order
and handles errors appropriately.
"""

import logging
import os
import tempfile
from typing import Dict, List, Any

from firebase_admin import storage

from .chunk_pdf import chunk_pdf
from .generate_embeddings import generate_embeddings
from .extract_predictive_data import extract_structured_data
from utils.firestore_helpers import store_data_in_firestore
from models import Case, MarkComparison

# Configure logging
logger = logging.getLogger(__name__)

def process_case_from_storage(bucket_name: str, file_name: str):
    """
    Orchestrates the entire case ingestion process for a file from Cloud Storage.
    
    This function implements the following pipeline:
    1. Download the PDF from Cloud Storage
    2. Extract chunks using Vision-Guided Chunking
    3. Generate embeddings for vector search
    4. Extract structured data for predictive analysis
    5. Store everything in Firestore
    
    Args:
        bucket_name: The name of the Cloud Storage bucket.
        file_name: The name of the file in the bucket.
    """
    logger.info(f"Processing file: {file_name} from bucket: {bucket_name}")
    
    bucket = storage.bucket(bucket_name)
    blob = bucket.blob(file_name)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        try:
            # Step 1: Download the PDF from Cloud Storage
            blob.download_to_filename(temp_pdf.name)
            logger.info(f"Downloaded {file_name} to temporary file {temp_pdf.name}")
            
            # Step 2: Extract chunks using Vision-Guided Chunking
            logger.info("Starting Vision-Guided Chunking")
            text_chunks, case_ref = chunk_pdf(temp_pdf.name)
            logger.info(f"Created {len(text_chunks)} chunks for case {case_ref}")
            
            # Step 3: Generate embeddings for the text chunks
            logger.info("Generating embeddings for vector search")
            embeddings = generate_embeddings(text_chunks)
            logger.info(f"Generated {len(embeddings)} embeddings")
            
            # Step 4: Extract structured data for predictive analysis (SKIPPED FOR THIS TEST)
            logger.info("Skipping structured data extraction for this test.")
            # case_obj = extract_structured_data(temp_pdf.name)
            # logger.info(f"Extracted structured data for case: {case_obj.case_reference}")
            
            # Create a placeholder Case object for storing chunks and embeddings
            # In a real scenario, this would be populated by extract_structured_data
            placeholder_mark_comparison = MarkComparison(
                visual_similarity="dissimilar",
                aural_similarity="dissimilar",
                conceptual_similarity="dissimilar"
            )
            case_obj = Case(
                case_reference=case_ref,
                decision_date="01/01/1970",
                decision_maker="System",
                application_number="unknown",
                applicant_name="unknown",
                opponent_name="unknown",
                applicant_marks=[],
                opponent_marks=[],
                grounds_for_opposition=[],
                proof_of_use_requested=False,
                goods_services_comparison=[],
                mark_comparison=placeholder_mark_comparison,
                distinctive_character="low_degree",
                average_consumer_attention="low",
                likelihood_of_confusion=False
            )

            # Step 5: Store everything in Firestore
            logger.info("Storing all data in Firestore")
            store_data_in_firestore(case_obj, text_chunks, embeddings)
            
            logger.info(f"Successfully completed ingestion for {case_obj.case_reference}")
            
        except Exception as e:
            logger.error(f"Case ingestion pipeline failed for {file_name}: {e}", exc_info=True)
            raise
        finally:
            # Clean up temporary file
            temp_pdf.close()
            os.remove(temp_pdf.name)
            logger.info(f"Removed temporary file: {temp_pdf.name}")