import os
import random
import sys
import logging
import json
import firebase_admin
from firebase_admin import credentials, storage
from google.cloud import aiplatform

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from functions.case_in.case_in import process_case_from_storage, INDEX_DISPLAY_NAME

# Custom JSON formatter for file logging
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)
        
        # Add full Gemini response if it exists in the log record
        if hasattr(record, 'gemini_response'):
            log_record['gemini_response'] = record.gemini_response

        return json.dumps(log_record)

# --- Logging Configuration ---
log_file_path = 'test_logs.json'

# Clear existing handlers to prevent duplicate logging
if logging.root.handlers:
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

# 1. Console Handler (for human-readable output)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# 2. File Handler (for JSON output, overwrites file on each run)
file_handler = logging.FileHandler(log_file_path, mode='w')
file_handler.setFormatter(JsonFormatter())

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        console_handler,
        file_handler
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env.test
with open('functions/.env.test', 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key.strip()] = value.strip()

# --- GCP & Firebase Configuration ---
# This is now an INTEGRATION TEST that uses live GCP services.
# Ensure you have authenticated with 'gcloud auth application-default login'
# and that the required environment variables are set in .env.test

cred = credentials.ApplicationDefault()
GCP_PROJECT = os.getenv('GCP_PROJECT')
GCS_BUCKET = os.getenv('GCS_BUCKET')

if not GCP_PROJECT:
    raise ValueError("GCP_PROJECT environment variable not set.")
if not GCS_BUCKET:
    raise ValueError("GCS_BUCKET environment variable not set. This test requires a real GCS bucket.")

# Initialize Firebase Admin SDK to interact with GCS
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        'projectId': GCP_PROJECT,
        'storageBucket': GCS_BUCKET
    })

# --- Test File Selection ---
PDF_DIRECTORY = 'data/case_pdfs/'
pdf_files = [f for f in os.listdir(PDF_DIRECTORY) if f.endswith('.pdf')]
if not pdf_files:
    raise FileNotFoundError(f"No PDF files found in {PDF_DIRECTORY}")

# Select a random PDF for the test
TEST_PDF_FILE = random.choice(pdf_files)
TEST_PDF_FILE_PATH = os.path.join(PDF_DIRECTORY, TEST_PDF_FILE)

# Use the real GCS bucket name
BUCKET_NAME = GCS_BUCKET
# The destination path in the bucket
DESTINATION_BLOB_NAME = f'test_cases/{TEST_PDF_FILE}'

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    bucket = storage.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    logger.info(f"File {source_file_name} uploaded to {destination_blob_name}.")

def run_test():
    """
    Runs the end-to-end test for the case ingestion pipeline.
    """
    logger.info("--- Starting Case Ingestion Test ---")

    logger.info(f"Using random PDF: {TEST_PDF_FILE_PATH}")
    
    # 1. Upload the test PDF to the bucket to trigger the function
    logger.info(f"Uploading {TEST_PDF_FILE_PATH} to gs://{BUCKET_NAME}/{DESTINATION_BLOB_NAME}")
    upload_to_gcs(BUCKET_NAME, TEST_PDF_FILE_PATH, DESTINATION_BLOB_NAME)
    
    # 2. Manually trigger the processing logic for testing purposes
    # In a real scenario, the Cloud Function would be triggered automatically.
    logger.info("--- Manually Triggering processing_case_from_storage ---")
    try:
        process_case_from_storage(BUCKET_NAME, DESTINATION_BLOB_NAME)
        logger.info("--- Test Completed Successfully ---")
    except Exception as e:
        logger.error(f"--- Test Failed: {e} ---", exc_info=True)

if __name__ == "__main__":
    # Note: This is an integration test that interacts with live GCP services
    # (Cloud Storage, Gemini API, Vertex AI).
    # Ensure you have authenticated with GCP:
    # `gcloud auth application-default login`
    #
    # Also ensure the required environment variables are set in `functions/.env.test`:
    # - GCP_PROJECT: Your Google Cloud project ID.
    # - GCS_BUCKET: A real GCS bucket for uploads and index files.
    # - VPC_NETWORK_NAME: The name of the VPC network for the Vector Search endpoint.
    run_test()
