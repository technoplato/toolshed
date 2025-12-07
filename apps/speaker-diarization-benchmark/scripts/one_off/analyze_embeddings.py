
"""
WHO:
  Antigravity
  (Context: Verification of Vector DB)

WHAT:
  A script to inspect the `speaker_embeddings` table in Postgres.
  
  [Actions]
  - Connects to PG using local env.
  - Prints table stats (count, columns).
  - Fetches a sample embedding.
  - Performs a similarity search using that sample.
  
  [How to run]
  `source .venv/bin/activate`
  `python3 apps/speaker-diarization-benchmark/scripts/one_off/analyze_embeddings.py`

WHEN:
  2025-12-06
"""

import sys
import os
from dotenv import load_dotenv

# Path setup to find src
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
sys.path.append(project_root)

from src.embeddings.pgvector_client import PgVectorClient

load_dotenv()

def main():
    dsn = os.getenv("POSTGRES_DSN")
    if not dsn:
        print("Error: POSTGRES_DSN is not set.")
        return

    print(f"Connecting to {dsn.split('@')[-1]}...") # Hide password
    client = PgVectorClient(dsn)
    
    with client._get_conn() as conn:
        with conn.cursor() as cur:
            # 1. Count
            cur.execute("SELECT COUNT(*) FROM speaker_embeddings;")
            count = cur.fetchone()[0]
            print(f"Total embeddings: {count}")
            
            # 2. Check Schema
            cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'speaker_embeddings';")
            cols = cur.fetchall()
            print("\nSchema:")
            for c in cols:
                print(f" - {c[0]}: {c[1]}")
                
            if count > 0:
                # 3. Sample search
                print("\nFetching a sample embedding...")
                cur.execute("SELECT pk.id, pk.speaker_id, pk.embedding, pk.external_id FROM speaker_embeddings pk LIMIT 1;")
                row = cur.fetchone()
                pk_id, spk_id, emb, ext_id = row
                # psycopg returns string or object? With vector extension, likely object. 
                # Or string if cast not set up.
                
                print(f"Sample ID: {pk_id}, Speaker: {spk_id}, External ID: {ext_id}")
                if hasattr(emb, '__len__'):
                     print(f"Vector dim: {len(emb)}")
                else:
                     print(f"Vector raw: {emb[:50]}...")
                
                print("\nRunning self-search (should match itself first)...")
                results = client.search(emb, limit=3)
                for r_spk, r_dist in results:
                    print(f" -> Found {r_spk} (dist: {r_dist:.4f})")
            else:
                print("\nTable is empty.")

if __name__ == "__main__":
    main()
