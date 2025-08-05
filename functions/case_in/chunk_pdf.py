"""
Heading-Aware Chunking for PDF Documents.

This module implements a heading-aware chunking strategy for PDF documents,
designed to create semantically meaningful chunks based on document structure.
"""

import logging
import re
import time
from typing import Dict, List, Any

import pdfplumber

from utils.clients import get_gemini_client

# Configure logging
logger = logging.getLogger(__name__)

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

def chunk_pdf(pdf_path: str) -> (List[Dict[str, Any]]):
    """
    Creates contextually relevant chunks from a PDF based on document headings.
    
    This function extracts text from a PDF, identifies section headings, and creates
    logical chunks based on the document's structure. This produces more semantically
    meaningful chunks compared to a simple word-count approach.
    
    Args:
        pdf_path: The path to the PDF file.
        
    Returns:
        A tuple containing:
        - A list of dictionaries, where each dictionary represents a text chunk with metadata.
        - The case reference string.
    """
    case_ref = extract_case_reference(pdf_path)
    logger.info(f"Creating heading-aware chunks for case: {case_ref}")
    
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
    
    full_text = ""
    section_markers = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            current_position = 0
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if not page_text:
                    continue
                
                lines = page_text.split('\n')
                for line_num, line in enumerate(lines):
                    clean_line = line.strip()
                    for heading_pattern in COMMON_HEADINGS:
                        if re.search(heading_pattern, clean_line, re.IGNORECASE):
                            position = current_position + len('\n'.join(lines[:line_num]))
                            section_markers.append({
                                "heading": clean_line,
                                "position": position,
                                "page": page_num + 1
                            })
                            break
                
                full_text += page_text + "\n"
                current_position += len(page_text) + 1
                
            logger.info(f"Found {len(section_markers)} section headings in document")
    
    except Exception as e:
        logger.error(f"Failed to extract sections from PDF {pdf_path}: {e}")
        raise
    
    if not section_markers:
        err_msg = f"No section headings found in {pdf_path}. Cannot perform heading-aware chunking."
        logger.error(err_msg)
        raise ValueError(err_msg)
    
    section_markers.sort(key=lambda x: x["position"])
    
    section_markers.append({
        "heading": "END_OF_DOCUMENT",
        "position": len(full_text),
        "page": -1
    })
    
    chunks = []
    for i in range(len(section_markers) - 1):
        start_pos = section_markers[i]["position"]
        end_pos = section_markers[i+1]["position"]
        
        section_text = full_text[start_pos:end_pos].strip()
        if not section_text:
            continue
            
        chunks.append({
            "text": section_text,
            "metadata": {
                "case_reference": case_ref.replace('/', '-'),
                "section": section_markers[i]["heading"],
                "page": section_markers[i]["page"],
                "chunk_sequence": len(chunks),
                "chunk_type": "section"
            }
        })
    
    logger.info(f"Created {len(chunks)} section-based chunks for case {case_ref}")
    return chunks, case_ref