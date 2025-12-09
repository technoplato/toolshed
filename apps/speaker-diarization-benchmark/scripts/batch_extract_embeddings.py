#!/usr/bin/env python3
"""
HOW:
  Extract embeddings for diarization segments that don't have them.
  
  Usage:
    cd apps/speaker-diarization-benchmark
    uv run python scripts/batch_extract_embeddings.py --run-id <diarization_run_id>
    
  Or with filters:
    uv run python scripts/batch_extract_embeddings.py --run-id <id> --limit 10 --dry-run
    
  [Inputs]
  - --run-id: Diarization run ID to process (required)
  - --limit: Maximum number of segments to process (optional)
  - --dry-run: Show what would be done without executing
  - --verbose: Enable verbose logging
  
  [Environment Variables]
  - INSTANT_APP_ID: InstantDB app ID
  - INSTANT_ADMIN_SECRET: InstantDB admin secret
  - POSTGRES_DSN: PostgreSQL connection string
  - HF_TOKEN: HuggingFace token for PyAnnote models

  [Outputs]
  - Extracts voice embeddings for segments without embedding_id
  - Saves embeddings to PostgreSQL (pgvector)
  - Updates InstantDB segments with embedding_id

WHO:
  Claude AI, User
  (Context: Batch embedding extraction for whisper_identified workflow)

WHAT:
  A batch script to extract voice embeddings for diarization segments
  that were created without embeddings (e.g., from whisper_identified workflow
  or segment splits).
  
  The script:
  1. Queries InstantDB for segments in a run that have no embedding_id
  2. For each segment, extracts a voice embedding using PyAnnote
  3. Saves the embedding to PostgreSQL with speaker_label
  4. Updates the InstantDB segment with the new embedding_id
  
  Memory-aware: Processes segments one at a time to avoid OOM issues
  with the PyAnnote embedding model.

WHEN:
  2025-12-09
  Last Modified: 2025-12-09

WHERE:
  apps/speaker-diarization-benchmark/scripts/batch_extract_embeddings.py

WHY:
  The whisper_identified workflow creates diarization segments from Whisper
  transcription boundaries but doesn't extract embeddings (since we don't
  know who the speakers are yet). This script backfills embeddings for
  segments that have been assigned speakers, enabling future KNN identification.
"""

import os
import sys
import uuid
import argparse
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load .env from repo root
repo_root = project_root.parents[1]
if (repo_root / ".env").exists():
    load_dotenv(repo_root / ".env")


def resolve_audio_path(audio_path: str) -> Optional[str]:
    """
    Resolve audio path for the current environment.
    Same logic as ground_truth_server.py.
    """
    if not audio_path:
        return None
    
    # If the path exists as-is, use it
    if os.path.exists(audio_path):
        return audio_path
    
    # Try to extract the filename and look in known locations
    filename = os.path.basename(audio_path)
    
    # Docker container path
    docker_path = f"/app/data/clips/{filename}"
    if os.path.exists(docker_path):
        return docker_path
    
    # Relative path from current working directory
    relative_path = f"data/clips/{filename}"
    if os.path.exists(relative_path):
        return relative_path
    
    # Try extracting from common path patterns
    if "data/clips/" in audio_path:
        suffix = audio_path.split("data/clips/")[-1]
        for base in ["/app/data/clips/", "data/clips/"]:
            candidate = base + suffix
            if os.path.exists(candidate):
                return candidate
    
    return None


