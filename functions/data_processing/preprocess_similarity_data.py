"""
Processes the raw EUIPO similarity data into a clean, structured format.

This script performs the following steps:
1.  Loads the raw data from the specified Excel file, using the first row as the header.
2.  Selects and renames the necessary columns for the analysis.
3.  Cleans the 'Similarity' column by stripping whitespace.
4.  Maps the textual similarity degrees (e.g., "High similar") to the
    application's standard enum values (e.g., "high_degree").
5.  Filters out rows with missing or invalid data to ensure quality.
6.  Saves the processed data to a JSONL file, which is optimal for batch
    processing with Vertex AI for embedding generation.
"""
import pandas as pd
import numpy as np
from typing import Dict
import json
import os

# Path to the raw data file provided by the user
RAW_DATA_PATH = "data/2025_08_06_Results_CFSimilarity.xls"
# Path to save the processed data, ready for Vertex AI
PROCESSED_DATA_PATH = "data/processed_similarity_data.jsonl"

# Mapping from spreadsheet values to the standard SimilarityDegree enum
SIMILARITY_MAP: Dict[str, str] = {
    "Identical": "identical",
    "High similar": "high_degree",
    "Similar": "medium_degree",
    "Low similar": "low_degree",
    "Dissimilar": "dissimilar",
}

def preprocess_data():
    """
    Loads, cleans, and structures the raw similarity data from the Excel file.
    """
    print(f"Starting preprocessing of {RAW_DATA_PATH}...")

    try:
        # 1. Load data, using the first row as the header
        df = pd.read_excel(RAW_DATA_PATH, engine='xlrd', header=0)
    except FileNotFoundError:
        print(f"ERROR: The file was not found at {RAW_DATA_PATH}")
        return
    except Exception as e:
        print(f"An error occurred while reading the Excel file: {e}")
        return

    # 2. Select and rename the necessary columns based on the inspection
    column_map = {
        "Office": "office",
        "Class 1": "class_1",
        "Term 1": "term_1",
        "Similarity": "similarity",
        "Class 2": "class_2",
        "Term 2": "term_2",
    }
    df = df[list(column_map.keys())].rename(columns=column_map)

    # 3. Drop rows with missing terms, which are essential for comparison
    df.dropna(subset=["term_1", "term_2", "similarity"], inplace=True)

    # 4. Clean and map the textual similarity degrees
    df["similarity"] = df["similarity"].str.strip()
    df["similarity_degree"] = df["similarity"].map(SIMILARITY_MAP)

    unmapped_count = df["similarity_degree"].isnull().sum()
    if unmapped_count > 0:
        print(f"Warning: {unmapped_count} rows had unmapped similarity values and will be dropped.")
        df.dropna(subset=["similarity_degree"], inplace=True)

    # 5. Prepare the final dataset for JSONL export
    df["comparison_id"] = [f"comp_{i}" for i in range(len(df))]
    output_df = df[[
        "comparison_id", "class_1", "term_1", "class_2", "term_2", "similarity_degree"
    ]].copy()

    # 6. Save the processed data to a JSONL file
    os.makedirs(os.path.dirname(PROCESSED_DATA_PATH), exist_ok=True)
    with open(PROCESSED_DATA_PATH, "w") as f:
        for record in output_df.to_dict(orient="records"):
            json.dump(record, f)
            f.write("\n")

    print(f"Successfully preprocessed {len(output_df)} records.")
    print(f"Cleaned data saved to {PROCESSED_DATA_PATH}")


if __name__ == "__main__":
    preprocess_data()