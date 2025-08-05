"""
Firestore helper functions for the trademark prediction system.

This module handles data storage operations in Firestore, including
storing cases, chunks, embeddings, and other structured data.
"""

import logging
from typing import List, Dict, Any

from firebase_admin import firestore
from pydantic import BaseModel
from .clients import get_firestore_client
from models import Case

# Configure logging
logger = logging.getLogger(__name__)

def store_data_in_firestore(case: Case, chunks: List[Dict[str, Any]]):
    """
    Stores the main case data and its text chunks in Firestore.

    Embeddings are stored separately in Vertex AI Vector Search.

    Args:
        case: The structured `Case` object.
        chunks: The list of text chunks from the full PDF text, each with a unique 'chunk_id'.
    """
    case_ref = case.case_reference
    # Sanitize the case reference to be used as a document ID
    doc_id = case_ref.replace('/', '-')
    logger.info(f"Storing data for {case_ref} (doc_id: {doc_id}) in Firestore...")
    
    db_client = get_firestore_client()
    batch = db_client.batch()
    
    # Set main case document (structured data)
    case_doc_ref = db_client.collection("cases").document(doc_id)
    case_data = case.model_dump(mode='json')
    case_data.update({
        "createdAt": firestore.SERVER_TIMESTAMP,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    })
    batch.set(case_doc_ref, case_data)
    
    # Set each chunk in the subcollection
    if chunks:
        chunks_collection_ref = case_doc_ref.collection("chunks")
        for chunk in chunks:
            # Use the unique chunk_id generated in the orchestrator
            chunk_id = chunk["metadata"]["chunk_id"]
            chunk_doc_ref = chunks_collection_ref.document(chunk_id)
            
            chunk_data = {
                "text": chunk["text"],
                "metadata": chunk["metadata"],
                "createdAt": firestore.SERVER_TIMESTAMP,
            }
            batch.set(chunk_doc_ref, chunk_data)
        
    batch.commit()
    logger.info(f"Successfully stored structured data and {len(chunks)} text chunks for {case_ref}.")

def update_case_data(case_ref: str, data: Dict[str, Any]):
    """
    Updates specific fields in a case document.

    Args:
        case_ref: The case reference ID.
        data: Dictionary of fields to update.
    """
    logger.info(f"Updating case data for {case_ref}")
    
    db_client = get_firestore_client()
    case_doc_ref = db_client.collection("cases").document(case_ref)
    
    # Add the update timestamp
    data["updatedAt"] = firestore.SERVER_TIMESTAMP
    
    case_doc_ref.update(data)
    logger.info(f"Successfully updated case data for {case_ref}")

def store_model_object(collection: str, doc_id: str, model_obj: BaseModel, merge: bool = False):
    """
    Generic function to store a Pydantic model in Firestore.

    Args:
        collection: Firestore collection name.
        doc_id: Document ID.
        model_obj: Pydantic model instance to store.
        merge: Whether to merge with existing document (True) or overwrite (False).
    """
    logger.info(f"Storing {type(model_obj).__name__} in {collection}/{doc_id}")
    
    db_client = get_firestore_client()
    doc_ref = db_client.collection(collection).document(doc_id)
    
    # Convert model to dict and add timestamps
    data = model_obj.model_dump(mode='json')
    data.update({
        "createdAt": firestore.SERVER_TIMESTAMP,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    })
    
    if merge:
        doc_ref.set(data, merge=True)
    else:
        doc_ref.set(data)
        
    logger.info(f"Successfully stored {type(model_obj).__name__} in {collection}/{doc_id}")