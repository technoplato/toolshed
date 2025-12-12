#!/usr/bin/env python3
"""
HOW:
  Fix the external_id values in PostgreSQL to match InstantDB segment IDs.
  
  Usage:
    cd apps/speaker-diarization-benchmark
    uv run python scripts/migrations/fix_embedding_external_ids.py --run-id <diarization_run_id>
    
  Or with dry-run:
    uv run python scripts/migrations/fix_embedding_external_ids.py --run-id <id> --dry-run
    
  [Inputs]
  - --run-id: Diarization run ID to fix (required)
  - --dry-run: Show what would be done without executing
  
  [Environment Variables]
  - INSTANT_APP_ID: InstantDB app ID
  - INSTANT_ADMIN_SECRET: InstantDB admin secret
  - POSTGRES_DSN: PostgreSQL connection string

WHO:
  Claude AI, User
  (Context: Fixing embedding ID mismatch between InstantDB and PostgreSQL)

WHAT:
  The batch_extract_embeddings.py script was incorrectly generating new UUIDs
  for embeddings instead of using the segment ID. This script fixes the data by:
  
  1. Querying InstantDB for segments with embedding_id
  2. For each segment, updating PostgreSQL to use segment_id as external_id
  3. Updating InstantDB segment.embedding_id to match segment.id
  
  After this migration:
  - PostgreSQL external_id = InstantDB segment.id
  - InstantDB segment.embedding_id = InstantDB segment.id

WHEN:
  2025-12-09
  Last Modified: 2025-12-09

WHERE:
  apps/speaker-diarization-benchmark/scripts/migrations/fix_embedding_external_ids.py

WHY:
  The clustering feature returns external_id values from PostgreSQL, which are
  used to link speaker assignments to segments. If external_id doesn't match
  segment.id, the linking fails with "Missing required attributes" errors.
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load .env from repo root
repo_root = project_root.parents[1]
if (repo_root / ".env").exists():
    load_dotenv(repo_root / ".env")


def main():
    parser = argparse.ArgumentParser(
        description="Fix embedding external_id values to match segment IDs"
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="Diarization run ID to fix"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing"
    )
    
    args = parser.parse_args()
    
    # Check environment
    app_id = os.environ.get("INSTANT_APP_ID")
    admin_secret = os.environ.get("INSTANT_ADMIN_SECRET")
    postgres_dsn = os.environ.get("POSTGRES_DSN")
    
    if not app_id or not admin_secret:
        print("❌ INSTANT_APP_ID and INSTANT_ADMIN_SECRET must be set")
        sys.exit(1)
    
    if not postgres_dsn:
        print("❌ POSTGRES_DSN must be set")
        sys.exit(1)
    
    print(f"🔧 Fix Embedding External IDs")
    print(f"   Run ID: {args.run_id}")
    print(f"   Dry run: {args.dry_run}")
    print()
    
    # Initialize clients
    from src.data.impl.instant_db_adapter import InstantDBVideoRepository
    from src.embeddings.pgvector_client import PgVectorClient
    import psycopg
    
    repo = InstantDBVideoRepository(app_id, admin_secret)
    pg_client = PgVectorClient(postgres_dsn)
    
    # Query InstantDB for segments with embedding_id
    print("📊 Querying segments with embeddings...")
    query = {
        "diarizationRuns": {
            "$": {"where": {"id": args.run_id}},
            "diarizationSegments": {}
        }
    }
    
    result = repo._query(query)
    runs = result.get("diarizationRuns", [])
    
    if not runs:
        print(f"❌ Diarization run not found: {args.run_id}")
        return
    
    run = runs[0]
    segments = run.get("diarizationSegments", [])
    
    # Filter to segments with embedding_id
    segments_with_embedding = [
        s for s in segments
        if s.get("embedding_id") and not s.get("is_invalidated")
    ]
    
    print(f"   Found {len(segments_with_embedding)} segments with embeddings")
    print()
    
    if not segments_with_embedding:
        print("✅ No segments to fix")
        return
    
    # Check which ones need fixing (where segment_id != embedding_id)
    needs_fix = [
        s for s in segments_with_embedding
        if s.get("id") != s.get("embedding_id")
    ]
    
    print(f"   {len(needs_fix)} segments need fixing (segment_id != embedding_id)")
    print()
    
    if not needs_fix:
        print("✅ All segments already have correct embedding_id")
        return
    
    if args.dry_run:
        print("🔍 DRY RUN - Would fix these segments:")
        for i, seg in enumerate(needs_fix[:20]):
            print(f"   {i+1}. segment_id={seg['id'][:8]}... embedding_id={seg.get('embedding_id', 'None')[:8]}...")
        if len(needs_fix) > 20:
            print(f"   ... and {len(needs_fix) - 20} more")
        return
    
    # Fix the data
    print("🔄 Fixing embeddings...")
    
    success_count = 0
    fail_count = 0
    
    for i, seg in enumerate(needs_fix):
        segment_id = seg["id"]
        old_embedding_id = seg.get("embedding_id")
        
        print(f"[{i+1}/{len(needs_fix)}] Fixing segment {segment_id[:8]}...")
        
        try:
            # Step 1: Update PostgreSQL external_id from old_embedding_id to segment_id
            with pg_client._get_conn() as conn:
                with conn.cursor() as cur:
                    # Check if old embedding exists
                    cur.execute(
                        "SELECT id FROM speaker_embeddings WHERE external_id = %s",
                        (old_embedding_id,)
                    )
                    row = cur.fetchone()
                    
                    if row:
                        # Update external_id to segment_id
                        cur.execute(
                            "UPDATE speaker_embeddings SET external_id = %s WHERE external_id = %s",
                            (segment_id, old_embedding_id)
                        )
                        conn.commit()
                        print(f"   ✅ Updated PostgreSQL: {old_embedding_id[:8]}... → {segment_id[:8]}...")
                    else:
                        print(f"   ⚠️ Embedding not found in PostgreSQL: {old_embedding_id[:8]}...")
            
            # Step 2: Update InstantDB segment.embedding_id to segment_id
            repo._transact([
                ["update", "diarizationSegments", segment_id, {"embedding_id": segment_id}]
            ])
            print(f"   ✅ Updated InstantDB embedding_id")
            
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            fail_count += 1
    
    print()
    print(f"{'='*60}")
    print(f"✅ Fixed: {success_count} embeddings")
    if fail_count > 0:
        print(f"❌ Failed: {fail_count} segments")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()