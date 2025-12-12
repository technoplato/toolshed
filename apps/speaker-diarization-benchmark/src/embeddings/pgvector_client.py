"""
HOW:
  from src.embeddings.pgvector_client import PgVectorClient
  
  client = PgVectorClient("postgresql://diarization:diarization_dev@localhost:5433/speaker_embeddings")
  
  # Add an embedding
  client.add_embedding(
      external_id="uuid-of-segment",
      embedding=[...512 floats...],
      speaker_id="Shane Gillis",
      video_id="uuid-of-video",
      start_time=10.5,
      end_time=15.2
  )
  
  # Search for similar speakers
  results = client.search(embedding, limit=5)
  # Returns: [("Shane Gillis", 0.05), ("Matt McCusker", 0.12), ...]

  [Inputs]
  - dsn: PostgreSQL connection string (LibPQ format)
  - DATABASE_URL env var as fallback

  [Outputs]
  - Client instance for embedding operations
  - search() returns list of (speaker_id, cosine_distance) tuples

  [Side Effects]
  - Connects to PostgreSQL
  - Creates tables/indexes on first run if they don't exist

WHO:
  Claude AI, User
  (Context: Speaker identification via KNN on segment embeddings)

WHAT:
  PostgreSQL + pgvector client for speaker embedding storage and search.
  - Per-segment embeddings (512 dimensions from pyannote/embedding)
  - KNN search using cosine distance for speaker identification
  - Links to InstantDB entities via external_id
  - Supports updating speaker_id when user corrects labels

WHEN:
  2025-12-05
  Last Modified: 2025-12-07
  
  [Change Log]
  - 2025-12-05: Initial creation
  - 2025-12-07: Updated for 512-dim, added video_id, timing fields

WHERE:
  apps/speaker-diarization-benchmark/src/embeddings/pgvector_client.py

WHY:
  Enable fast nearest-neighbor search on speaker embeddings.
  Per-segment embeddings (not centroids) allow:
  - Better handling of speaker variation (mood, mic distance)
  - Clustering to discover unknown speakers
  - Comparing new segments to labeled examples
  
  PostgreSQL + pgvector provides:
  - IVFFlat index for approximate KNN (much faster than linear scan)
  - ACID transactions for data integrity
  - Easy integration with existing tools (psql, pg_dump, etc.)
"""

import json
import os
import psycopg
from typing import List, Tuple, Optional, Dict, Any
import numpy as np

# Register pgvector types with psycopg
from pgvector.psycopg import register_vector