def get_segments_without_embeddings(repo, run_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Query InstantDB for segments in a run that don't have embeddings.
    """
    query = {
        "diarizationRuns": {
            "$": {"where": {"id": run_id}},
            "video": {},
            "diarizationSegments": {
                "speakerAssignments": {
                    "speaker": {}
                }
            }
        }
    }
    
    result = repo._query(query)
    runs = result.get("diarizationRuns", [])
    
    if not runs:
        print(f"❌ Diarization run not found: {run_id}")
        return []
    
    run = runs[0]
    video = run.get("video", [])
    if not video:
        print(f"❌ No video linked to run {run_id}")
        return []
    
    video_info = video[0]
    audio_path = video_info.get("filepath")
    video_id = video_info.get("id")
    
    segments = run.get("diarizationSegments", [])
    
    # Filter to segments without embedding_id
    segments_without_embedding = [
        {
            **seg,
            "audio_path": audio_path,
            "video_id": video_id,
            "run_id": run_id,
        }
        for seg in segments
        if not seg.get("embedding_id") and not seg.get("is_invalidated")
    ]
    
    # Sort by start_time for consistent processing order
    segments_without_embedding.sort(key=lambda s: s.get("start_time", 0))
    
    if limit:
        segments_without_embedding = segments_without_embedding[:limit]
    
    return segments_without_embedding


def get_speaker_name_for_segment(segment: Dict[str, Any]) -> Optional[str]:
    """
    Get the most recent speaker assignment for a segment.
    Returns the speaker name or None if no assignment.
    """
    assignments = segment.get("speakerAssignments", [])
    if not assignments:
        return None
    
    # Sort by assigned_at descending to get most recent
    sorted_assignments = sorted(
        assignments,
        key=lambda a: a.get("assigned_at", ""),
        reverse=True
    )
    
    most_recent = sorted_assignments[0]
    speaker = most_recent.get("speaker", [])
    
    if speaker and len(speaker) > 0:
        return speaker[0].get("name")
    
    return None


def extract_and_save_embedding(
    segment: Dict[str, Any],
    pg_client,
    repo,
    embedder,
    verbose: bool = False
) -> bool:
    """
    Extract embedding for a segment and save to PostgreSQL.
    Returns True if successful, False otherwise.
    """
    segment_id = segment.get("id")
    start_time = segment.get("start_time")
    end_time = segment.get("end_time")
    speaker_label = segment.get("speaker_label", "UNKNOWN")
    audio_path = segment.get("audio_path")
    video_id = segment.get("video_id")
    run_id = segment.get("run_id")
    
    # Get speaker name from assignment
    speaker_name = get_speaker_name_for_segment(segment)
    
    # Resolve audio path
    resolved_path = resolve_audio_path(audio_path)
    if not resolved_path:
        print(f"  ⚠️ Audio file not found: {audio_path}")
        return False
    
    if verbose:
        print(f"  📁 Audio path: {resolved_path}")
        print(f"  ⏱️ Time range: {start_time:.2f}s - {end_time:.2f}s")
        print(f"  🏷️ Speaker label: {speaker_label}")
        print(f"  👤 Speaker name: {speaker_name or '(none)'}")
    
    try:
        # Extract embedding
        t_start = time.time()
        embedding = embedder.extract_embedding(resolved_path, start_time, end_time)
        t_extract = time.time()
        
        if verbose:
            print(f"  🎤 Extracted embedding in {(t_extract - t_start)*1000:.0f}ms")
        
        # Generate embedding ID
        embedding_id = str(uuid.uuid4())
        
        # Save to PostgreSQL
        pg_client.add_embedding(
            external_id=embedding_id,
            embedding=embedding,
            speaker_id=speaker_name,  # Can be None
            speaker_label=speaker_label,
            video_id=video_id,
            diarization_run_id=run_id,
            start_time=start_time,
            end_time=end_time,
        )
        t_save = time.time()
        
        if verbose:
            print(f"  💾 Saved to PostgreSQL in {(t_save - t_extract)*1000:.0f}ms")
        
        # Update InstantDB segment with embedding_id
        repo._transact([
            ["update", "diarizationSegments", segment_id, {"embedding_id": embedding_id}]
        ])
        t_update = time.time()
        
        if verbose:
            print(f"  🔗 Updated InstantDB in {(t_update - t_save)*1000:.0f}ms")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Extract embeddings for diarization segments without them"
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="Diarization run ID to process"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of segments to process"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--only-assigned",
        action="store_true",
        help="Only process segments that have a speaker assignment"
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
    
    print(f"🔧 Batch Embedding Extraction")
    print(f"   Run ID: {args.run_id}")
    print(f"   Limit: {args.limit or 'none'}")
    print(f"   Dry run: {args.dry_run}")
    print(f"   Only assigned: {args.only_assigned}")
    print()
    
    # Initialize clients
    from src.data.impl.instant_db_adapter import InstantDBVideoRepository
    from src.embeddings.pgvector_client import PgVectorClient
    
    repo = InstantDBVideoRepository(app_id, admin_secret)
    pg_client = PgVectorClient(postgres_dsn)
    
    # Get segments without embeddings
    print("📊 Querying segments without embeddings...")
    segments = get_segments_without_embeddings(repo, args.run_id, args.limit)
    
    if not segments:
        print("✅ No segments need embeddings")
        return
    
    # Filter to only assigned if requested
    if args.only_assigned:
        segments = [s for s in segments if get_speaker_name_for_segment(s)]
        print(f"   Filtered to {len(segments)} segments with speaker assignments")
    
    print(f"   Found {len(segments)} segments without embeddings")
    print()
    
    if args.dry_run:
        print("🔍 DRY RUN - Would process these segments:")
        for i, seg in enumerate(segments[:20]):  # Show first 20
            speaker = get_speaker_name_for_segment(seg)
            print(f"   {i+1}. [{seg.get('start_time', 0):.1f}s - {seg.get('end_time', 0):.1f}s] "
                  f"{seg.get('speaker_label', 'UNKNOWN')} → {speaker or '(no assignment)'}")
        if len(segments) > 20:
            print(f"   ... and {len(segments) - 20} more")
        return
    
    # Initialize embedder (lazy load to avoid loading model if dry run)
    print("🔄 Loading PyAnnote embedding model...")
    from ingestion.ground_truth_server import Embedder
    
    # Force model load
    _ = Embedder.get_pipeline()
    print("✅ Model loaded")
    print()
    
    # Process segments
    success_count = 0
    fail_count = 0
    
    for i, segment in enumerate(segments):
        seg_id = segment.get("id", "")[:8]
        start = segment.get("start_time", 0)
        end = segment.get("end_time", 0)
        speaker = get_speaker_name_for_segment(segment)
        
        print(f"[{i+1}/{len(segments)}] Segment {seg_id}... ({start:.1f}s - {end:.1f}s)")
        
        if extract_and_save_embedding(segment, pg_client, repo, Embedder, args.verbose):
            success_count += 1
            print(f"  ✅ Done")
        else:
            fail_count += 1
    
    print()
    print(f"{'='*60}")
    print(f"✅ Completed: {success_count} embeddings extracted")
    if fail_count > 0:
        print(f"❌ Failed: {fail_count} segments")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()