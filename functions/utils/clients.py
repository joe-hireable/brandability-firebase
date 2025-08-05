"""
Client initialization utilities for Firebase and Gemini APIs.

This module provides lazy initialization of clients for Firebase and Gemini APIs,
ensuring they are properly configured and reused across the application.
"""

import logging
import firebase_admin
from firebase_admin import firestore
from google import genai

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