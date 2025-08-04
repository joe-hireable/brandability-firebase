"""
Core logic for the Trademark Case Ingestion function.

This module contains the implementation for processing PDF case documents,
extracting structured data using Gemini AI, and storing the results in Firestore.
It also extracts the full text from the PDF, chunks it, and creates embeddings
for vector search.

The extraction process uses a two-pass approach:
1. Global Pass: High-level analysis of the entire document to identify its structure
2. Targeted Pass: Detailed extraction from specific chunks with parallel processing
"""

import json
import logging
import os
import re
import tempfile
import time
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Tuple

import pdfplumber
from firebase_admin import firestore, storage
from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from models import Case

# Configure logging
logger = logging.getLogger(__name__)

# Lazily initialized clients to ensure Firebase is initialized first.
_db_client = None
_gemini_client = None

def get_firestore_client():
    """Initializes and returns a Firestore client, reusing if possible."""
    global _db_client
    if not _db_client:
        if not firebase_admin._apps:
            # This will use Application Default Credentials by default.
            # For local testing, the test runner handles FIRESTORE_EMULATOR_HOST.
            firebase_admin.initialize_app()
        _db_client = firestore.client()
    return _db_client

def get_gemini_client():
    """Initializes and returns a Gemini client, reusing if possible."""
    global _gemini_client
    if not _gemini_client:
        # The API key should be set as an environment variable for security.
        _gemini_client = genai.Client()
    return _gemini_client

def load_prompts() -> Dict[str, str]:
    """Loads system and user prompts from their respective files."""
    try:
        # Assuming the script is run from the 'functions' directory
        base_path = Path(__file__).parent.parent
        with open(base_path / 'data/prompts/system_prompt.txt', 'r', encoding='utf-8') as f:
            system_prompt = f.read()
        with open(base_path / 'data/prompts/user_prompt.txt', 'r', encoding='utf-8') as f:
            user_prompt = f.read()
        return {"system_prompt": system_prompt, "user_prompt": user_prompt}
    except FileNotFoundError as e:
        logger.error(f"Prompt file not found: {e}")
        raise

