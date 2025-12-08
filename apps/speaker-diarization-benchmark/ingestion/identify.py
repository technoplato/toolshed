#!/usr/bin/env python3
"""
HOW:
  # Via audio_ingestion.py CLI (recommended)
  uv run audio_ingestion.py identify \
    --video-id "20dbb029-5729-5072-8c6b-ef1f0a0cab0a" \
    --start-time 0 \
    --end-time 60

  # Execute - actually saves to DB
  uv run audio_ingestion.py identify \
    --video-id "20dbb029-5729-5072-8c6b-ef1f0a0cab0a" \
    --execute

  # As a module (for programmatic use)
  from ingestion.identify import identify_speakers, execute_plan, IdentificationPlan
  plan = identify_speakers(instant_client, pg_client, video_id="...")
  execute_plan(instant_client, pg_client, plan)

  [Inputs]
  - video_id: Video UUID in InstantDB
  - start_time: Optional start time filter (seconds)
  - end_time: Optional end time filter (seconds)
  - threshold: Distance threshold for identification (default: 0.5)
  - top_k: Number of nearest neighbors to consider (default: 5)
  - audio_path: Optional audio file path (auto-detected from video if omitted)

  [Outputs]
  - IdentificationPlan with results for each segment
  - If executed: Speaker assignments saved to InstantDB

  [Side Effects]
  - Reads from InstantDB (via TypeScript server)
  - Reads from PostgreSQL (embeddings)
  - May extract embeddings from audio file
  - If executed: Writes speaker assignments to InstantDB

WHO:
  Claude AI, User
  (Context: Speaker identification - core pipeline component)

WHAT:
  Identifies speakers in diarization segments by comparing their voice
  embeddings to known speaker embeddings in PostgreSQL.

  Workflow:
  1. Fetch diarization segments from InstantDB (via TypeScript server)
  2. For each segment without a speaker assignment:
     a. Extract voice embedding (pyannote) if not already in Postgres
     b. Run KNN search against known embeddings
     c. If distance < threshold, identify as that speaker
  3. Return IdentificationPlan (caller decides whether to execute)

WHEN:
  2025-12-07
  Last Modified: 2025-12-08
  Change Log:
  - 2025-12-08: Moved from scripts/one_off/ to ingestion/ as core pipeline component

WHERE:
  apps/speaker-diarization-benchmark/ingestion/identify.py

WHY:
  To automatically identify speakers in new audio by comparing their voice
  embeddings to previously labeled speakers. This speeds up the labeling
  process and provides consistent speaker identification.
  
  Part of the core audio ingestion pipeline, not a one-off script.
"""

import sys
import os
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from src.embeddings.pgvector_client import PgVectorClient
from .instant_client import InstantClient, DiarizationSegment


@dataclass
class IdentificationResult:
    """Result of identifying a single segment."""
    segment_id: str
    segment_start: float
    segment_end: float
    original_label: str
    identified_speaker: Optional[str]
    speaker_id: Optional[str]
    distance: Optional[float]
    top_matches: List[Dict[str, Any]]
    status: str  # "identified", "unknown", "already_assigned", "skipped"
    reason: Optional[str] = None


@dataclass
class IdentificationPlan:
    """Collection of planned identification actions."""
    video_id: str
    run_id: Optional[str]
    start_time: Optional[float]
    end_time: Optional[float]
    threshold: float
    top_k: int
    timestamp: str
    cache_key: str
    results: List[IdentificationResult] = field(default_factory=list)
    
    @property
    def identified_count(self) -> int:
        return sum(1 for r in self.results if r.status == "identified")
    
    @property
    def unknown_count(self) -> int:
        return sum(1 for r in self.results if r.status == "unknown")
    
    @property
    def skipped_count(self) -> int:
        return sum(1 for r in self.results if r.status in ("already_assigned", "skipped"))
    
    def summary_by_speaker(self) -> Dict[str, int]:
        """Count identifications per speaker."""
        counts: Dict[str, int] = defaultdict(int)
        for r in self.results:
            if r.identified_speaker:
                counts[r.identified_speaker] += 1
        return dict(counts)


