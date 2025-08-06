"""
Vision-Guided Chunking for PDF Documents.

This module implements a vision-guided chunking strategy for PDF documents,
designed to create semantically meaningful chunks based on the visual and
structural layout of the document.
"""

import logging
import re
import time
from typing import Dict, List, Any

import pdfplumber
from pydantic import BaseModel, Field

from google.genai import types
from utils.clients import get_gemini_client

# Configure logging
logger = logging.getLogger(__name__)

# --- Pydantic Schemas for Structured Output ---

class DocumentSection(BaseModel):
    """A section of the document identified by a heading."""
    heading: str = Field(description="The main heading of this section.")
    start_page: int = Field(description="The page number where this section begins (1-indexed).")
    end_page: int = Field(description="The page number where this section ends (1-indexed).")

class DocumentStructure(BaseModel):
    """The overall structure of the document, composed of sections."""
    sections: List[DocumentSection] = Field(description="A list of all primary sections in the document.")

# --- Main Chunking Logic ---

def extract_case_reference(pdf_path: str) -> str:
    """
    Extract the case reference from the PDF filename or first page.
    
    Args:
        pdf_path: The path to the PDF file.
        
    Returns:
        A string containing the case reference.
    """
    # Try to get from filename first
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

def get_document_structure(uploaded_file: types.File) -> DocumentStructure:
    """
    Uses Gemini 2.5 Pro to analyze the PDF and extract its structure.
    
    Args:
        uploaded_file: The uploaded file object from the Gemini API.
        
    Returns:
        A DocumentStructure object detailing the sections of the PDF.
    """
    gemini_client = get_gemini_client()
    logger.info(f"Analyzing document structure with Gemini 2.5 Pro for file: {uploaded_file.name}")

    system_prompt = """
    You are an expert document analysis AI. Your task is to analyze the provided
    PDF and identify its primary sections based on the main headings. You must
    determine the starting and ending page number for each section.

    - Identify only the main content sections.
    - Do not include the table of contents, index, or appendices.
    - Page numbers must be 1-indexed.
    - Ensure the end_page is greater than or equal to the start_page.
    """
    user_prompt = "Please analyze this document and return its structure in the requested JSON format."

    response = gemini_client.models.generate_content(
        model='gemini-2.5-pro',
        contents=[user_prompt, uploaded_file],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=DocumentStructure,
            system_instruction=system_prompt,
        ),
    )
    
    logger.info("Successfully extracted document structure from Gemini.")
    return DocumentStructure.model_validate_json(response.text)


def chunk_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Creates vision-guided, semantically relevant chunks from a PDF.
    
    This function uses Gemini 2.5 Pro to analyze the document's structure and then
    creates chunks based on the identified sections. Each chunk corresponds to a
    full section and includes the text from all pages that the section spans.
    
    Args:
        pdf_path: The path to the PDF file.
        
    Returns:
        A list of dictionaries, where each dictionary represents a text chunk with metadata.
    """
    case_ref = extract_case_reference(pdf_path)
    logger.info(f"Starting vision-guided chunking for case: {case_ref}")
    
    gemini_client = get_gemini_client()
    uploaded_file = None
    
    try:
        # 1. Upload the file to the Gemini API
        logger.info(f"Uploading {pdf_path} to the Gemini API...")
        uploaded_file = gemini_client.files.upload(file=pdf_path)
        logger.info(f"File uploaded successfully: {uploaded_file.name}")

        # 2. Get the document's structure from Gemini
        doc_structure = get_document_structure(uploaded_file)
        logger.info(f"Identified {len(doc_structure.sections)} sections in the document.")

        # 3. Extract text and create chunks based on the structure
        chunks = []
        with pdfplumber.open(pdf_path) as pdf:
            for i, section in enumerate(doc_structure.sections):
                start_page = section.start_page
                end_page = section.end_page
                
                if start_page > len(pdf.pages) or end_page > len(pdf.pages) or start_page > end_page:
                    logger.warning(f"Skipping invalid section '{section.heading}' with pages {start_page}-{end_page}.")
                    continue

                # Collect all text from the pages the section spans
                section_text = ""
                page_numbers = list(range(start_page, end_page + 1))
                for page_num in page_numbers:
                    # pdfplumber pages are 0-indexed
                    page_text = pdf.pages[page_num - 1].extract_text()
                    if page_text:
                        section_text += page_text + "\n\n"
                
                if not section_text.strip():
                    logger.warning(f"No text extracted for section '{section.heading}' on pages {page_numbers}.")
                    continue

                chunks.append({
                    "text": section_text.strip(),
                    "metadata": {
                        "case_reference": case_ref.replace('/', '-'),
                        "section": section.heading,
                        "pages": page_numbers,
                        "chunk_sequence": i,
                        "chunk_type": "vision_guided_section"
                    }
                })
        
        logger.info(f"Created {len(chunks)} vision-guided chunks for case {case_ref}")
        return chunks

    except Exception as e:
        logger.error(f"Vision-guided chunking pipeline failed for {pdf_path}: {e}", exc_info=True)
        raise
    finally:
        # Clean up the uploaded file from the Gemini API
        if uploaded_file:
            logger.info(f"Deleting uploaded file from Gemini: {uploaded_file.name}")
            gemini_client.files.delete(name=uploaded_file.name)
            logger.info("Uploaded file deleted.")