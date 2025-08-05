"""
Predictive Data Extraction for Trademark Cases.

This module extracts structured data from PDF case documents using Gemini 2.5 Pro,
with the aim of creating a predictive dataset for trademark case outcome prediction.
The extraction follows a schema-enforced approach to ensure consistent data quality.
"""

import json
import logging
import os
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter

from google.genai import types
from google.genai.errors import APIError
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from utils.clients import get_gemini_client
from .chunk_pdf import chunk_pdf
from models import Case

# Configure logging
logger = logging.getLogger(__name__)

def load_prompts() -> Dict[str, str]:
    """Loads system and user prompts from their respective files."""
    try:
        # Get the base path (project root)
        base_path = Path(__file__).parent.parent.parent
        with open(base_path / 'data/prompts/system_prompt.txt', 'r', encoding='utf-8') as f:
            system_prompt = f.read()
        with open(base_path / 'data/prompts/user_prompt.txt', 'r', encoding='utf-8') as f:
            user_prompt = f.read()
        return {"system_prompt": system_prompt, "user_prompt": user_prompt}
    except FileNotFoundError as e:
        logger.error(f"Prompt file not found: {e}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def extract_from_chunk(chunk: Dict[str, Any], prompts: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Extracts structured data from a single chunk by calling the Gemini API multiple times.
    
    Args:
        chunk: The chunk to process.
        prompts: The system and user prompts.
        
    Returns:
        A list of dictionaries, each containing one extraction result from the API.
    """
    section = chunk["metadata"].get("section", "General")
    text = chunk["text"]
    
    # Tailor the extraction focus based on the section
    extraction_focus = ""
    if "Background" in section:
        extraction_focus = "Focus on extracting case reference, decision date, decision maker, jurisdiction, application number, applicant and opponent names."
    elif "Comparison of goods" in section:
        extraction_focus = "Focus on extracting goods_services_comparison data."
    elif "Comparison of marks" in section:
        extraction_focus = "Focus on extracting mark_comparison data (visual, aural, conceptual similarity)."
    elif "Likelihood of confusion" in section:
        extraction_focus = "Focus on extracting likelihood_of_confusion, confusion_type, and opposition_outcome."
    
    tailored_prompt = f"{prompts['user_prompt']}\n\n{extraction_focus}\n\nSection: {section}\n\n<case>\n{text}\n</case>"
    
    gemini_client = get_gemini_client()
    
    # Call the API 5 times for the same chunk
    extraction_results = []
    for i in range(5):
        try:
            response = gemini_client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[
                    prompts["system_prompt"],
                    tailored_prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=Case,
                ),
            )
            extraction_results.append(json.loads(response.text))
        except (APIError, json.JSONDecodeError) as e:
            logger.error(f"Error on extraction attempt {i+1} for chunk {chunk['metadata'].get('chunk_sequence')}: {e}")
            extraction_results.append({"error": str(e)})
            
    return extraction_results

def extract_data_from_chunks(chunks: List[Dict[str, Any]], prompts: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Performs targeted extraction on all chunks in parallel.
    
    Args:
        chunks: A list of all chunks to process.
        prompts: The system and user prompts.
        
    Returns:
        A list of results, where each result contains the metadata of the chunk
        and a list of the 5 extraction attempts.
    """
    logger.info(f"Starting targeted extraction for {len(chunks)} chunks with parallel processing.")
    
    max_workers = min(len(chunks), os.cpu_count() or 4)
    all_results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_chunk = {
            executor.submit(extract_from_chunk, chunk, prompts): chunk
            for chunk in chunks
        }
        
        for future in concurrent.futures.as_completed(future_to_chunk):
            chunk = future_to_chunk[future]
            try:
                result = future.result()
                all_results.append({
                    "chunk_metadata": chunk["metadata"],
                    "extraction_attempts": result
                })
                logger.info(f"Successfully processed chunk {chunk['metadata'].get('chunk_sequence')}")
            except Exception as e:
                logger.error(f"Error processing chunk {chunk['metadata'].get('chunk_sequence')}: {e}")
    
    return all_results

def combine_extraction_results(results: List[Dict[str, Any]]) -> Case:
    """
    Combines extraction results from all chunks by finding the most common value for each field.
    
    Args:
        results: A list of all extraction results from all chunks.
        
    Returns:
        A single, validated Case object.
    """
    final_data = {}
    
    # Get all field names from the Case model
    all_fields = Case.model_fields.keys()
    
    for field in all_fields:
        all_values = []
        for result in results:
            for attempt in result["extraction_attempts"]:
                if field in attempt:
                    value = attempt[field]
                    # Handle nested dicts and lists by converting them to a hashable format
                    if isinstance(value, dict):
                        all_values.append(json.dumps(value, sort_keys=True))
                    elif isinstance(value, list):
                        all_values.extend([json.dumps(item, sort_keys=True) if isinstance(item, dict) else item for item in value])
                    else:
                        all_values.append(value)
        
        if all_values:
            # Find the most common value
            most_common = Counter(all_values).most_common(1)[0][0]
            # Convert back from JSON if needed
            try:
                final_data[field] = json.loads(most_common)
            except (json.JSONDecodeError, TypeError):
                final_data[field] = most_common

    return Case.model_validate(final_data)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def extract_structured_data(pdf_path: str) -> Case:
    """
    Extracts structured data from a PDF using a multi-pass, parallel, chunk-based approach.

    This approach is inspired by Google's langextract and aims for high accuracy by:
    1.  Chunking the document into semantically relevant sections.
    2.  Processing each chunk in parallel.
    3.  Making multiple API calls per chunk to get a variety of extraction results.
    4.  Aggregating the results to find the most common, and therefore most likely, correct value for each field.

    Args:
        pdf_path: The local path to the PDF file.

    Returns:
        A `Case` object populated with the extracted data.
    """
    logger.info(f"Starting multi-pass structured data extraction for PDF: {pdf_path}")
    prompts = load_prompts()
    
    # First pass: Chunk the document
    chunks, case_ref = chunk_pdf(pdf_path)
    
    # Second pass: Extract data from chunks in parallel
    results = extract_data_from_chunks(chunks, prompts)
    
    # Third pass: Combine and validate the results
    final_case = combine_extraction_results(results)
    final_case.case_reference = case_ref
    
    logger.info(f"Successfully parsed and validated structured case data for: {final_case.case_reference}")
    return final_case