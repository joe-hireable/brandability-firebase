"""
Predictive Data Extraction for Trademark Cases.

This module extracts structured data from PDF case documents using Gemini 2.5 Pro,
with the aim of creating a predictive dataset for trademark case outcome prediction.
The extraction follows a schema-enforced approach to ensure consistent data quality.
"""

import json
import logging
import os
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter

from google.genai import types
import tempfile
from google.cloud import storage
from google.genai.errors import APIError
from pydantic import ValidationError

from utils.clients import get_gemini_client
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

def get_extraction_attempts(bucket_name: str, file_name: str, prompts: Dict[str, str], num_passes: int = 5) -> List[Dict[str, Any]]:
    """
    Calls the Gemini API multiple times with the PDF content to get multiple extraction results.
    
    Args:
        bucket_name: The GCS bucket name.
        file_name: The name of the file in the bucket.
        prompts: The system and user prompts.
        num_passes: The number of times to call the API.
        
    Returns:
        A list of dictionaries, each containing one extraction result from the API.
    """
    gs_uri = f"gs://{bucket_name}/{file_name}"
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    # Create a temporary file to store the PDF, ensuring it's closed before use
    # to avoid PermissionError on Windows.
    temp_pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_pdf_file.close()
    
    try:
        blob.download_to_filename(temp_pdf_file.name)
        with open(temp_pdf_file.name, 'rb') as f:
            pdf_bytes = f.read()
    finally:
        os.remove(temp_pdf_file.name)

    pdf_part = types.Part.from_bytes(
        data=pdf_bytes,
        mime_type="application/pdf"
    )
    
    gemini_client = get_gemini_client()
    extraction_results = []
    
    for i in range(num_passes):
        try:
            response = gemini_client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[prompts["user_prompt"], pdf_part],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=Case,
                    system_instruction=prompts["system_prompt"],
                ),
            )
            extraction_results.append(json.loads(response.text))
            logger.info(f"Extraction pass {i+1}/{num_passes} successful for {gs_uri}.")
        except (APIError, json.JSONDecodeError, Exception) as e:
            logger.error(f"Error on extraction attempt {i+1}/{num_passes} for {gs_uri}: {e}")
            extraction_results.append({"error": str(e)})
            
    return extraction_results

def combine_extraction_results(extraction_attempts: List[Dict[str, Any]]) -> Case:
    """
    Combines extraction results by finding the most common value for each field.
    
    Args:
        extraction_attempts: A list of all extraction results from the API calls.
        
    Returns:
        A single, validated Case object.
    """
    final_data = {}
    all_fields = Case.model_fields.keys()
    
    for field in all_fields:
        all_values = []
        for attempt in extraction_attempts:
            if isinstance(attempt, dict) and field in attempt and attempt[field] is not None:
                value = attempt[field]
                # Handle nested dicts and lists by converting them to a hashable format
                if isinstance(value, dict):
                    all_values.append(json.dumps(value, sort_keys=True))
                elif isinstance(value, list):
                    # Only add non-empty lists
                    if value:
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

    # Ensure list types are correctly formatted
    for field_name, field_model in Case.model_fields.items():
        if field_name in final_data:
            # Check if the field is a list type
            if hasattr(field_model.annotation, '__origin__') and field_model.annotation.__origin__ is list:
                if not isinstance(final_data[field_name], list):
                    final_data[field_name] = [final_data[field_name]]
            # Ensure application_number is a string
            elif field_name == 'application_number':
                final_data[field_name] = str(final_data[field_name])

    try:
        # Validate the combined data against the Pydantic model
        return Case.model_validate(final_data)
    except ValidationError as e:
        logger.error(f"Failed to validate final combined data: {e}\nFinal data: {final_data}")
        raise

def extract_structured_data(bucket_name: str, file_name: str) -> Case:
    """
    Extracts structured data from a PDF using a multi-pass approach on the full document.

    This approach aims for high accuracy by:
    1.  Passing the PDF's Cloud Storage URI directly to Gemini.
    2.  Making multiple API calls to get a variety of extraction results.
    3.  Aggregating the results to find the most common, and therefore most likely, correct value for each field.

    Args:
        bucket_name: The name of the Cloud Storage bucket.
        file_name: The name of the file in the bucket.

    Returns:
        A `Case` object populated with the extracted data.
    """
    encoded_file_name = urllib.parse.quote(file_name)
    logger.info(f"Starting multi-pass structured data extraction for PDF: gs://{bucket_name}/{file_name}")
    
    prompts = load_prompts()
    
    # Pass 1: Get multiple extraction attempts from the full PDF
    extraction_attempts = get_extraction_attempts(bucket_name, file_name, prompts)
    
    # Pass 2: Combine and validate the results
    final_case = combine_extraction_results(extraction_attempts)
    
    logger.info(f"Successfully parsed and validated structured case data for: {final_case.case_reference}")
    return final_case