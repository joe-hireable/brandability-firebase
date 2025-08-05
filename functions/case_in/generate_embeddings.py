"""
Embeddings Generation for PDF Chunks.

This module handles the generation of embeddings for text chunks extracted from
PDFs. These embeddings enable vector search and semantic retrieval of document
content.
"""

import logging
from typing import List, Dict, Any

from google.genai.errors import APIError
from tenacity import retry, stop_after_attempt, wait_exponential

from utils.clients import get_gemini_client

# Configure logging
logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
def generate_embeddings(chunks: List[Dict[str, Any]]) -> List[List[float]]:
    """
    Generates embeddings for a list of text chunks using Gemini.

    Args:
        chunks: A list of chunk dictionaries, each with a "text" key.

    Returns:
        A list of embedding vectors corresponding to each chunk.
    """
    if not chunks:
        return []
    
    logger.info(f"Generating embeddings for {len(chunks)} chunks...")
    texts_to_embed = [chunk["text"] for chunk in chunks]
    
    gemini_client = get_gemini_client()
    try:
        # Use embed_content which handles batching for lists of strings
        result = gemini_client.models.embed_content(
            model="models/embedding-001",
            contents=texts_to_embed
        )
        logger.info("Successfully generated embeddings.")
        # The result contains a list of embeddings
        return result.embeddings
    except APIError as e:
        logger.error(f"Failed to generate embeddings: {e}")
        raise