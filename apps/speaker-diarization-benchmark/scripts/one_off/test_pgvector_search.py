#!/usr/bin/env python3
"""
HOW:
  cd apps/speaker-diarization-benchmark
  uv run python scripts/one_off/test_pgvector_search.py

  [Inputs]
  - PostgreSQL with migrated embeddings
  - DATABASE_URL env var or default localhost connection

  [Outputs]
  - Prints KNN search results
  - Demonstrates speaker identification via nearest neighbors

WHO:
  Claude AI, User
  (Context: Testing pgvector KNN search)

WHAT:
  Test script to exercise the pgvector speaker embedding search.
  - Picks a random embedding from a known speaker
  - Searches for nearest neighbors
  - Verifies the search correctly identifies the speaker

WHEN:
  2025-12-07

WHERE:
  apps/speaker-diarization-benchmark/scripts/one_off/test_pgvector_search.py

WHY:
  Verify that:
  1. KNN search works correctly
  2. Embeddings from same speaker cluster together
  3. Speaker identification via nearest neighbors is accurate
"""

import os
import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.embeddings.pgvector_client import PgVectorClient


def main():
    dsn = os.environ.get(
        "DATABASE_URL", 
        "postgresql://diarization:diarization_dev@localhost:5433/speaker_embeddings"
    )
    
    print("Connecting to PostgreSQL...")
    client = PgVectorClient(dsn)
    
    # List speakers
    print("\n" + "="*60)
    print("SPEAKERS IN DATABASE")
    print("="*60)
    speakers = client.list_speakers()
    for speaker, count in speakers:
        print(f"  {speaker}: {count} embeddings")
    
    # Test 1: Pick Shane Gillis embedding and search
    print("\n" + "="*60)
    print("TEST 1: Search using a Shane Gillis embedding")
    print("="*60)
    
    shane_embeddings = client.get_embeddings_for_speaker("Shane Gillis")
    if shane_embeddings:
        # Pick a random one
        test_emb = random.choice(shane_embeddings)
        query = test_emb["embedding"]
        exclude_id = test_emb["external_id"]
        
        print(f"Query embedding: {exclude_id[:8]}...")
        print(f"Searching for 10 nearest neighbors (excluding self)...\n")
        
        results = client.search(query, limit=10, exclude_external_id=exclude_id)
        
        print("Results (speaker_id, external_id, distance):")
        for speaker_id, ext_id, dist in results:
            match = "✓" if speaker_id == "Shane Gillis" else "✗"
            print(f"  {match} {speaker_id:30} {str(ext_id)[:8]}... dist={dist:.4f}")
        
        # Count how many are Shane
        shane_count = sum(1 for r in results if r[0] == "Shane Gillis")
        print(f"\n{shane_count}/10 nearest neighbors are Shane Gillis")
    
    # Test 2: Search by speaker (averaged distance)
    print("\n" + "="*60)
    print("TEST 2: Search by speaker (averaged distance)")
    print("="*60)
    
    if shane_embeddings:
        query = shane_embeddings[0]["embedding"]
        print("Query: Shane Gillis embedding")
        print("Finding speakers by average distance to all their embeddings...\n")
        
        results = client.search_by_speaker(query, limit=5)
        print("Results (speaker, avg_distance, num_embeddings):")
        for speaker_id, avg_dist, num_emb in results:
            match = "✓" if speaker_id == "Shane Gillis" else " "
            print(f"  {match} {speaker_id:30} avg_dist={avg_dist:.4f} ({num_emb} embeddings)")
    
    # Test 3: Cross-speaker test - Joe DeRosa
    print("\n" + "="*60)
    print("TEST 3: Search using a Joe DeRosa embedding")
    print("="*60)
    
    joe_embeddings = client.get_embeddings_for_speaker("Joe DeRosa")
    if joe_embeddings:
        test_emb = random.choice(joe_embeddings)
        query = test_emb["embedding"]
        exclude_id = test_emb["external_id"]
        
        print(f"Query embedding: {exclude_id[:8]}...")
        
        results = client.search_by_speaker(query, limit=5)
        print("Speakers by average distance:")
        for speaker_id, avg_dist, num_emb in results:
            match = "✓" if speaker_id == "Joe DeRosa" else " "
            print(f"  {match} {speaker_id:30} avg_dist={avg_dist:.4f} ({num_emb} embeddings)")
    
    # Test 4: Matt McCusker
    print("\n" + "="*60)
    print("TEST 4: Search using a Matt McCusker embedding")
    print("="*60)
    
    matt_embeddings = client.get_embeddings_for_speaker("Matt McCusker")
    if matt_embeddings:
        test_emb = random.choice(matt_embeddings)
        query = test_emb["embedding"]
        
        results = client.search_by_speaker(query, limit=5)
        print("Speakers by average distance:")
        for speaker_id, avg_dist, num_emb in results:
            match = "✓" if speaker_id == "Matt McCusker" else " "
            print(f"  {match} {speaker_id:30} avg_dist={avg_dist:.4f} ({num_emb} embeddings)")
    
    print("\n" + "="*60)
    print("TESTS COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()



