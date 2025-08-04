"""
Cloud Functions for Firebase Entry Point.

This module initializes the Firebase Admin SDK and registers the cloud functions
that trigger the case ingestion pipeline.
"""
import logging
import os

from firebase_admin import initialize_app
from firebase_functions import options, storage_fn
from firebase_functions.storage_fn import CloudEvent, StorageObjectData

# Local application imports
import case_in

# --- Firebase and Global Configuration ---

# Set global options for all functions, e.g., region, memory, etc.
# By default, functions are deployed to us-central1.
# options.set_global_options(region="europe-west1", memory=options.MemoryOption.GB_1)

# Initialize Firebase Admin SDK.
# This is required to interact with Firebase services like Firestore and Storage.
initialize_app()

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Environment variable for the target storage bucket
# The GOOGLE_CLOUD_PROJECT environment variable is automatically set by the Cloud Functions runtime.
PDF_BUCKET = f"{os.getenv('GOOGLE_CLOUD_PROJECT')}.appspot.com"


@storage_fn.on_object_finalized(bucket=PDF_BUCKET)
def on_pdf_upload(event: CloudEvent[StorageObjectData]) -> None:
    """
    Triggers the case ingestion pipeline when a new PDF is uploaded to the
    specified Cloud Storage bucket.

    This function is configured to only trigger for files ending with '.pdf'.

    Args:
        event: The CloudEvent data containing details about the storage object.
    """
    bucket = event.data.bucket
    file_name = event.data.name

    log.info(f"Received file upload event for: {file_name} in bucket: {bucket}")

    # --- Input Validation ---
    if not file_name:
        log.error("No file name found in the event data. Aborting.")
        return

    if not file_name.lower().endswith('.pdf'):
        log.info(f"File '{file_name}' is not a PDF. Skipping processing.")
        return

    try:
        # --- Trigger Core Logic ---
        # The main processing is delegated to the `case_in` module to keep
        # this entry point clean and focused on triggering logic.
        log.info(f"Starting case ingestion pipeline for: {file_name}")
        case_in.process_case_from_storage(bucket_name=bucket, file_name=file_name)
        log.info(f"Successfully completed case ingestion for: {file_name}")

    except Exception as e:
        # The `process_case_from_storage` function has its own detailed error
        # logging. This is a final catch-all.
        log.critical(
            f"The case ingestion pipeline failed catastrophically for file '{file_name}'. "
            f"Error: {e}",
            exc_info=True
        )
        # Depending on the requirements, you might want to:
        # 1. Move the file to an 'error' folder within the bucket.
        # 2. Send a notification (e.g., via Cloud Tasks, Pub/Sub, or email).
        # 3. Re-raise the exception to mark the function execution as a failure.
        raise