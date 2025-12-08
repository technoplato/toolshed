#!/usr/bin/env python3
"""
HOW:
  cd apps/speaker-diarization-benchmark
  uv run python scripts/one_off/migrate_embeddings_to_postgres.py
  
  # Or with explicit connection string:
  DATABASE_URL="postgresql://diarization:diarization_dev@localhost:5433/speaker_embeddings" \
    uv run python scripts/one_off/migrate_embeddings_to_postgres.py

  [Inputs]
  - data/speaker_embeddings.json: Existing 512-dim embeddings by speaker
  - DATABASE_URL env var or default localhost connection

  [Outputs]
  - Inserts embeddings into PostgreSQL speaker_embeddings table
  - Prints migration stats

  [Side Effects]
  - Modifies PostgreSQL database
  - Uses upsert so safe to re-run

WHO:
  Claude AI, User
  (Context: Migrating from JSON file to pgvector)

WHAT:
  Migration script to load existing speaker embeddings from JSON into PostgreSQL.
  The JSON file has structure: { "Speaker Name": [[512 floats], [512 floats], ...], ... }
  Each embedding array becomes a row in speaker_embeddings table.

WHEN:
  2025-12-07

WHERE:
  apps/speaker-diarization-benchmark/scripts/one_off/migrate_embeddings_to_postgres.py

WHY:
  Move from file-based embedding storage to pgvector for:
  - Fast KNN search via IVFFlat index
  - Proper speaker identification via nearest neighbors
  - Concurrent access and ACID guarantees
"""

import json
import os
import sys
import uuid
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.embeddings.pgvector_client import PgVectorClient


def main():
    # Paths
    json_file = Path(__file__).parent.parent.parent / "data" / "speaker_embeddings.json"
    
    # Default connection string for local Docker
    dsn = os.environ.get(
        "DATABASE_URL", 
        "postgresql://diarization:diarization_dev@localhost:5433/speaker_embeddings"
    )
    
    print(f"Loading embeddings from: {json_file}")
    print(f"Connecting to: {dsn.replace(':diarization_dev@', ':***@')}")
    
    # Load JSON
    if not json_file.exists():
        print(f"ERROR: {json_file} not found")
        sys.exit(1)
        
    with open(json_file) as f:
        data = json.load(f)
    
    # Connect to PostgreSQL
    client = PgVectorClient(dsn)
    
    # Migrate each speaker's embeddings
    total_migrated = 0
    skipped = 0
    
    for speaker_id, embeddings in data.items():
        print(f"\nMigrating {len(embeddings)} embeddings for: {speaker_id}")
        speaker_migrated = 0
        
        for i, embedding in enumerate(embeddings):
            # Check for NaN or invalid values
            import math
            if any(math.isnan(v) or math.isinf(v) for v in embedding):
                print(f"  ⚠ Skipping embedding {i} - contains NaN/Inf")
                skipped += 1
                continue
            
            # Generate a deterministic UUID based on speaker + index
            # This allows re-running the migration safely
            external_id = str(uuid.uuid5(
                uuid.NAMESPACE_DNS, 
                f"legacy_embedding:{speaker_id}:{i}"
            ))
            
            client.add_embedding(
                external_id=external_id,
                embedding=embedding,
                speaker_id=speaker_id,
                speaker_label=f"LEGACY_{i}",
                metadata={
                    "source": "speaker_embeddings.json",
                    "legacy_index": i,
                    "migration_script": "migrate_embeddings_to_postgres.py"
                }
            )
            total_migrated += 1
            speaker_migrated += 1
            
            # Progress indicator
            if (i + 1) % 20 == 0:
                print(f"  ... {i + 1}/{len(embeddings)}")
        
        print(f"  ✓ Migrated {speaker_migrated} embeddings")
    
    print(f"\n{'='*50}")
    print(f"Migration complete!")
    print(f"Total embeddings migrated: {total_migrated}")
    if skipped > 0:
        print(f"Skipped (NaN/Inf): {skipped}")
    
    # Verify
    print(f"\nVerifying in database...")
    speakers = client.list_speakers()
    print(f"Speakers in database:")
    for speaker, count in speakers:
        print(f"  {speaker}: {count} embeddings")
    
    total_in_db = client.count()
    print(f"\nTotal embeddings in database: {total_in_db}")


if __name__ == "__main__":
    main()