class PgVectorClient:
    """
    Client for storing and searching speaker embeddings in PostgreSQL with pgvector.
    
    Embeddings are 512-dimensional vectors from pyannote/embedding model.
    Uses cosine distance for similarity search.
    """
    
    def __init__(self, dsn: str = None):
        """
        Initialize the client.
        
        Args:
            dsn: PostgreSQL connection string. Falls back to DATABASE_URL env var.
        """
        self.dsn = dsn or os.environ.get("DATABASE_URL")
        if not self.dsn:
            raise ValueError("No database connection string provided. Set DATABASE_URL or pass dsn.")
        self._init_db()

    def _get_conn(self):
        """Get a new database connection with pgvector support."""
        conn = psycopg.connect(self.dsn)
        # Register vector type so embeddings are returned as numpy arrays
        register_vector(conn)
        return conn

    def _init_db(self):
        """
        Ensure extension and table exist.
        This is idempotent - safe to call multiple times.
        """
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                
                # Check if table exists
                cur.execute("SELECT to_regclass('public.speaker_embeddings');")
                exists = cur.fetchone()[0]
                
                if not exists:
                    # Create table with 512-dimensional vectors
                    cur.execute("""
                        CREATE TABLE speaker_embeddings (
                            id SERIAL PRIMARY KEY,
                            external_id UUID UNIQUE NOT NULL,
                            video_id UUID,
                            diarization_run_id UUID,
                            speaker_id TEXT DEFAULT 'UNKNOWN',
                            speaker_label TEXT,
                            embedding vector(512) NOT NULL,
                            start_time FLOAT,
                            end_time FLOAT,
                            metadata JSONB DEFAULT '{}',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    
                    # IVFFlat index for cosine similarity
                    cur.execute("""
                        CREATE INDEX speaker_embedding_cosine_idx 
                        ON speaker_embeddings 
                        USING ivfflat (embedding vector_cosine_ops) 
                        WITH (lists = 100);
                    """)
                    
                    # Index for lookups by external_id
                    cur.execute("CREATE INDEX speaker_embedding_ext_id_idx ON speaker_embeddings(external_id);")
                    
                    # Index for lookups by video
                    cur.execute("CREATE INDEX speaker_embedding_video_idx ON speaker_embeddings(video_id);")
                    
                    # Index for lookups by speaker
                    cur.execute("CREATE INDEX speaker_embedding_speaker_idx ON speaker_embeddings(speaker_id);")
                else:
                    # Migrate existing table if needed (add new columns)
                    cur.execute("ALTER TABLE speaker_embeddings ADD COLUMN IF NOT EXISTS video_id UUID;")
                    cur.execute("ALTER TABLE speaker_embeddings ADD COLUMN IF NOT EXISTS diarization_run_id UUID;")
                    cur.execute("ALTER TABLE speaker_embeddings ADD COLUMN IF NOT EXISTS speaker_label TEXT;")
                    cur.execute("ALTER TABLE speaker_embeddings ADD COLUMN IF NOT EXISTS start_time FLOAT;")
                    cur.execute("ALTER TABLE speaker_embeddings ADD COLUMN IF NOT EXISTS end_time FLOAT;")
                    cur.execute("ALTER TABLE speaker_embeddings ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
                    cur.execute("ALTER TABLE speaker_embeddings ADD COLUMN IF NOT EXISTS cluster_id INTEGER;")
                    cur.execute("ALTER TABLE speaker_embeddings ADD COLUMN IF NOT EXISTS cluster_run_id UUID;")
                    
                conn.commit()

    def add_embedding(
        self, 
        external_id: str, 
        embedding: List[float], 
        speaker_id: str = None,
        speaker_label: str = None,
        video_id: str = None,
        diarization_run_id: str = None,
        start_time: float = None,
        end_time: float = None,
        metadata: dict = None
    ):
        """
        Add or update an embedding.
        
        Uses upsert - if external_id exists, updates the row.
        
        Args:
            external_id: UUID linking to DiarizationSegment in InstantDB
            embedding: 512-dimensional vector from pyannote/embedding
            speaker_id: Current speaker label (can be updated)
            speaker_label: Original label from diarization model
            video_id: UUID linking to Video in InstantDB
            diarization_run_id: UUID linking to DiarizationRun in InstantDB
            start_time: Segment start time in seconds
            end_time: Segment end time in seconds
            metadata: Additional data (JSON)
        """
        if metadata is None:
            metadata = {}
        
        # Convert embedding to numpy array for pgvector compatibility
        embedding_array = np.array(embedding, dtype=np.float32)
            
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO speaker_embeddings 
                        (external_id, speaker_id, speaker_label, embedding, video_id, 
                         diarization_run_id, start_time, end_time, metadata) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (external_id) DO UPDATE SET
                        speaker_id = EXCLUDED.speaker_id,
                        speaker_label = EXCLUDED.speaker_label,
                        embedding = EXCLUDED.embedding,
                        video_id = EXCLUDED.video_id,
                        diarization_run_id = EXCLUDED.diarization_run_id,
                        start_time = EXCLUDED.start_time,
                        end_time = EXCLUDED.end_time,
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP;
                    """,
                    (external_id, speaker_id, speaker_label, embedding_array, video_id,
                     diarization_run_id, start_time, end_time, json.dumps(metadata))
                )
                conn.commit()

    def update_speaker_id(self, external_id: str, new_speaker_id: str):
        """
        Update the speaker_id for an embedding.
        
        Called when user corrects a speaker label in the UI.
        
        Args:
            external_id: UUID of the segment
            new_speaker_id: New speaker name
        """
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE speaker_embeddings SET speaker_id = %s, updated_at = CURRENT_TIMESTAMP WHERE external_id = %s",
                    (new_speaker_id, external_id)
                )
                conn.commit()

    def delete_embedding(self, external_id: str):
        """
        Delete an embedding.
        
        Called when a segment is deleted or invalidated.
        
        Args:
            external_id: UUID of the segment
        """
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM speaker_embeddings WHERE external_id = %s",
                    (external_id,)
                )
                conn.commit()

    def search(
        self, 
        embedding: List[float], 
        limit: int = 5,
        video_id: str = None,
        exclude_external_id: str = None
    ) -> List[Tuple[str, str, float]]:
        """
        Find nearest neighbors to an embedding.
        
        Args:
            embedding: 512-dimensional query vector
            limit: Max number of results
            video_id: Optional - only search within this video
            exclude_external_id: Optional - exclude this segment from results
            
        Returns:
            List of (speaker_id, external_id, cosine_distance) tuples,
            ordered by distance (closest first).
        """
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                # Build query with optional filters
                query = """
                    SELECT speaker_id, external_id, embedding <=> %s::vector as dist
                    FROM speaker_embeddings
                    WHERE 1=1
                """
                params = [embedding]
                
                if video_id:
                    query += " AND video_id = %s"
                    params.append(video_id)
                    
                if exclude_external_id:
                    query += " AND external_id != %s"
                    params.append(exclude_external_id)
                
                query += " ORDER BY dist ASC LIMIT %s"
                params.append(limit)
                
                cur.execute(query, params)
                return cur.fetchall()

    def search_by_speaker(
        self, 
        embedding: List[float], 
        limit: int = 5
    ) -> List[Tuple[str, float, int]]:
        """
        Find nearest speakers by averaging distance to their embeddings.
        
        More robust than single-embedding search for speaker identification.
        
        Args:
            embedding: 512-dimensional query vector
            limit: Max number of speakers to return
            
        Returns:
            List of (speaker_id, avg_distance, num_embeddings) tuples.
        """
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        speaker_id, 
                        AVG(embedding <=> %s::vector) as avg_dist,
                        COUNT(*) as num_embeddings
                    FROM speaker_embeddings
                    WHERE speaker_id IS NOT NULL
                    GROUP BY speaker_id
                    ORDER BY avg_dist ASC
                    LIMIT %s
                """, (embedding, limit))
                return cur.fetchall()

    def get_embeddings_for_speaker(self, speaker_id: str) -> List[Dict[str, Any]]:
        """
        Get all embeddings for a speaker.
        
        Useful for computing centroids or analyzing speaker variation.
        
        Args:
            speaker_id: Speaker name
            
        Returns:
            List of dicts with external_id, embedding, start_time, end_time, metadata
        """
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT external_id, embedding, start_time, end_time, metadata
                    FROM speaker_embeddings 
                    WHERE speaker_id = %s
                    ORDER BY start_time
                """, (speaker_id,))
                rows = cur.fetchall()
                return [
                    {
                        "external_id": str(row[0]),
                        "embedding": list(row[1]) if row[1] is not None else None,
                        "start_time": row[2],
                        "end_time": row[3],
                        "metadata": row[4]
                    }
                    for row in rows
                ]

    def get_embedding(self, external_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single embedding by external_id.
        
        Args:
            external_id: UUID of the segment
            
        Returns:
            Dict with all fields, or None if not found
        """
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT external_id, speaker_id, speaker_label, embedding, 
                           video_id, diarization_run_id, start_time, end_time, metadata
                    FROM speaker_embeddings 
                    WHERE external_id = %s
                """, (external_id,))
                row = cur.fetchone()
                if not row:
                    return None
                return {
                    "external_id": str(row[0]),
                    "speaker_id": row[1],
                    "speaker_label": row[2],
                    "embedding": list(row[3]) if row[3] is not None else None,
                    "video_id": str(row[4]) if row[4] else None,
                    "diarization_run_id": str(row[5]) if row[5] else None,
                    "start_time": row[6],
                    "end_time": row[7],
                    "metadata": row[8]
                }

    def count(self, speaker_id: str = None) -> int:
        """
        Count embeddings, optionally filtered by speaker.
        
        Args:
            speaker_id: Optional speaker to filter by
            
        Returns:
            Number of embeddings
        """
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                if speaker_id:
                    cur.execute("SELECT COUNT(*) FROM speaker_embeddings WHERE speaker_id = %s", (speaker_id,))
                else:
                    cur.execute("SELECT COUNT(*) FROM speaker_embeddings")
                return cur.fetchone()[0]

    def list_speakers(self) -> List[Tuple[str, int]]:
        """
        List all speakers and their embedding counts.
        
        Returns:
            List of (speaker_id, count) tuples, ordered by count descending.
        """
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT speaker_id, COUNT(*) as cnt
                    FROM speaker_embeddings
                    GROUP BY speaker_id
                    ORDER BY cnt DESC
                """)
                return cur.fetchall()

    def get_embeddings_by_run(
        self, 
        diarization_run_id: str,
        speaker_id: str = None,
        only_unlabeled: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get all embeddings for a diarization run.
        
        Used for clustering unknown segments to discover likely same-speaker groups.
        
        Args:
            diarization_run_id: UUID of the diarization run
            speaker_id: Optional - filter to specific speaker (or None for unlabeled)
            only_unlabeled: If True, only return embeddings where speaker_id IS NULL
            
        Returns:
            List of dicts with external_id, embedding, speaker_id, speaker_label, 
            start_time, end_time, metadata
        """
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT external_id, embedding, speaker_id, speaker_label, 
                           start_time, end_time, metadata
                    FROM speaker_embeddings 
                    WHERE diarization_run_id = %s
                """
                params = [diarization_run_id]
                
                if only_unlabeled:
                    query += " AND (speaker_id IS NULL OR speaker_id = '')"
                elif speaker_id is not None:
                    query += " AND speaker_id = %s"
                    params.append(speaker_id)
                
                query += " ORDER BY start_time"
                
                cur.execute(query, params)
                rows = cur.fetchall()
                
                return [
                    {
                        "external_id": str(row[0]),
                        "embedding": list(row[1]) if row[1] is not None else None,
                        "speaker_id": row[2],
                        "speaker_label": row[3],
                        "start_time": row[4],
                        "end_time": row[5],
                        "metadata": row[6]
                    }
                    for row in rows
                ]

    def update_cluster_assignments(
        self, 
        cluster_run_id: str,
        cluster_assignments: Dict[str, int]
    ):
        """
        Update cluster assignments for multiple embeddings.
        
        Called after HDBSCAN clustering to persist cluster IDs.
        
        Args:
            cluster_run_id: UUID identifying this clustering run
            cluster_assignments: Dict mapping external_id -> cluster_id
                                 (cluster_id = -1 for noise)
        """
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                for external_id, cluster_id in cluster_assignments.items():
                    cur.execute(
                        """
                        UPDATE speaker_embeddings 
                        SET cluster_id = %s, cluster_run_id = %s, updated_at = CURRENT_TIMESTAMP 
                        WHERE external_id = %s
                        """,
                        (cluster_id, cluster_run_id, external_id)
                    )
                conn.commit()

    def bulk_update_speaker_id(
        self, 
        external_ids: List[str], 
        new_speaker_id: str
    ) -> int:
        """
        Update speaker_id for multiple embeddings at once.
        
        Used for bulk confirmation of clusters.
        
        Args:
            external_ids: List of segment UUIDs to update
            new_speaker_id: New speaker name to assign
            
        Returns:
            Number of rows updated
        """
        if not external_ids:
            return 0
            
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                # Use ANY for efficient bulk update
                cur.execute(
                    """
                    UPDATE speaker_embeddings 
                    SET speaker_id = %s, updated_at = CURRENT_TIMESTAMP 
                    WHERE external_id = ANY(%s)
                    """,
                    (new_speaker_id, external_ids)
                )
                updated = cur.rowcount
                conn.commit()
                return updated

    def get_cluster_assignments(
        self, 
        diarization_run_id: str,
        cluster_run_id: str = None
    ) -> Dict[str, int]:
        """
        Get cluster assignments for a diarization run.
        
        Args:
            diarization_run_id: UUID of the diarization run
            cluster_run_id: Optional - filter to specific clustering run
            
        Returns:
            Dict mapping external_id -> cluster_id
        """
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT external_id, cluster_id
                    FROM speaker_embeddings 
                    WHERE diarization_run_id = %s AND cluster_id IS NOT NULL
                """
                params = [diarization_run_id]
                
                if cluster_run_id:
                    query += " AND cluster_run_id = %s"
                    params.append(cluster_run_id)
                
                cur.execute(query, params)
                return {str(row[0]): row[1] for row in cur.fetchall()}
