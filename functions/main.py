"""
Cloud Functions for Firebase Entry Point.

This module initializes the Firebase Admin SDK and registers the cloud functions
that trigger the case ingestion pipeline.
"""
import logging
import os

from firebase_admin import initialize_app
from firebase_functions import options, storage_fn, https_fn
from firebase_functions.storage_fn import CloudEvent, StorageObjectData

# Local application imports
from case_in import case_in
from case_prediction import mark_visual_similarity

# --- Firebase and Global Configuration ---

# Set global options for all functions, e.g., region, memory, etc.
# This is to ensure the function runs in the correct region.
options.set_global_options(region="europe-west2")

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
    
    
from flask import jsonify

@https_fn.on_request(cors=options.CorsOptions(cors_origins="*", cors_methods=["get", "post"]))
def api(req: https_fn.Request) -> https_fn.Response:
    """
    API gateway for all HTTP functions.
    """
    if req.path == "/calculateVisualSimilarity":
        applicant_mark = req.get_json().get("applicant_mark")
        opponent_mark = req.get_json().get("opponent_mark")

        if not applicant_mark or not opponent_mark:
            return https_fn.Response("Missing applicant_mark or opponent_mark", status=400)

        score, degree = mark_visual_similarity.calculate_visual_similarity(
            applicant_mark, opponent_mark
        )

        return jsonify({"score": score, "degree": degree})
    
    return https_fn.Response("Not Found", status=404)