#!/usr/bin/env python3
"""
Comprehensive integration tests for case_in.py using Firebase emulators and real Gemini calls.

This test suite validates:
1. PDF processing with real Gemini API calls
2. Firestore integration with emulators
3. Data extraction accuracy for trademark cases
4. Vector search preparation with embeddings
"""

import os
import sys
import json
import tempfile
import pytest
import logging
from unittest.mock import patch, MagicMock
from pathlib import Path
import shutil
from datetime import datetime
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import firestore, storage

# Add functions directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the module to test
from case_in import (
    extract_structured_data,
    extract_full_text_from_pdf,
    create_heading_aware_chunks,
    generate_embeddings,
    store_data_in_firestore,
    process_case_from_storage,
    extract_case_reference
)

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Pytest Fixtures ---

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Initializes the test environment once per session.
    - Loads environment variables from .env.test file.
    - Configures and initializes Firebase Admin SDK to use emulators.
    """
    # Load environment variables from .env.test file
    load_dotenv(dotenv_path=Path(__file__).parent / '.env.test')

    # Configure emulators
    os.environ['FIRESTORE_EMULATOR_HOST'] = "localhost:8080"
    os.environ['FIREBASE_AUTH_EMULATOR_HOST'] = "localhost:9099"
    os.environ['FIREBASE_STORAGE_EMULATOR_HOST'] = "localhost:9199"
    
    # Initialize Firebase Admin SDK if not already initialized
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
        logger.info("Firebase Admin SDK initialized for testing.")
    
    yield
    # Teardown can go here if needed
    logger.info("Test session finished.")


# --- Test Configuration ---
TEST_PROJECT_ID = "trademark-prediction-system"
TEST_BUCKET = f"{TEST_PROJECT_ID}.appspot.com"

# Test PDF files (paths relative to the 'functions' directory)
PDF_BASE_PATH = Path(__file__).parent.parent / "data" / "case_pdfs"
TEST_PDF_FILES = [
    str(PDF_BASE_PATH / "Barking Brains LTD.pdf"),
    str(PDF_BASE_PATH / "Bug Off.pdf"),
    str(PDF_BASE_PATH / "CM Games.pdf"),
    str(PDF_BASE_PATH / "DREAM RITE.pdf"),
    str(PDF_BASE_PATH / "JOLLY PECKISH.pdf")
]

class TestCaseInIntegration:
    """Integration tests for case_in.py with real Gemini calls and Firestore emulators."""
    
    def test_extract_case_reference_from_filename(self):
        """Test case reference extraction from filename and PDF content."""
        test_cases = [
            (str(PDF_BASE_PATH / "Barking Brains LTD.pdf"), "O/0060/24"),
            (str(PDF_BASE_PATH / "Bug Off.pdf"), "O/0950/24"),
            (str(PDF_BASE_PATH / "CM Games.pdf"), "O/0958/24"),
            (str(PDF_BASE_PATH / "DREAM RITE.pdf"), "O/0702/24"),
            (str(PDF_BASE_PATH / "JOLLY PECKISH.pdf"), "O/0703/24")
        ]

        for pdf_path, expected_ref in test_cases:
            if not os.path.exists(pdf_path):
                pytest.skip(f"Test PDF not found: {pdf_path}")

            ref = extract_case_reference(pdf_path)
            assert ref == expected_ref, f"For file {pdf_path}, expected {expected_ref}, but got {ref}"
    
    def test_extract_full_text_from_pdf(self):
        """Test full text extraction from PDF files."""
        for pdf_file in TEST_PDF_FILES:
            if os.path.exists(pdf_file):
                logger.info(f"Testing full text extraction from {pdf_file}")
                full_text = extract_full_text_from_pdf(pdf_file)
                
                # Basic validation
                assert isinstance(full_text, str)
                assert len(full_text) > 100  # Should have substantial content
                assert "TRADE MARKS ACT" in full_text.upper() or "TRADE MARK" in full_text.upper()
    
    def test_create_heading_aware_chunks(self):
        """Test heading-aware chunking for PDFs."""
        for pdf_file in TEST_PDF_FILES:
            if os.path.exists(pdf_file):
                logger.info(f"Testing chunking for {pdf_file}")
                case_ref = extract_case_reference(os.path.basename(pdf_file))
                chunks = create_heading_aware_chunks(pdf_file, case_ref)
                
                # Validation
                assert isinstance(chunks, list)
                assert len(chunks) > 0
                
                for chunk in chunks:
                    assert "text" in chunk
                    assert "metadata" in chunk
                    assert chunk["metadata"]["case_reference"] == case_ref
    
    def test_extract_structured_data_real_gemini(self):
        """Test structured data extraction with real Gemini API."""
        # Skip if no API key
        if not os.getenv("GEMINI_API_KEY"):
            pytest.skip("GEMINI_API_KEY not set")
        
        for pdf_file in TEST_PDF_FILES:
            if os.path.exists(pdf_file):
                logger.info(f"Testing structured extraction from {pdf_file}")
                
                try:
                    case_obj = extract_structured_data(pdf_file)
                    
                    # Validate structure
                    assert hasattr(case_obj, 'case_reference')
                    assert hasattr(case_obj, 'applicant_name')
                    assert hasattr(case_obj, 'opponent_name')
                    assert hasattr(case_obj, 'opposition_outcome')
                    
                    # Basic validation
                    assert case_obj.case_reference
                    assert case_obj.applicant_name or case_obj.opponent_name
                    
                    logger.info(f"Successfully extracted: {case_obj.case_reference}")
                    
                except Exception as e:
                    logger.error(f"Failed to extract from {pdf_file}: {e}")
                    raise
    
    def test_generate_embeddings(self):
        """Test embedding generation for chunks."""
        # Skip if no API key
        if not os.getenv("GEMINI_API_KEY"):
            pytest.skip("GEMINI_API_KEY not set")
        
        for pdf_file in TEST_PDF_FILES:
            if os.path.exists(pdf_file):
                logger.info(f"Testing embeddings for {pdf_file}")
                
                case_ref = extract_case_reference(os.path.basename(pdf_file))
                chunks = create_heading_aware_chunks(pdf_file, case_ref)
                
                if chunks:
                    embeddings = generate_embeddings(chunks)
                    
                    # Validation
                    assert isinstance(embeddings, list)
                    assert len(embeddings) == len(chunks)
                    
                    for embedding in embeddings:
                        assert isinstance(embedding, list)
                        assert len(embedding) > 0  # Should have vector dimensions
    
    def test_firestore_integration(self):
        """Test Firestore integration with emulators."""
        # Skip if no API key
        if not os.getenv("GEMINI_API_KEY"):
            pytest.skip("GEMINI_API_KEY not set")
        
        from models import Case
        
        db = firestore.client()
        
        # Test with first available PDF
        for pdf_file in TEST_PDF_FILES:
            if os.path.exists(pdf_file):
                logger.info(f"Testing Firestore integration with {pdf_file}")
                
                case_obj = extract_structured_data(pdf_file)
                case_ref = case_obj.case_reference
                chunks = create_heading_aware_chunks(pdf_file, case_ref)
                embeddings = generate_embeddings(chunks)
                
                # Store data
                store_data_in_firestore(case_obj, chunks, embeddings)
                
                # Verify storage
                doc_ref = db.collection("cases").document(case_ref)
                doc = doc_ref.get()
                
                assert doc.exists, f"Document {case_ref} not found in Firestore"
                
                # Verify chunks
                chunks_ref = doc_ref.collection("chunks")
                chunks_docs = list(chunks_ref.stream())
                
                assert len(chunks_docs) > 0, "No chunks found in Firestore"
                assert len(chunks_docs) == len(chunks), "Chunk count mismatch"
                
                logger.info(f"Successfully stored {case_ref} with {len(chunks)} chunks")
                break
    
    def test_complete_pipeline(self):
        """Test complete pipeline with all PDFs."""
        # Skip if no API key
        if not os.getenv("GEMINI_API_KEY"):
            pytest.skip("GEMINI_API_KEY not set")
        
        results = []
        
        for pdf_file in TEST_PDF_FILES:
            if os.path.exists(pdf_file):
                logger.info(f"Testing complete pipeline for {pdf_file}")
                
                try:
                    # Full pipeline
                    case_obj = extract_structured_data(pdf_file)
                    case_ref = case_obj.case_reference
                    chunks = create_heading_aware_chunks(pdf_file, case_ref)
                    embeddings = generate_embeddings(chunks)
                    store_data_in_firestore(case_obj, chunks, embeddings)
                    
                    results.append({
                        "file": pdf_file,
                        "case_reference": case_ref,
                        "chunks": len(chunks),
                        "success": True
                    })
                    
                except Exception as e:
                    results.append({
                        "file": pdf_file,
                        "error": str(e),
                        "success": False
                    })
        
        # Assert all succeeded
        failures = [r for r in results if not r["success"]]
        if failures:
            logger.error(f"Pipeline failures: {failures}")
            pytest.fail(f"Pipeline failed for {len(failures)} files")
        
        logger.info(f"Successfully processed {len(results)} PDFs")


class TestDataValidation:
    """Validation tests for extracted data accuracy."""
    
    def test_barking_brains_extraction(self):
        """Validate specific data extraction for Barking Brains case."""
        pdf_path = str(PDF_BASE_PATH / "Barking Brains LTD.pdf")
        if not os.path.exists(pdf_path):
            pytest.skip("Test PDF not found")
        
        if not os.getenv("GEMINI_API_KEY"):
            pytest.skip("GEMINI_API_KEY not set")
        
        case_obj = extract_structured_data(pdf_path)
        
        # Validate specific fields
        assert case_obj.case_reference == "O/0060/24"
        assert "barking brains ltd" in str(case_obj.applicant_name).lower()
        assert "pet food (uk) ltd" in str(case_obj.opponent_name).lower()
        assert case_obj.opposition_outcome is not None
    
    def test_bug_off_extraction(self):
        """Validate specific data extraction for Bug Off case."""
        pdf_path = str(PDF_BASE_PATH / "Bug Off.pdf")
        if not os.path.exists(pdf_path):
            pytest.skip("Test PDF not found")
        
        if not os.getenv("GEMINI_API_KEY"):
            pytest.skip("GEMINI_API_KEY not set")
        
        case_obj = extract_structured_data(pdf_path)
        
        # Validate specific fields
        assert case_obj.case_reference == "O/0950/24"
        assert "lakeland cosmetics" in str(case_obj.applicant_name).lower()
        assert "s.c. johnson & son" in str(case_obj.opponent_name).lower()
    
    def test_cm_games_extraction(self):
        """Validate specific data extraction for CM Games case."""
        pdf_path = str(PDF_BASE_PATH / "CM Games.pdf")
        if not os.path.exists(pdf_path):
            pytest.skip("Test PDF not found")
        
        if not os.getenv("GEMINI_API_KEY"):
            pytest.skip("GEMINI_API_KEY not set")
        
        case_obj = extract_structured_data(pdf_path)
        
        # Validate specific fields
        assert case_obj.case_reference == "O/0958/24"
        assert "creative mobile" in str(case_obj.applicant_name).lower()
        assert "cheetah mobile" in str(case_obj.opponent_name).lower()


@pytest.fixture(scope="session")
def firestore_emulator():
    """Ensure Firestore emulator is running."""
    # This would typically be handled by the Firebase CLI
    # For now, we'll assume emulators are started externally
    return True


@pytest.mark.integration
class TestIntegration:
    """Full integration tests."""
    
    def test_all_pdfs_integration(self, firestore_emulator):
        """Test processing all PDFs with real services."""
        test_instance = TestCaseInIntegration()
        test_instance.test_complete_pipeline()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])