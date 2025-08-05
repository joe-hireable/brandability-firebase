"""
Shared utilities for the Trademark Case Ingestion system.

This module provides common functionality used across different modules in the system,
including client initialization, prompt loading, and helper functions.
"""

import logging
import firebase_admin
from firebase_admin import firestore, storage
from google import genai
from pathlib import Path
from typing import Dict, Any

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