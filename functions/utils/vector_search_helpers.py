"""
Vertex AI Vector Search Helpers.

This module provides helper functions for interacting with Google Cloud's
Vertex AI Vector Search (formerly Matching Engine). It handles the creation,
deployment, and upserting of data to a vector search index.
"""

import logging
import os
from typing import List, Optional

from google.cloud import aiplatform
from google.cloud.aiplatform_v1.types import IndexDatapoint

# Configure logging
logger = logging.getLogger(__name__)

# --- Environment and Configuration ---

PROJECT_ID = os.getenv("GCP_PROJECT")
REGION = os.getenv("GCP_REGION", "europe-west2")
VPC_NETWORK_NAME = os.getenv("VPC_NETWORK_NAME") # e.g. "uca-vpc"

# Initialize the AI Platform client
aiplatform.init(project=PROJECT_ID, location=REGION)

# --- Index and Endpoint Management ---

def get_or_create_vector_search_index(
    index_name: str,
    index_display_name: str,
    contents_delta_uri: str,
    dimensions: int
) -> aiplatform.MatchingEngineIndex:
    """
    Retrieves an existing Vector Search index or creates a new one if it doesn't exist.

    Args:
        index_name: The unique name of the index.
        index_display_name: The human-readable display name for the index.
        contents_delta_uri: GCS URI where the index data will be stored.
        dimensions: The number of dimensions of the embedding vectors.

    Returns:
        An aiplatform.MatchingEngineIndex object.
    """
    try:
        # Check if the index already exists
        indexes = aiplatform.MatchingEngineIndex.list(
            filter=f'display_name="{index_display_name}"'
        )
        if indexes:
            index = indexes[0]
            logger.info(f"Found existing Vector Search index: {index.resource_name}")
            return index
        
        # If not, create a new one
        logger.info(f"No existing index found. Creating new index: {index_display_name}")
        index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
            display_name=index_display_name,
            contents_delta_uri=contents_delta_uri,
            dimensions=dimensions,
            approximate_neighbors_count=150,
            distance_measure_type="DOT_PRODUCT_DISTANCE",
            leaf_node_embedding_count=500,
            leaf_nodes_to_search_percent=80,
            description="Vector search index for trademark case law.",
            index_update_method="STREAM_UPDATE",
        )
        logger.info(f"Successfully created Vector Search index: {index.resource_name}")
        return index

    except Exception as e:
        logger.error(f"Failed to get or create Vector Search index: {e}", exc_info=True)
        raise


def get_or_create_index_endpoint(
    endpoint_display_name: str,
) -> aiplatform.MatchingEngineIndexEndpoint:
    """
    Retrieves an existing index endpoint or creates one if it doesn't exist.

    Args:
        endpoint_display_name: The human-readable display name for the endpoint.

    Returns:
        An aiplatform.MatchingEngineIndexEndpoint object.
    """
    try:
        # Check if the endpoint already exists
        endpoints = aiplatform.MatchingEngineIndexEndpoint.list(
            filter=f'display_name="{endpoint_display_name}"'
        )
        if endpoints:
            endpoint = endpoints[0]
            logger.info(f"Found existing index endpoint: {endpoint.resource_name}")
            return endpoint

        # If not, create a new one
        logger.info(f"No existing endpoint found. Creating new endpoint: {endpoint_display_name}")
        endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
            display_name=endpoint_display_name,
            public_endpoint_enabled=True,
            description="Endpoint for the trademark case law vector search index.",
        )
        logger.info(f"Successfully created index endpoint: {endpoint.resource_name}")
        return endpoint

    except Exception as e:
        logger.error(f"Failed to get or create index endpoint: {e}", exc_info=True)
        raise

def deploy_index_to_endpoint(
    endpoint: aiplatform.MatchingEngineIndexEndpoint,
    index: aiplatform.MatchingEngineIndex,
    deployment_id: str
):
    """
    Deploys an index to an endpoint if it's not already deployed.

    Args:
        endpoint: The endpoint to deploy the index to.
        index: The index to deploy.
        deployment_id: A unique ID for the deployment.
    """
    try:
        # Check if the index is already deployed to this endpoint
        if any(deployed_index.id == deployment_id for deployed_index in endpoint.deployed_indexes):
            logger.info(f"Index {index.display_name} is already deployed to endpoint {endpoint.display_name} with deployment ID {deployment_id}.")
            return

        logger.info(f"Deploying index {index.display_name} to endpoint {endpoint.display_name}...")
        endpoint.deploy_index(
            index=index,
            deployed_index_id=deployment_id
        )
        logger.info("Index deployed successfully.")

    except Exception as e:
        logger.error(f"Failed to deploy index to endpoint: {e}", exc_info=True)
        raise

# --- Data Upsertion ---

def upsert_embeddings_to_vector_search(
    index: aiplatform.MatchingEngineIndex,
    embedding_ids: List[str],
    embeddings: List[List[float]]
):
    """
    Upserts (inserts or updates) embeddings into the Vector Search index.

    Args:
        index: The Vector Search index object.
        embedding_ids: A list of unique string IDs for each embedding.
        embeddings: A list of embedding vectors.
    """
    if not embedding_ids or not embeddings:
        logger.warning("No embeddings or IDs provided to upsert. Skipping.")
        return
        
    if len(embedding_ids) != len(embeddings):
        raise ValueError("The number of embedding IDs must match the number of embeddings.")

    try:
        logger.info(f"Upserting {len(embeddings)} embeddings to index {index.display_name}...")
        
        # The upsert operation takes a list of IndexDatapoint objects.
        datapoints = [
            IndexDatapoint(datapoint_id=id, feature_vector=embedding)
            for id, embedding in zip(embedding_ids, embeddings)
        ]
        
        index.upsert_datapoints(datapoints=datapoints)
        
        logger.info("Successfully upserted embeddings to Vector Search.")
        
    except Exception as e:
        logger.error(f"Failed to upsert embeddings to Vector Search: {e}", exc_info=True)
        raise