"""
HOW:
  from ingestion.clustering import cluster_embeddings, ClusterResult
  
  # Get unlabeled embeddings from PostgreSQL
  embeddings = pg_client.get_embeddings_by_run(run_id, only_unlabeled=True)
  
  # Cluster them
  result = cluster_embeddings(embeddings)
  
  # Result contains clusters mapping cluster_id -> list of segment_ids
  for cluster_id, segment_ids in result.clusters.items():
      print(f"Cluster {cluster_id}: {len(segment_ids)} segments")

  [Inputs]
  - embeddings: List of dicts with 'external_id' and 'embedding' keys
  - min_cluster_size: Minimum segments to form a cluster (default: 2)
  - min_samples: HDBSCAN min_samples parameter (default: 1)

  [Outputs]
  - ClusterResult with clusters dict and noise list

  [Side Effects]
  - None (pure computation)

WHO:
  Claude AI, User
  (Context: Phase 2 - HDBSCAN clustering for unknown segments)

WHAT:
  Clustering module for grouping unlabeled voice embeddings by speaker similarity.
  Uses HDBSCAN which:
  - Auto-detects number of clusters
  - Handles noise/outliers gracefully
  - Works well with cosine distance

WHEN:
  2025-12-09
  Last Modified: 2025-12-09

WHERE:
  apps/speaker-diarization-benchmark/ingestion/clustering.py

WHY:
  To help users efficiently label unknown segments by grouping them by voice similarity.
  Instead of labeling 175 segments individually, users can:
  1. Run clustering to discover ~5-10 speaker groups
  2. Label one segment per cluster
  3. Propagate labels to all segments in that cluster
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from collections import defaultdict

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ClusterResult:
    """Result of clustering embeddings."""
    
    # Mapping of cluster_id -> list of segment external_ids
    clusters: Dict[int, List[str]] = field(default_factory=dict)
    
    # Segment IDs that were classified as noise (no cluster)
    noise: List[str] = field(default_factory=list)
    
    # Number of embeddings processed
    total_embeddings: int = 0
    
    # Number of clusters found (excluding noise)
    num_clusters: int = 0
    
    @property
    def clustered_count(self) -> int:
        """Number of embeddings assigned to clusters."""
        return sum(len(ids) for ids in self.clusters.values())
    
    @property
    def noise_count(self) -> int:
        """Number of embeddings classified as noise."""
        return len(self.noise)


def cluster_embeddings(
    embeddings: List[Dict[str, Any]],
    min_cluster_size: int = 2,
    min_samples: int = 1,
    cluster_selection_method: str = 'leaf',
    cluster_selection_epsilon: float = 0.0,
) -> ClusterResult:
    """
    Cluster embeddings using HDBSCAN to discover likely same-speaker groups.
    
    HDBSCAN (Hierarchical Density-Based Spatial Clustering of Applications with Noise):
    - Auto-detects number of clusters based on density
    - Handles noise/outliers by labeling them as -1
    - Uses euclidean distance on L2-normalized vectors (equivalent to cosine distance)
    
    Args:
        embeddings: List of dicts with 'external_id' and 'embedding' keys
        min_cluster_size: Minimum number of segments to form a cluster
        min_samples: HDBSCAN min_samples parameter (affects density estimation)
        cluster_selection_method: 'eom' (Excess of Mass) or 'leaf'
            - 'eom': Finds fewer, larger clusters (good for varying density)
            - 'leaf': Finds more, smaller clusters (better for distinct speakers)
        cluster_selection_epsilon: Distance threshold for merging clusters
            - 0.0: No merging (default)
            - Higher values merge nearby clusters
        
    Returns:
        ClusterResult with clusters and noise segments
    """
    if not embeddings:
        return ClusterResult()
    
    # Filter out embeddings without vectors
    valid_embeddings = [e for e in embeddings if e.get('embedding')]
    
    if len(valid_embeddings) < min_cluster_size:
        logger.warning(f"Not enough embeddings for clustering: {len(valid_embeddings)} < {min_cluster_size}")
        return ClusterResult(
            noise=[e['external_id'] for e in valid_embeddings],
            total_embeddings=len(valid_embeddings),
        )
    
    # Import HDBSCAN (lazy import to avoid loading if not needed)
    try:
        from hdbscan import HDBSCAN
    except ImportError:
        logger.error("HDBSCAN not installed. Run: pip install hdbscan")
        raise ImportError("HDBSCAN not installed. Run: pip install hdbscan")
    
    # Extract embedding vectors
    external_ids = [e['external_id'] for e in valid_embeddings]
    vectors = np.array([e['embedding'] for e in valid_embeddings])
    
    # L2-normalize vectors so euclidean distance is equivalent to cosine distance
    # For normalized vectors: ||a - b||^2 = 2 - 2*cos(a,b)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1  # Avoid division by zero
    vectors_normalized = vectors / norms
    
    logger.info(f"Clustering {len(vectors)} embeddings with HDBSCAN "
                f"(min_cluster_size={min_cluster_size}, method={cluster_selection_method})")
    
    # Run HDBSCAN clustering with euclidean metric on normalized vectors
    # This is equivalent to cosine distance but more widely supported
    #
    # Key parameters:
    # - cluster_selection_method='leaf': Better for distinct speaker clusters
    # - cluster_selection_epsilon: Can help merge very similar clusters
    clusterer = HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric='euclidean',
        cluster_selection_method=cluster_selection_method,
        cluster_selection_epsilon=cluster_selection_epsilon,
    )
    
    labels = clusterer.fit_predict(vectors_normalized)
    
    # Group by cluster
    clusters: Dict[int, List[str]] = defaultdict(list)
    noise: List[str] = []
    
    for external_id, label in zip(external_ids, labels):
        if label == -1:
            noise.append(external_id)
        else:
            clusters[label].append(external_id)
    
    # Convert defaultdict to regular dict
    clusters = dict(clusters)
    
    result = ClusterResult(
        clusters=clusters,
        noise=noise,
        total_embeddings=len(valid_embeddings),
        num_clusters=len(clusters),
    )
    
    logger.info(f"Found {result.num_clusters} clusters, {result.noise_count} noise segments")
    for cluster_id, segment_ids in sorted(clusters.items()):
        logger.info(f"  Cluster {cluster_id}: {len(segment_ids)} segments")
    
    return result


def get_cluster_representatives(
    embeddings: List[Dict[str, Any]],
    cluster_result: ClusterResult,
) -> Dict[int, str]:
    """
    Get a representative segment for each cluster (closest to centroid).
    
    Useful for displaying one example per cluster in the UI.
    
    Args:
        embeddings: Original embeddings list
        cluster_result: Result from cluster_embeddings()
        
    Returns:
        Dict mapping cluster_id -> representative segment external_id
    """
    # Build lookup by external_id
    embedding_by_id = {e['external_id']: e for e in embeddings if e.get('embedding')}
    
    representatives = {}
    
    for cluster_id, segment_ids in cluster_result.clusters.items():
        # Get embeddings for this cluster
        cluster_embeddings = [
            embedding_by_id[sid]['embedding'] 
            for sid in segment_ids 
            if sid in embedding_by_id
        ]
        
        if not cluster_embeddings:
            continue
        
        # Compute centroid
        centroid = np.mean(cluster_embeddings, axis=0)
        
        # Find closest to centroid
        min_dist = float('inf')
        representative = None
        
        for sid in segment_ids:
            if sid not in embedding_by_id:
                continue
            emb = np.array(embedding_by_id[sid]['embedding'])
            # Cosine distance
            dist = 1 - np.dot(centroid, emb) / (np.linalg.norm(centroid) * np.linalg.norm(emb))
            if dist < min_dist:
                min_dist = dist
                representative = sid
        
        if representative:
            representatives[cluster_id] = representative
    
    return representatives