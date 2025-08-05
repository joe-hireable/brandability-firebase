# Brandability AI - Trademark Intelligence System  

Brandability is an AI/ML-driven application that provides decision intelligence to UK/EU trademark lawyers. The system maintains a database (Firestore) of past case decisions in PDF format used for semantic and natural language search, retrieval-augmented generation (RAG). These cases are also parsed to extract structured data that will be used by machine learning models to predict the outcomes of future cases (based on real results of past case decisions) and inform similarity analyses. 

Users (trademark lawyers) will be able to predict outcomes of pending cases, assess similarity between goods/services based on their term/name and NICE Class, assess similarity between competing wordmarks, prepare and brainstorm legal arguments, find precedent or similar cases and more. Ultimately enabling them to manage their caseloads more effectively, win more arguments and better represent their clients.

## Tech Stack
Core Infrastructure: Firebase, Firestore, Google Cloud Platform
Frontend: React, Typescript, Tailwind, Vite, Node
Functions: Python, Firebase Functions
AI: Vertex AI, google-genai, Gemini 2.5 Pro (`gemini-2.5-pro`)

## Environment Variables
GEMINI_API_KEY=your-api-key
FIRESTORE_EMULATOR_HOST=localhost:8080
FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
FIREBASE_STORAGE_EMULATOR_HOST=localhost:9199
GOOGLE_CLOUD_PROJECT=trademark-prediction-system
FIREBASE_PROJECT_ID=trademark-prediction-system
PYTHONPATH=.
LOG_LEVEL=INFO

## Functions
1. `case_in`: triggered by new PDF going into bucket, triggers `chunk_pdf`, `generate_embeddings`, `extract_predictive_data` https://firebase.google.com/docs/functions/custom-events.
2. `chunk_pdf`: context-aware chunking of PDF cases using vision-guided chunking (used by `case_in` function). Docs - https://arxiv.org/html/2506.16035v1.
3. `generate_embeddings`: generates embeddings for PDF chunks and stores in firestore (used by `case_in` function).
4. `extract_predictive_data`: uses gemini-2.5-pro to extract predictive data from cases (used by `case_in` function) and store in our predictive dataset.
2. `gs_similarity`: uses gemini-2.5-pro to assess similarity between competing goods/services based on good/service terms, NICE classifications and optional descriptions (used directly by users and by the `case_prediction` function).
3. `mark_similarity`: assess overall similarity of marks based on `mark_visual_similarity`, `mark_aural_similarity` and `mark_conceptual_similarity`, returns overall similarity score and individual visual, aural and conceptual scores (used by the `case_prediction` function).
4. `mark_visual_similarity`: assesses the visual similarity of wordmarks (case sensitive) using levenstein distance (used by the `mark_similarity` function).
5. `mark_aural_similarity`: assesses aural similarity of wordmarks using metaphone/double metaphone or similar (used by the `mark_similarity` function).
6. `mark_conceptual_similarity`: assesses conceptual similarity of wordmarks using gemini-2.5-pro (used by the `mark_similarity` function).
7. `case_prediction`: predicts `likelihood_of_confusion` and `confusion_type` between 2 competing wordmarks with explainable `reasoning` and `arguments` based on `mark_similarity` results and list of `gs_similarity` results.