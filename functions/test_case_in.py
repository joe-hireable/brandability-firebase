import os
import random
import sys
import firebase_admin
from firebase_admin import credentials, storage

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from functions.case_in.case_in import process_case_from_storage

# Load environment variables from .env.test
with open('functions/.env.test', 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key.strip()] = value.strip()

# Initialize Firebase Admin SDK
# The Admin SDK automatically detects the FIREBASE_STORAGE_EMULATOR_HOST env var
cred = credentials.ApplicationDefault()
project_id = os.getenv('FIREBASE_PROJECT_ID')
if not project_id:
    raise ValueError("FIREBASE_PROJECT_ID environment variable not set.")

if not os.getenv('FIREBASE_STORAGE_EMULATOR_HOST'):
    raise ValueError("FIREBASE_STORAGE_EMULATOR_HOST is not set. Is the emulator running?")

firebase_admin.initialize_app(cred, {
    'projectId': project_id,
    'storageBucket': f"{project_id}.appspot.com"
})

# --- Test Configuration ---
PDF_DIRECTORY = 'data/case_pdfs/'
# Get a list of all PDF files in the directory
pdf_files = [f for f in os.listdir(PDF_DIRECTORY) if f.endswith('.pdf')]
if not pdf_files:
    raise FileNotFoundError(f"No PDF files found in {PDF_DIRECTORY}")

# Select a random PDF for the test
TEST_PDF_FILE = random.choice(pdf_files)
TEST_PDF_FILE_PATH = os.path.join(PDF_DIRECTORY, TEST_PDF_FILE)

BUCKET_NAME = os.getenv('FIREBASE_PROJECT_ID') + '.firebasestorage.app'
# The destination path in the bucket
DESTINATION_BLOB_NAME = 'cases/' + TEST_PDF_FILE

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    bucket = storage.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print(f"File {source_file_name} uploaded to {destination_blob_name}.")

def run_test():
    """
    Runs the end-to-end test for the case ingestion pipeline.
    """
    print("--- Starting Case Ingestion Test ---")
    print(f"Using random PDF: {TEST_PDF_FILE_PATH}")
    
    # 1. Upload the test PDF to the bucket to trigger the function
    print(f"Uploading {TEST_PDF_FILE_PATH} to gs://{BUCKET_NAME}/{DESTINATION_BLOB_NAME}")
    upload_to_gcs(BUCKET_NAME, TEST_PDF_FILE_PATH, DESTINATION_BLOB_NAME)
    
    # 2. Manually trigger the processing logic for testing purposes
    # In a real scenario, the Cloud Function would be triggered automatically.
    print("\n--- Manually Triggering processing_case_from_storage ---")
    try:
        process_case_from_storage(BUCKET_NAME, DESTINATION_BLOB_NAME)
        print("\n--- Test Completed Successfully ---")
    except Exception as e:
        print(f"\n--- Test Failed: {e} ---")

if __name__ == "__main__":
    # Note: Ensure you are authenticated with GCP and have the necessary
    # environment variables set (e.g., GOOGLE_CLOUD_PROJECT).
    # You can authenticate via the CLI: `gcloud auth application-default login`
    run_test()