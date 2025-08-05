"""
Predictive Data Extraction for Trademark Cases.

This module extracts structured data from PDF case documents using Gemini 2.5 Pro,
with the aim of creating a predictive dataset for trademark case outcome prediction.
The extraction follows a schema-enforced approach to ensure consistent data quality.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter

from google.genai import types
from google.genai.errors import APIError

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


def get_parallel_extraction_attempts(
    uploaded_file: types.File,
    prompts: Dict[str, str],
    num_passes: int = 5
) -> List[Dict[str, Any]]:
    """
    Creates and executes a batch job to get multiple extraction results in parallel.

    Args:
        uploaded_file: The uploaded file object to use for the requests.
        prompts: The system and user prompts.
        num_passes: The number of times to call the API in parallel.

    Returns:
        A list of dictionaries, each containing one extraction result from the API.
    """
    gemini_client = get_gemini_client()
    logger.info(f"Starting parallel extraction with {num_passes} passes for file: {uploaded_file.name}")

    # Create a part from the uploaded file's URI
    gcs_part = types.Part(file_data=types.FileData(
        file_uri=uploaded_file.uri,
        mime_type="application/pdf"
    ))

    # Create multiple requests for the batch job.
    # The system prompt is placed at the beginning of the contents.
    requests = [
        {
            'contents': [prompts["system_prompt"], gcs_part, prompts["user_prompt"]],
            'config': {
                'response_mime_type': 'application/json',
                'response_schema': Case,
            },
        }
        for _ in range(num_passes)
    ]

    batch_job = gemini_client.batches.create(
        model="models/gemini-2.5-pro",
        src=requests,
        config={
            'display_name': f"extraction-job-{int(time.time())}",
        },
    )
    
    logger.info(f"Created batch job: {batch_job.name}")
    
    while batch_job.state.name not in ('JOB_STATE_SUCCEEDED', 'JOB_STATE_FAILED', 'JOB_STATE_CANCELLED', 'JOB_STATE_EXPIRED'):
        logger.info(f"Job not finished. Current state: {batch_job.state.name}. Waiting 60 seconds...")
        time.sleep(60)
        batch_job = gemini_client.batches.get(name=batch_job.name)

    logger.info(f"Job finished with state: {batch_job.state.name}")
    
    if batch_job.state.name == 'JOB_STATE_FAILED':
        # It's useful to log the details of the failed job for debugging
        logger.error(f"Batch job failed. Error: {batch_job.error}")
        # Optionally, you can inspect individual request errors if available
        if batch_job.dest and batch_job.dest.inlined_responses:
            for i, res in enumerate(batch_job.dest.inlined_responses):
                if res.error:
                    logger.error(f"Request {i} failed with error: {res.error}")
        raise APIError(f"Batch job failed: {batch_job.error}")

    extraction_results = []
    if batch_job.dest and batch_job.dest.inlined_responses:
        for i, inline_response in enumerate(batch_job.dest.inlined_responses):
            try:
                if inline_response.response:
                    pass_result = json.loads(inline_response.response.text)
                    extraction_results.append(pass_result)
                    logger.info(
                        f"Batch extraction pass {i+1}/{num_passes} successful.",
                        extra={'gemini_response': pass_result}
                    )
                else:
                    error_msg = f"Failed to get response from batch pass {i+1}: {inline_response.error}"
                    logger.error(error_msg, exc_info=True)
                    extraction_results.append({"error": str(inline_response.error)})
            except (json.JSONDecodeError, Exception) as e:
                error_msg = f"Failed to parse response from batch pass {i+1}: {e}"
                logger.error(error_msg, exc_info=True)
                extraction_results.append({"error": error_msg})

    return extraction_results


def combine_extraction_results(extraction_attempts: List[Dict[str, Any]]) -> Case:
    """
    Combines extraction results by finding the most common value for each field.
    
    Args:
        extraction_attempts: A list of all extraction results from the API calls.
        
    Returns:
        A single, validated Case object.
    """
    logger.info(f"Combining {len(extraction_attempts)} extraction attempts.")
    final_data = {}
    all_fields = Case.model_fields.keys()

    valid_attempts = [a for a in extraction_attempts if isinstance(a, dict) and "error" not in a]
    if not valid_attempts:
        err_msg = "No successful extraction attempts to combine."
        logger.error(err_msg)
        raise ValueError(err_msg)
    
    logger.info(f"Found {len(valid_attempts)} successful extraction attempts to combine.")

    for field in all_fields:
        all_values = []
        for attempt in valid_attempts:
            if field in attempt and attempt[field] is not None:
                value = attempt[field]
                # Convert values to a hashable format for the Counter
                if isinstance(value, dict):
                    all_values.append(json.dumps(value, sort_keys=True))
                elif isinstance(value, list):
                    try:
                        # Convert list to a tuple of hashable items to count occurrences of the whole list
                        hashable_list = tuple(json.dumps(i, sort_keys=True) if isinstance(i, dict) else i for i in value)
                        all_values.append(hashable_list)
                    except TypeError:
                        logger.warning(f"Could not make value for field '{field}' hashable: {value}")
                else:
                    all_values.append(value)
        
        if all_values:
            # Find the most common value
            most_common = Counter(all_values).most_common(1)[0][0]
            
            # Convert back from JSON/tuple if needed
            final_value = most_common
            if isinstance(most_common, str) and (most_common.startswith('{') or most_common.startswith('[')):
                try:
                    final_value = json.loads(most_common)
                except (json.JSONDecodeError, TypeError):
                    pass # Keep as string if not valid JSON
            elif isinstance(most_common, tuple):
                # Convert tuple back to list and decode items from JSON if necessary
                final_value = [json.loads(i) if (isinstance(i, str) and (i.startswith('{') or i.startswith('['))) else i for i in most_common]

            final_data[field] = final_value
            logger.debug(f"Consolidated value for field '{field}': {final_data.get(field)}")
        else:
            logger.warning(f"No value found for field '{field}' across all extraction attempts.")
            final_data[field] = None # Ensure field exists for pydantic model

    try:
        validated_case = Case(**final_data)
        logger.info(f"Successfully combined and validated extraction results for case: {validated_case.case_reference}")
        return validated_case
    except Exception as e:
        logger.error(f"Failed to validate combined data into Case object: {e}", exc_info=True)
        logger.error(f"Final data that failed validation: {final_data}")
        raise


def extract_structured_data(pdf_path: str) -> Case:
    """
    Extracts structured data from a PDF using a multi-pass, parallel approach.

    This approach aims for high accuracy and efficiency by:
    1.  Uploading the file to Gemini to get a usable URI.
    2.  Using a single batch API call to run all extraction passes in parallel.
    3.  Aggregating the results to find the most common value for each field.

    Args:
        pdf_path: The local path to the PDF file.

    Returns:
        A `Case` object populated with the extracted data.
    """
    logger.info(f"Starting parallel data extraction for PDF: {pdf_path}")
    
    prompts = load_prompts()
    gemini_client = get_gemini_client()
    
    uploaded_file = None
    try:
        # Step 1: Upload the file to Gemini, which returns a file with a URI
        # that the Gemini backend can access.
        logger.info(f"Uploading {pdf_path} to the Gemini API...")
        uploaded_file = gemini_client.files.upload(
            file=pdf_path
        )
        logger.info(f"File uploaded successfully: {uploaded_file.name} ({uploaded_file.uri})")

        # Step 2: Get multiple extraction attempts in parallel using a single batch call
        extraction_attempts = get_parallel_extraction_attempts(uploaded_file, prompts)
        
        # Step 3: Combine and validate the results
        final_case = combine_extraction_results(extraction_attempts)
        
        return final_case

    except Exception as e:
        logger.error(f"Structured data extraction pipeline failed for {pdf_path}: {e}", exc_info=True)
        raise
    finally:
        # Step 4: Clean up resources to avoid unnecessary costs
        if uploaded_file:
            logger.info(f"Deleting uploaded file from Gemini: {uploaded_file.name}")
            gemini_client.files.delete(name=uploaded_file.name)
            logger.info("Uploaded file deleted.")