def compute_cache_key(
    video_id: str,
    start_time: Optional[float],
    end_time: Optional[float],
    threshold: float,
    top_k: int,
    embedding_count: int,
) -> str:
    """Compute a cache key for the identification run."""
    data = f"{video_id}|{start_time}|{end_time}|{threshold}|{top_k}|{embedding_count}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def get_cache_path(cache_key: str) -> Path:
    """Get the path to a cache file."""
    cache_dir = Path(__file__).parent.parent.parent / "data" / "cache" / "identify"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{cache_key}.json"


def load_cache(cache_key: str) -> Optional[IdentificationPlan]:
    """Load cached identification results if they exist."""
    cache_path = get_cache_path(cache_key)
    if not cache_path.exists():
        return None
    
    try:
        with open(cache_path) as f:
            data = json.load(f)
        
        plan = IdentificationPlan(
            video_id=data["video_id"],
            run_id=data.get("run_id"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            threshold=data["threshold"],
            top_k=data["top_k"],
            timestamp=data["timestamp"],
            cache_key=data["cache_key"],
        )
        
        for r in data.get("results", []):
            plan.results.append(IdentificationResult(**r))
        
        return plan
    except Exception as e:
        print(f"⚠️  Cache load failed: {e}")
        return None


def save_cache(plan: IdentificationPlan) -> None:
    """Save identification results to cache."""
    cache_path = get_cache_path(plan.cache_key)
    
    data = {
        "video_id": plan.video_id,
        "run_id": plan.run_id,
        "start_time": plan.start_time,
        "end_time": plan.end_time,
        "threshold": plan.threshold,
        "top_k": plan.top_k,
        "timestamp": plan.timestamp,
        "cache_key": plan.cache_key,
        "results": [asdict(r) for r in plan.results],
    }
    
    with open(cache_path, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"💾 Cached results to {cache_path}")


def extract_embedding_for_segment(
    audio_path: str,
    start_time: float,
    end_time: float,
) -> Optional[List[float]]:
    """Extract a voice embedding for a time range in an audio file."""
    try:
        from embeddings.pyannote_extractor import PyAnnoteEmbeddingExtractor
        
        extractor = PyAnnoteEmbeddingExtractor()
        embedding = extractor.extract_embedding(
            audio_path=audio_path,
            start_time=start_time,
            end_time=end_time,
        )
        
        if embedding is not None:
            return embedding.tolist()
        return None
    except Exception as e:
        print(f"⚠️  Embedding extraction failed: {e}")
        return None


def identify_speakers(
    instant_client: Optional[InstantClient],
    pg_client: PgVectorClient,
    video_id: str,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
    threshold: float = 0.5,
    top_k: int = 5,
    audio_path: Optional[str] = None,
    use_cache: bool = True,
    segments: Optional[List[DiarizationSegment]] = None,
) -> IdentificationPlan:
    """
    Identify speakers in diarization segments.
    
    This is the COMPUTE phase - no side effects to InstantDB.
    
    Args:
        instant_client: InstantDB client (optional if segments provided)
        pg_client: PostgreSQL client for embeddings
        video_id: Video ID (for caching)
        segments: Optional pre-computed segments (for preview mode).
                  If provided, skips fetching from InstantDB.
    """
    print(f"\n🔍 Identifying speakers in video {video_id[:8]}...")
    print(f"   Threshold: {threshold}, Top-K: {top_k}")
    if start_time is not None or end_time is not None:
        print(f"   Time range: {start_time or 0}s - {end_time or '∞'}s")
    
    # Check cache invalidation - get total embedding count
    speaker_counts = pg_client.list_speakers()  # Returns List[Tuple[speaker_id, count]]
    total_embeddings = sum(count for _, count in speaker_counts)
    
    cache_key = compute_cache_key(
        video_id, start_time, end_time, threshold, top_k, total_embeddings
    )
    
    if use_cache:
        cached = load_cache(cache_key)
        if cached:
            print(f"📦 Using cached results (key: {cache_key})")
            return cached
    
    # Use provided segments or fetch from InstantDB
    if segments is not None:
        print(f"📥 Using {len(segments)} pre-computed segments (preview mode)")
    elif instant_client is not None:
        print(f"\n📥 Fetching segments from InstantDB...")
        segments = instant_client.get_diarization_segments(
            video_id=video_id,
            start_time=start_time,
            end_time=end_time,
        )
        print(f"   Found {len(segments)} segments")
    else:
        raise ValueError("Either instant_client or segments must be provided")
    
    # Get all speakers for lookup (optional - only if we have a client)
    speaker_by_name: Dict[str, Any] = {}
    if instant_client is not None:
        speakers = instant_client.get_speakers()
        speaker_by_name = {s.name: s for s in speakers}
        print(f"   Found {len(speakers)} speakers in database")
    else:
        # In preview mode, we'll get speaker info from PostgreSQL results
        print(f"   Skipping speaker lookup (preview mode)")
    
    # Create plan
    plan = IdentificationPlan(
        video_id=video_id,
        run_id=None,
        start_time=start_time,
        end_time=end_time,
        threshold=threshold,
        top_k=top_k,
        timestamp=datetime.now().isoformat(),
        cache_key=cache_key,
    )
    
    # Process each segment
    for seg in segments:
        # Skip invalidated segments
        if seg.is_invalidated:
            plan.results.append(IdentificationResult(
                segment_id=seg.id,
                segment_start=seg.start_time,
                segment_end=seg.end_time,
                original_label=seg.speaker_label,
                identified_speaker=None,
                speaker_id=None,
                distance=None,
                top_matches=[],
                status="skipped",
                reason="segment invalidated",
            ))
            continue
        
        # Skip if already has a user assignment
        if seg.speaker_assignments:
            user_assignments = [a for a in seg.speaker_assignments if a.get("source") == "user"]
            if user_assignments:
                plan.results.append(IdentificationResult(
                    segment_id=seg.id,
                    segment_start=seg.start_time,
                    segment_end=seg.end_time,
                    original_label=seg.speaker_label,
                    identified_speaker=seg.current_speaker_name,
                    speaker_id=seg.current_speaker_id,
                    distance=None,
                    top_matches=[],
                    status="already_assigned",
                    reason="has user assignment",
                ))
                continue
        
        # Get embedding from Postgres (by segment ID)
        # Note: In preview mode (instant_client=None), segment IDs are temp UUIDs
        # that won't exist in Postgres, so we'll extract embeddings but not save them
        embedding_record = pg_client.get_embedding(seg.id)
        
        if not embedding_record or not embedding_record.get("embedding"):
            # Try to extract embedding if we have audio
            if audio_path and os.path.exists(audio_path):
                print(f"   Extracting embedding for segment {seg.start_time:.1f}s-{seg.end_time:.1f}s...")
                embedding = extract_embedding_for_segment(
                    audio_path, seg.start_time, seg.end_time
                )
                if embedding:
                    # Only save to Postgres if we have a valid InstantDB client
                    # (not in preview mode where video_id might be a YouTube ID)
                    if instant_client is not None:
                        pg_client.add_embedding(
                            external_id=seg.id,
                            embedding=embedding,
                            speaker_id="UNKNOWN",
                            video_id=video_id,
                            start_time=seg.start_time,
                            end_time=seg.end_time,
                            speaker_label=seg.speaker_label,
                        )
                    embedding_record = {"embedding": embedding}
            
            if not embedding_record or not embedding_record.get("embedding"):
                plan.results.append(IdentificationResult(
                    segment_id=seg.id,
                    segment_start=seg.start_time,
                    segment_end=seg.end_time,
                    original_label=seg.speaker_label,
                    identified_speaker=None,
                    speaker_id=None,
                    distance=None,
                    top_matches=[],
                    status="skipped",
                    reason="no embedding available",
                ))
                continue
        
        # Run KNN search
        knn_results = pg_client.search(
            embedding=embedding_record["embedding"],
            limit=top_k,
            exclude_external_id=seg.id,
        )
        
        # Format top matches
        top_matches = []
        for speaker_id, ext_id, distance in knn_results:
            top_matches.append({
                "speaker": speaker_id,
                "external_id": str(ext_id),
                "distance": float(distance),
            })
        
        # Determine identification
        if knn_results and knn_results[0][2] < threshold:
            best_speaker_name = knn_results[0][0]
            best_distance = knn_results[0][2]
            
            # Get speaker ID from our lookup
            speaker = speaker_by_name.get(best_speaker_name)
            speaker_id = speaker.id if speaker else None
            
            plan.results.append(IdentificationResult(
                segment_id=seg.id,
                segment_start=seg.start_time,
                segment_end=seg.end_time,
                original_label=seg.speaker_label,
                identified_speaker=best_speaker_name,
                speaker_id=speaker_id,
                distance=best_distance,
                top_matches=top_matches,
                status="identified",
            ))
        else:
            plan.results.append(IdentificationResult(
                segment_id=seg.id,
                segment_start=seg.start_time,
                segment_end=seg.end_time,
                original_label=seg.speaker_label,
                identified_speaker=None,
                speaker_id=None,
                distance=knn_results[0][2] if knn_results else None,
                top_matches=top_matches,
                status="unknown",
                reason=f"no match below threshold ({threshold})",
            ))
    
    # Save to cache
    if use_cache:
        save_cache(plan)
    
    return plan


def print_plan(plan: IdentificationPlan) -> None:
    """Pretty-print the identification plan."""
    print("\n" + "=" * 70)
    print("📋 IDENTIFICATION RESULTS")
    print("=" * 70)
    
    print(f"\nVideo: {plan.video_id[:8]}...")
    print(f"Time range: {plan.start_time or 0}s - {plan.end_time or '∞'}s")
    print(f"Threshold: {plan.threshold}, Top-K: {plan.top_k}")
    print(f"Cache key: {plan.cache_key}")
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Identified: {plan.identified_count}")
    print(f"   ❓ Unknown: {plan.unknown_count}")
    print(f"   ⏭️  Skipped: {plan.skipped_count}")
    
    if plan.identified_count > 0:
        print(f"\n🎤 Identifications by speaker:")
        for speaker, count in sorted(plan.summary_by_speaker().items(), key=lambda x: -x[1]):
            print(f"   {speaker}: {count} segments")
    
    print(f"\n📝 Details:")
    for r in plan.results:
        time_str = f"{r.segment_start:.1f}s-{r.segment_end:.1f}s"
        
        if r.status == "identified":
            print(f"   ✅ [{time_str}] {r.original_label} → {r.identified_speaker} (dist: {r.distance:.3f})")
        elif r.status == "unknown":
            dist_str = f"{r.distance:.3f}" if r.distance is not None else "N/A"
            print(f"   ❓ [{time_str}] {r.original_label} → UNKNOWN (best dist: {dist_str})")
        elif r.status == "already_assigned":
            print(f"   ⏭️  [{time_str}] {r.original_label} → {r.identified_speaker} (already assigned)")
        elif r.status == "skipped":
            print(f"   ⏭️  [{time_str}] {r.original_label} → SKIPPED ({r.reason})")
    
    print()


def execute_plan(
    instant_client: InstantClient,
    pg_client: PgVectorClient,
    plan: IdentificationPlan,
) -> None:
    """Execute the identification plan - save to InstantDB."""
    print("\n🚀 Executing identification plan...")
    
    # Filter to only identified results (use speaker name if ID not available)
    to_save = [r for r in plan.results if r.status == "identified" and (r.speaker_id or r.identified_speaker)]
    
    if not to_save:
        print("   No identifications to save.")
        return
    
    # Build assignments
    assignments = []
    for r in to_save:
        # Note is stored as JSON in schema, but serialize just in case
        note_data = {
            "method": "knn_identify",
            "script": "identify_speakers.py",
            "threshold": plan.threshold,
            "top_k": plan.top_k,
            "knn_distance": r.distance,
            "top_matches": r.top_matches[:3],  # Keep top 3
            "cache_key": plan.cache_key,
            "timestamp": plan.timestamp,
        }
        
        assignments.append({
            "segment_id": r.segment_id,
            "speaker_id": r.speaker_id,  # May be None - server will lookup by name
            "speaker_name": r.identified_speaker,  # Speaker name for lookup
            "source": "auto_identify",
            "confidence": 1.0 - (r.distance or 0.5),  # Convert distance to confidence
            "note": note_data,  # Will be serialized by the server if needed
            "assigned_by": "system:auto_identify",
        })
    
    # Save to InstantDB
    result = instant_client.create_speaker_assignments(assignments)
    
    if result.get("success"):
        print(f"   ✅ Saved {len(assignments)} speaker assignments to InstantDB")
        
        # Update speaker_id in Postgres for these segments
        for r in to_save:
            try:
                pg_client.update_speaker_id(r.segment_id, r.identified_speaker)
            except Exception as e:
                print(f"   ⚠️  Failed to update Postgres for segment {r.segment_id}: {e}")
        
        print(f"   ✅ Updated speaker IDs in PostgreSQL")
    else:
        print(f"   ❌ Failed to save: {result}")


def main():
    parser = argparse.ArgumentParser(
        description="Identify speakers in diarization segments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run
  uv run scripts/one_off/identify_speakers.py --video-id "abc123..."
  
  # Execute with time range
  uv run scripts/one_off/identify_speakers.py --video-id "abc123..." --start-time 0 --end-time 60 --execute
  
  # Custom threshold
  uv run scripts/one_off/identify_speakers.py --video-id "abc123..." --threshold 0.4 --execute
        """
    )
    
    parser.add_argument("--video-id", required=True, help="Video UUID in InstantDB")
    parser.add_argument("--start-time", type=float, help="Start time filter (seconds)")
    parser.add_argument("--end-time", type=float, help="End time filter (seconds)")
    parser.add_argument("--threshold", type=float, default=0.5, help="Distance threshold (default: 0.5)")
    parser.add_argument("--top-k", type=int, default=5, help="Number of nearest neighbors (default: 5)")
    parser.add_argument("--audio-path", help="Path to audio file (auto-detected if omitted)")
    parser.add_argument("--execute", action="store_true", help="Actually save results (default: dry-run)")
    parser.add_argument("--no-cache", action="store_true", help="Ignore cached results")
    
    args = parser.parse_args()
    
    # Get Postgres DSN - note port 5433 is mapped from Docker
    # Note: Use SPEAKER_DB_DSN for this project's specific postgres, not generic POSTGRES_DSN
    # The docker-compose maps 5433->5432 to avoid conflicts with local postgres
    pg_dsn = os.getenv("SPEAKER_DB_DSN") or "postgresql://diarization:diarization_dev@localhost:5433/speaker_embeddings"
    
    print("🔧 Initializing clients...")
    
    # Initialize clients
    try:
        instant_client = InstantClient()
        print("   ✅ InstantDB server connected")
    except RuntimeError as e:
        print(f"   ❌ {e}")
        sys.exit(1)
    
    try:
        pg_client = PgVectorClient(pg_dsn)
        print("   ✅ PostgreSQL connected")
    except Exception as e:
        print(f"   ❌ PostgreSQL connection failed: {e}")
        sys.exit(1)
    
    # Get audio path from video if not provided
    audio_path = args.audio_path
    if not audio_path:
        video = instant_client.get_video(args.video_id)
        audio_path = video.get("filepath")
        if audio_path:
            print(f"   📁 Audio path from video: {audio_path}")
    
    # Run identification
    plan = identify_speakers(
        instant_client=instant_client,
        pg_client=pg_client,
        video_id=args.video_id,
        start_time=args.start_time,
        end_time=args.end_time,
        threshold=args.threshold,
        top_k=args.top_k,
        audio_path=audio_path,
        use_cache=not args.no_cache,
    )
    
    # Print results
    print_plan(plan)
    
    # Execute if requested
    if args.execute:
        execute_plan(instant_client, pg_client, plan)
    else:
        print("💡 This was a dry run. Add --execute to save results.")


if __name__ == "__main__":
    main()

