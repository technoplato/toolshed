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
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS speaker_embeddings (
                        id SERIAL PRIMARY KEY,
                        speaker_id TEXT NOT NULL,
                        embedding vector(512),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                # Check if index exists before creating to avoid errors in strict modes, or use IF NOT EXISTS
                cur.execute("CREATE INDEX IF NOT EXISTS speaker_embedding_idx ON speaker_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);")
                conn.commit()

    def add_embedding(self, speaker_id: str, embedding: List[float]):
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO speaker_embeddings (speaker_id, embedding) VALUES (%s, %s)",
                    (speaker_id, embedding)
                )

    def search(self, embedding: List[float], limit: int = 5) -> List[Tuple[str, float]]:
        """
        Returns list of (speaker_id, distance).
        Distance is Cosine Distance (0 = identical, 2 = opposite).
        """
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                # <=> is cosine distance operator in pgvector
                # We cast to vector explicitly just in case
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
                # psycopg returns vector as list/numpy depending on config, usually list or string
                # We assume correct casting by psycopg generic adapter or manual parsing if needed
                # For modern psycopg 3 with [vector] extra, it handles it.
                return [row[0] for row in rows]
