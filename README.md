# Brandability AI - Trademark Intelligence System  

Brandability is an AI/ML-driven application that provides decision intelligence to UK/EU trademark lawyers. The system maintains a database (Firestore) of past case decisions in PDF format used for semantic and natural language search, retrieval-augmented generation (RAG). These cases are also parsed to extract structured data that will be used by machine learning models to predict the outcomes of future cases (based on real results of past case decisions) and inform similarity analyses. 

Users (trademark lawyers) will be able to predict outcomes of pending cases, assess similarity between goods/services based on their term/name and NICE Class, assess similarity between competing wordmarks, prepare and brainstorm legal arguments, find precedent or similar cases and more. Ultimately enabling them to manage their caseloads more effectively, win more arguments and better represent their clients.

## Tech Stack
Core Infrastructure: Firebase, Firestore, Google Cloud Platform
Frontend: React, Typescript, Tailwind, Vite, Node
Functions: Python, Firebase Functions
AI: Vertex AI, google-genai, Gemini 2.5 Pro (`gemini-2.5-pro`)

## Environment Variables
### Gemini API Key
GEMINI_API_KEY=your-api-key

### Emulators
FIRESTORE_EMULATOR_HOST=localhost:8080
FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
FIREBASE_STORAGE_EMULATOR_HOST=localhost:9199

### Google Cloud and Firebase Config
GOOGLE_CLOUD_PROJECT=trademark-prediction-system
FIREBASE_PROJECT_ID=trademark-prediction-system
VERTEXAI_LOCATION=europe-west2
GOOGLE_CLOUD_LOCATION=europe-west2
PYTHONPATH=.
LOG_LEVEL=INFO

## Functions

The core logic of the application is handled by a set of backend functions, primarily focused on case ingestion, data processing, and AI-driven analysis.

### 1. Case Ingestion Pipeline (`case_in/`)

This module orchestrates the entire case ingestion pipeline, triggered when a new PDF case document is uploaded to a Cloud Storage bucket. It ensures each document is processed, analyzed, and stored for retrieval and predictive modeling.

-   **`case_in.py` (Orchestrator)**: Manages the end-to-end pipeline:
    1.  **Downloads** the PDF from Cloud Storage.
    2.  **Coordinates** the chunking, data extraction, and embedding generation steps.
    3.  **Sets up** the Vertex AI Vector Search index and endpoint if they don't exist.
    4.  **Upserts** the generated embeddings into the Vector Search index.
    5.  **Stores** the structured data and text chunks in Firestore.

-   **`chunk_pdf.py` (Vision-Guided Chunking)**:
    -   Uses Gemini 2.5 Pro to analyse the visual and structural layout of the PDF.
    -   Identifies primary sections (e.g., "Background", "Decision", "Legal Framework") and their page ranges.
    -   Creates semantically meaningful chunks based on these sections, preserving the document's original context.

-   **`generate_embeddings.py` (Embedding Generation)**:
    -   Generates vector embeddings for each text chunk using the `models/embedding-001` model.
    -   Includes retry logic to handle transient API errors.

-   **`extract_predictive_data.py` (Parallelised Data Extraction)**:
    -   Extracts structured data from the PDF using Gemini 2.5 Pro with a schema-enforced (`Pydantic`) model.
    -   Employs a multi-pass, parallel extraction strategy by running multiple API calls simultaneously in a single batch job.
    -   Consolidates the results by selecting the most common value for each field, ensuring high accuracy and resilience to occasional extraction errors.

### 2. Similarity and Prediction Functions (`case_prediction/`)

These functions are used directly by users or as components in the overall case prediction model.

-   **`gs_similarity`**: Uses Gemini 2.5 Pro to assess similarity between competing goods/services based on their terms, NICE classifications, and optional descriptions.
-   **`mark_similarity`**: Assesses the overall similarity of two wordmarks by combining visual, aural, and conceptual scores.
-   **`mark_visual_similarity`**: Assesses visual similarity using Levenshtein distance.
-   **`mark_aural_similarity`**: Assesses aural similarity using phonetic algorithms like Metaphone/Double Metaphone.
-   **`mark_conceptual_similarity`**: Assesses conceptual similarity using Gemini 2.5 Pro.
-   **`case_prediction`**: Predicts the `likelihood_of_confusion` and `confusion_type` for a case. It generates explainable `reasoning` and `arguments` based on the combined results from `mark_similarity` and `gs_similarity`.