def extract_document_structure(pdf_path: str, case_ref: str) -> Dict[str, Any]:
    """
    First pass of the two-pass extraction process. This function analyzes the document
    structure and identifies key sections for targeted extraction in the second pass.
    
    Args:
        pdf_path: The path to the PDF file.
        case_ref: The case reference.
        
    Returns:
        A dictionary containing the document structure, including identified sections
        and their positions.
    """
    logger.info(f"Extracting document structure for case: {case_ref}")
    
    # Extract heading-aware chunks first
    chunks = create_heading_aware_chunks(pdf_path, case_ref)
    
    # Prepare to send the full document to Gemini for high-level analysis
    gemini_client = get_gemini_client()
    try:
        # Corrected: The SDK uses the 'file' argument, not 'path'.
        uploaded_file = gemini_client.files.upload(file=pdf_path)
        prompts = load_prompts()
        
        logger.info("Calling Gemini API for document structure analysis...")
        
        # Define the structure analysis prompt
        structure_prompt = """
        Analyze this trademark opposition case document and identify its structure.
        
        Specifically:
        1. Identify the case reference, applicant name, and opponent name
        2. List all major sections in the document (e.g., Background & Pleadings, Comparison of Goods)
        3. For each section, provide its approximate starting page number
        4. Identify which sections contain key information about:
           - The contested marks
           - The goods and services being compared
           - The comparison of the marks
           - The likelihood of confusion assessment
           - The final decision
        
        Return the information in a structured JSON format.
        """
        
        response = gemini_client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[
                structure_prompt,
                uploaded_file
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        
        logger.info("Successfully received structure analysis from Gemini.")
        
        # Parse the response
        structure_data = json.loads(response.text)
        
        # Add the chunks we already created to the structure data
        structure_data["chunks"] = chunks
        
        return structure_data
        
    except (APIError, json.JSONDecodeError) as e:
        logger.error(f"Error during document structure analysis: {e}")
        
        # If Gemini analysis fails, return just the chunks we extracted
        return {"chunks": chunks, "error": str(e)}
    finally:
        if 'uploaded_file' in locals() and uploaded_file:
            get_gemini_client().files.delete(name=uploaded_file.name)
            logger.info(f"Deleted temporary file from Gemini File API: {uploaded_file.name}")

def extract_from_chunk(chunk: Dict[str, Any], prompts: Dict[str, str], pdf_path: str) -> Dict[str, Any]:
    """
    Extract structured data from a specific chunk using Gemini.
    
    Args:
        chunk: The chunk to process.
        prompts: The system and user prompts.
        pdf_path: The path to the PDF file (for reference if needed).
        
    Returns:
        A dictionary containing the extracted data.
    """
    # Create a prompt specific to this chunk's section
    section = chunk["metadata"].get("section", "")
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
    elif "Distinctive character" in section:
        extraction_focus = "Focus on extracting distinctive_character information."
    elif "Average consumer" in section:
        extraction_focus = "Focus on extracting average_consumer_attention information."
    
    # Prepare the tailored prompt
    tailored_prompt = f"{prompts['user_prompt']}\n\n{extraction_focus}\n\nSection: {section}\n\n<case>\n{text}\n</case>"
    
    gemini_client = get_gemini_client()
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[
                prompts["system_prompt"],
                tailored_prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        
        # Parse the response
        extracted_data = json.loads(response.text)
        return extracted_data
        
    except (APIError, json.JSONDecodeError) as e:
        logger.error(f"Error extracting data from chunk {chunk['metadata'].get('chunk_sequence')}: {e}")
        return {"error": str(e)}

def extract_data_from_chunks(structure_data: Dict[str, Any], prompts: Dict[str, str], pdf_path: str) -> Dict[str, Any]:
    """
    Second pass of the two-pass extraction process. This function performs targeted
    extraction on specific chunks identified in the first pass, using parallel processing.
    
    Args:
        structure_data: The document structure identified in the first pass.
        prompts: The system and user prompts.
        pdf_path: The path to the PDF file.
        
    Returns:
        A dictionary containing the extracted structured data.
    """
    logger.info(f"Starting targeted extraction with parallel processing")
    
    chunks = structure_data.get("chunks", [])
    if not chunks:
        logger.warning("No chunks found for extraction")
        return {}
    
    # Define maximum workers based on available CPU cores
    max_workers = min(len(chunks), os.cpu_count() or 4)
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit extraction tasks for each chunk
        future_to_chunk = {
            executor.submit(extract_from_chunk, chunk, prompts, pdf_path): chunk
            for chunk in chunks
        }
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_chunk):
            chunk = future_to_chunk[future]
            try:
                result = future.result()
                results.append({
                    "chunk_metadata": chunk["metadata"],
                    "extracted_data": result
                })
                logger.info(f"Successfully processed chunk {chunk['metadata'].get('chunk_sequence')} ({chunk['metadata'].get('section', 'unknown section')})")
            except Exception as e:
                logger.error(f"Error processing chunk {chunk['metadata'].get('chunk_sequence')}: {e}")
    
    # Combine results from all chunks
    combined_data = combine_extraction_results(results, structure_data)
    
    return combined_data

def deep_merge(source: Dict, destination: Dict) -> Dict:
    """
    Recursively merges source dict into destination dict.
    - Dictionaries are merged recursively.
    - Lists are extended, avoiding duplicates.
    - Other types from source overwrite destination if not None.
    """
    for key, value in source.items():
        if isinstance(value, dict) and key in destination and isinstance(destination[key], dict):
            destination[key] = deep_merge(value, destination[key])
        elif isinstance(value, list) and key in destination and isinstance(destination[key], list):
            for item in value:
                # A simple check for dicts; more complex identity checks might be needed
                if isinstance(item, dict):
                    if not any(d == item for d in destination[key]):
                        destination[key].append(item)
                elif item not in destination[key]:
                    destination[key].append(item)
        elif value is not None:
            # Overwrite only if the new value is not None
            # This prevents overwriting a found value with an empty one
            if value or (not destination.get(key)):
                 destination[key] = value
    return destination

def combine_extraction_results(results: List[Dict[str, Any]], structure_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Combine extraction results from individual chunks into a coherent whole
    using a deep merge strategy.
    
    Args:
        results: List of extraction results from individual chunks.
        structure_data: The overall document structure.
        
    Returns:
        A combined and validated data structure.
    """
    # Initialize with a structure that matches the Case model to guide the merge
    combined_data = Case.model_construct().model_dump()

    # Pre-populate with high-level data from the structure analysis
    if "case_details" in structure_data:
        combined_data = deep_merge(structure_data["case_details"], combined_data)

    # Process each chunk's extraction results
    for result in results:
        data = result.get("extracted_data", {})
        
        # Skip if there's an error or no data
        if "error" in data or not data:
            continue

        # The model sometimes returns a list with a single dict
        if isinstance(data, list) and data:
            data = data[0]

        if not isinstance(data, dict):
            logger.warning(f"Extracted data for section '{result['chunk_metadata'].get('section')}' is not a dict, skipping.")
            continue
            
        # Deep merge the extracted data from the chunk into the main object
        combined_data = deep_merge(data, combined_data)
    
    return combined_data

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def extract_structured_data(pdf_path: str) -> Case:
    """
    Extracts structured data from a PDF using a single, schema-enforced pass.

    This approach is more robust as it provides the full document context to the
    model and leverages Gemini's ability to directly generate a valid JSON object
    that conforms to the Pydantic schema.

    Args:
        pdf_path: The local path to the PDF file.

    Returns:
        A `Case` object populated with the extracted data.
    """
    logger.info(f"Starting structured data extraction for PDF: {pdf_path}")
    prompts = load_prompts()
    gemini_client = get_gemini_client()
    uploaded_file = None

    try:
        # Upload the entire PDF for the model to analyze
        uploaded_file = gemini_client.files.upload(file=pdf_path)
        
        # Make a single, direct call to the model, enforcing the Case schema
        logger.info("Calling Gemini API with schema enforcement for structured data extraction...")
        response = gemini_client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[
                prompts["system_prompt"],
                prompts["user_prompt"],
                uploaded_file
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Case,
            ),
        )
        
        # The response text is a JSON string guaranteed to match the schema
        extracted_data = json.loads(response.text)
        
        # Validate the data (which should always pass due to schema enforcement)
        case_obj = Case.model_validate(extracted_data)
        logger.info(f"Successfully parsed and validated structured case data for: {case_obj.case_reference}")
        return case_obj
        
    except (APIError, ValidationError, json.JSONDecodeError) as e:
        logger.error(f"Error during structured extraction or validation: {e}")
        raise
    finally:
        # Clean up the uploaded file
        if uploaded_file:
            gemini_client.files.delete(name=uploaded_file.name)
            logger.info(f"Deleted temporary file from Gemini File API: {uploaded_file.name}")

def extract_full_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts all text content from a PDF file.

    Args:
        pdf_path: The local path to the PDF file.

    Returns:
        A string containing the entire text of the PDF.
    """
    logger.info(f"Starting FULL TEXT extraction for PDF: {pdf_path}")
    full_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
        logger.info(f"Successfully extracted full text from {len(pdf.pages)} pages.")
        return full_text
    except Exception as e:
        logger.error(f"Failed to extract full text from PDF {pdf_path}: {e}")
        raise

def extract_case_reference(pdf_path: str) -> str:
    """
    Extract the case reference from the PDF filename or first page.
    
    Args:
        pdf_path: The path to the PDF file.
        
    Returns:
        A string containing the case reference.
    """
    # Try to get from filename first
    # Robustly get the filename regardless of OS path separator
    filename = str(pdf_path).replace("\\", "/").split("/")[-1]

    # Common patterns: O-1234-23, O/1234/23, etc.
    match = re.search(r'([A-Z][/-]\d{4,}[/-]\d{2,})', filename)
    if match:
        # Standardize reference to use slashes
        return match.group(1).replace('-', '/')
    
    # If not in filename, try to extract from first page
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if pdf.pages:
                first_page_text = pdf.pages[0].extract_text()
                # Look for patterns like "O/1234/23" or "O-1234-23"
                match = re.search(r'([A-Z][/-]\d{4,}[/-]\d{2,})', first_page_text)
                if match:
                    # Standardize reference to use slashes
                    return match.group(1).replace('-', '/')
    except Exception as e:
        logger.warning(f"Could not extract case reference from PDF '{pdf_path}': {e}")
    
    # Fallback to a timestamp-based ID
    logger.warning(f"Could not find case reference for {pdf_path}, falling back to generated ID.")
    return f"CASE-{int(time.time())}"

def create_heading_aware_chunks(pdf_path: str, case_ref: str) -> List[Dict[str, Any]]:
    """
    Creates contextually relevant chunks from a PDF based on document headings.
    
    This function extracts text from a PDF, identifies section headings, and creates
    logical chunks based on the document's structure. This produces more semantically
    meaningful chunks compared to a simple word-count approach.
    
    Args:
        pdf_path: The path to the PDF file.
        case_ref: The case reference to associate with the chunks.
        
    Returns:
        A list of dictionaries, where each dictionary represents a text chunk with
        metadata about its section and position in the document.
    """
    logger.info(f"Creating heading-aware chunks for case: {case_ref}")
    
    # Common headings in trademark opposition cases
    COMMON_HEADINGS = [
        r"Background\s+&\s+pleadings",
        r"(?:Opponent|Applicant)'?s?\s+evidence",
        r"Relevant\s+statutory\s+provision",
        r"Proof\s+of\s+use",
        r"Comparison\s+of\s+(?:the\s+)?goods\s+and\s+services",
        r"Average\s+consumer\s+and\s+the\s+(?:nature\s+of\s+the\s+)?purchasing\s+(?:process|act)",
        r"Comparison\s+of\s+(?:the\s+)?(?:trade\s+)?marks",
        r"Distinctive\s+character\s+of\s+the\s+earlier\s+mark",
        r"Likelihood\s+of\s+confusion",
        r"Section\s+5\(\d\)(?:\([a-z]\))?",
        r"Conclusion",
        r"Decision",
        r"Costs"
    ]
    
    # Extract full text from PDF
    full_text = ""
    section_markers = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            current_position = 0
            
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if not page_text:
                    continue
                
                # Look for headings in this page
                lines = page_text.split('\n')
                for line_num, line in enumerate(lines):
                    # Clean the line for regex matching
                    clean_line = line.strip()
                    
                    # Check if this line matches any of our heading patterns
                    for heading_pattern in COMMON_HEADINGS:
                        if re.search(heading_pattern, clean_line, re.IGNORECASE):
                            # Found a heading - add to markers
                            position = current_position + len('\n'.join(lines[:line_num]))
                            section_markers.append({
                                "heading": clean_line,
                                "position": position,
                                "page": page_num + 1
                            })
                            break
                
                full_text += page_text + "\n"
                current_position += len(page_text) + 1  # +1 for the newline
                
            logger.info(f"Found {len(section_markers)} section headings in document")
    
    except Exception as e:
        logger.error(f"Failed to extract sections from PDF {pdf_path}: {e}")
        raise
    
    # Create chunks based on section markers
    chunks = []
    
    if not section_markers:
        # Fallback to simple chunking if no sections found
        logger.warning(f"No section headings found in {pdf_path}, falling back to simple chunking")
        return create_simple_chunks(full_text, case_ref)
    
    # Sort markers by position
    section_markers.sort(key=lambda x: x["position"])
    
    # Add document end as final marker
    section_markers.append({
        "heading": "END_OF_DOCUMENT",
        "position": len(full_text),
        "page": -1
    })
    
    # Create chunks between markers
    for i in range(len(section_markers) - 1):
        start_pos = section_markers[i]["position"]
        end_pos = section_markers[i+1]["position"]
        
        section_text = full_text[start_pos:end_pos].strip()
        if not section_text:
            continue
            
        # Create chunk
        chunks.append({
            "text": section_text,
            "metadata": {
                "case_reference": case_ref,
                "section": section_markers[i]["heading"],
                "page": section_markers[i]["page"],
                "chunk_sequence": len(chunks),
                "chunk_type": "section"
            }
        })
    
    logger.info(f"Created {len(chunks)} section-based chunks for case {case_ref}")
    return chunks

def create_simple_chunks(full_text: str, case_ref: str, chunk_size: int = 500, overlap: int = 50) -> List[Dict[str, Any]]:
    """
    Fallback chunking method that splits by word count. Used if heading detection fails.
    
    Args:
        full_text: The entire text content of the PDF.
        case_ref: The case reference to associate with the chunks.
        chunk_size: The number of words per chunk.
        overlap: The number of words to overlap between chunks.

    Returns:
        A list of dictionaries, where each dictionary represents a text chunk.
    """
    logger.info(f"Creating simple text chunks for case: {case_ref}")
    words = full_text.split()
    if not words:
        return []

    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk_text = " ".join(words[i:i + chunk_size])
        chunks.append({
            "text": chunk_text,
            "metadata": {
                "case_reference": case_ref,
                "chunk_sequence": len(chunks),
                "chunk_type": "simple"
            }
        })
    logger.info(f"Created {len(chunks)} simple chunks for case {case_ref}")
    return chunks

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
            content=texts_to_embed,
            task_type="retrieval_document",
        )
        logger.info("Successfully generated embeddings.")
        # The result is a dict with a list of embeddings
        return result["embedding"]
    except APIError as e:
        logger.error(f"Failed to generate embeddings: {e}")
        raise

def store_data_in_firestore(case: Case, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
    """
    Stores the main case data and its text chunks with embeddings in Firestore.

    Args:
        case: The structured `Case` object.
        chunks: The list of text chunks from the full PDF text.
        embeddings: The list of corresponding embedding vectors.
    """
    case_ref = case.case_reference
    logger.info(f"Storing all data for {case_ref} in Firestore...")
    
    db_client = get_firestore_client()
    batch = db_client.batch()
    
    # Set main case document (structured data)
    case_doc_ref = db_client.collection("cases").document(case_ref)
    case_data = case.model_dump(mode='json')
    case_data.update({
        "createdAt": firestore.SERVER_TIMESTAMP,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    })
    batch.set(case_doc_ref, case_data)
    
    # Set each chunk in the subcollection for vector search
    if chunks and embeddings:
        chunks_collection_ref = case_doc_ref.collection("chunks")
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_doc_ref = chunks_collection_ref.document(f"chunk_{i:04d}")
            chunk_data = {
                **chunk,
                "embedding": embedding,
                "createdAt": firestore.SERVER_TIMESTAMP,
            }
            batch.set(chunk_doc_ref, chunk_data)
        
    batch.commit()
    logger.info(f"Successfully stored structured data and {len(chunks)} text chunks for {case_ref}.")

def process_case_from_storage(bucket_name: str, file_name: str):
    """
    Orchestrates the entire case ingestion process for a file from Cloud Storage.
    
    This function implements a two-step process:
    1. Structured data extraction using a two-pass approach with Gemini
    2. Vector search preparation with heading-aware text chunking and embeddings
    """
    logger.info(f"Processing file: {file_name} from bucket: {bucket_name}")
    
    bucket = storage.bucket(bucket_name)
    blob = bucket.blob(file_name)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        try:
            blob.download_to_filename(temp_pdf.name)
            logger.info(f"Downloaded {file_name} to temporary file {temp_pdf.name}")
            
            # Step 1: Extract structured data using improved two-pass approach
            logger.info("Starting structured data extraction with two-pass approach")
            case_obj = extract_structured_data(temp_pdf.name)
            
            # Step 2: Extract heading-aware chunks for vector search
            logger.info("Starting heading-aware chunking for vector search")
            text_chunks = create_heading_aware_chunks(temp_pdf.name, case_obj.case_reference)
            
            # If heading-based chunking yielded very few chunks, complement with text-based chunks
            if len(text_chunks) < 3:
                logger.info("Few section-based chunks found, complementing with full-text chunks")
                full_pdf_text = extract_full_text_from_pdf(temp_pdf.name)
                simple_chunks = create_simple_chunks(full_pdf_text, case_obj.case_reference)
                text_chunks.extend(simple_chunks)
            
            # Generate embeddings for the text chunks
            embeddings = generate_embeddings(text_chunks)
            
            # Store both structured data and text chunks in Firestore
            store_data_in_firestore(case_obj, text_chunks, embeddings)
            
            logger.info(f"Successfully completed ingestion for {case_obj.case_reference}")
            
        except Exception as e:
            logger.error(f"Case ingestion pipeline failed for {file_name}: {e}", exc_info=True)
            raise
        finally:
            os.remove(temp_pdf.name)
            logger.info(f"Removed temporary file: {temp_pdf.name}")
