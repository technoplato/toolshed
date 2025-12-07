"""
HOW:
  `client = PgVectorClient("postgresql://user:pass@localhost:5432/db")`
  `client.add_embedding("speaker_123", [0.1, 0.2, ...])`

  [Inputs]
  - connection_string: standard LibPQ connection string.

  [Outputs]
  - Client instance.

WHO:
  Antigravity, User
  (Context: Scalable embedding search)

WHAT:
  A wrapper around psycopg (or compatible driver) to handle Vector operations.
  - Ensures `vector` extension exists.
  - Manages `speaker_embeddings` table.
  - Provides `search` using cosine distance (<=> operator).

WHEN:
  2025-12-05

WHERE:
  apps/speaker-diarization-benchmark/src/embeddings/pgvector_client.py

WHY:
  To offload dense vector similarity search to a specialized database engine, 
  avoiding O(N) linear scans in Python.
"""

import psycopg
from typing import List, Tuple, Optional
import numpy as np

class PgVectorClient:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self._init_db()

    def _get_conn(self):
        return psycopg.connect(self.dsn)

    def _init_db(self):
        """Ensure extension and table exist."""
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                # Check if table exists
                cur.execute("SELECT to_regclass('public.speaker_embeddings');")
                exists = cur.fetchone()[0]
                
                if not exists:
                    cur.execute("""
                        CREATE TABLE speaker_embeddings (
                            id SERIAL PRIMARY KEY,
                            external_id UUID UNIQUE, 
                            speaker_id TEXT NOT NULL,
                            embedding vector(512),
                            metadata JSONB DEFAULT '{}',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    cur.execute("CREATE INDEX speaker_embedding_idx ON speaker_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);")
                    cur.execute("CREATE INDEX speaker_embedding_ext_id_idx ON speaker_embeddings(external_id);")
                else:
                    # Migrate if needed (idempotent columns)
                    cur.execute("ALTER TABLE speaker_embeddings ADD COLUMN IF NOT EXISTS external_id UUID UNIQUE;")
                    cur.execute("ALTER TABLE speaker_embeddings ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';")
                    
                conn.commit()

    def add_embedding(self, external_id: str, embedding: List[float], speaker_id: str = "UNKNOWN", metadata: dict = None):
        if metadata is None: metadata = {}
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO speaker_embeddings (external_id, speaker_id, embedding, metadata) 
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (external_id) DO UPDATE SET
                        speaker_id = EXCLUDED.speaker_id,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata;
                    """,
                    (external_id, speaker_id, embedding, json.dumps(metadata))
                )

    def update_speaker_id(self, external_id: str, new_speaker_id: str):
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE speaker_embeddings SET speaker_id = %s WHERE external_id = %s",
                    (new_speaker_id, external_id)
                )

    def delete_embedding(self, external_id: str):
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM speaker_embeddings WHERE external_id = %s",
                    (external_id,)
                )

    def search(self, embedding: List[float], limit: int = 5) -> List[Tuple[str, float]]:
        """
        Returns list of (speaker_id, distance).
        """
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT speaker_id, embedding <=> %s::vector as dist
                    FROM speaker_embeddings
                    ORDER BY dist ASC
                    LIMIT %s
                """, (embedding, limit))
                return cur.fetchall()

    def get_embeddings_for_speaker(self, speaker_id: str) -> List[List[float]]:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT embedding FROM speaker_embeddings WHERE speaker_id = %s", (speaker_id,))
                rows = cur.fetchall()
                # Assuming automatic conversion or list of strings depending on psycopg version
                # If rows return strings, we might need to parse, but pgvector-python usually handles it?
                # We assume correct environment.
                return [row[0] for row in rows]
