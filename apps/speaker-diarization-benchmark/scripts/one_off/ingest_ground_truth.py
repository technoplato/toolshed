"""
HOW:
  Run from the speaker-diarization-benchmark directory:
  `uv run python scripts/one_off/ingest_ground_truth.py`

  [Inputs]
  - Ground truth file: data/clips/clip_youtube_jAlKYYr1bpY_0_60_ground_truth.txt
  - Cached transcription: data/cache/transcriptions/clip_youtube_jAlKYYr1bpY_0_60.json
  - INSTANT_APP_ID (env)
  - INSTANT_ADMIN_SECRET (env)

  [Outputs]
  - Creates Video, Speakers, TranscriptionRun (with Words), DiarizationRun (with Segments),
    and SpeakerAssignments in InstantDB

WHO:
  Antigravity, User
  (Context: Ingesting verified ground truth for MSSP Joe DeRosa episode)

WHAT:
  Parses the ground truth file to extract speaker labels per segment,
  combines with word-level transcription timestamps, and creates all
  entities in InstantDB according to the new schema.

WHEN:
  Created: 2025-12-07

WHERE:
  apps/speaker-diarization-benchmark/scripts/one_off/ingest_ground_truth.py

WHY:
  To populate InstantDB with verified ground truth data that can be used
  for benchmarking speaker diarization accuracy.
"""

import sys
import os
import json
import uuid
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Setup paths
repo_root = Path(__file__).resolve().parents[4]
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# Load .env
load_dotenv(repo_root / ".env")


def parse_ground_truth(filepath: Path) -> dict:
    """
    Parse ground truth file format:
    
    [0.0 - 1.5] MSSP Theme Music: The Wild Wild West.
    [1.8 - 2.4] Shane Gillis: Two hours.
    ...
    
    Returns:
    {
        "title": "...",
        "clip_id": "...",
        "duration": 60,
        "speakers": ["Joe DeRosa", "Matt McCusker", ...],
        "segments": [
            {"start": 0.0, "end": 1.5, "speaker": "MSSP Theme Music", "text": "The Wild Wild West."},
            ...
        ]
    }
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    result = {
        "title": "",
        "clip_id": "",
        "duration": 60,
        "speakers": [],
        "segments": []
    }
    
    # Line 1: Title
    if lines:
        result["title"] = lines[0].strip()
    
    # Line 2: ID and duration
    if len(lines) > 1:
        match = re.search(r'ID:\s*(\S+)', lines[1])
        if match:
            result["clip_id"] = match.group(1)
        match = re.search(r'Duration:\s*(\d+)', lines[1])
        if match:
            result["duration"] = int(match.group(1))
    
    # Find speakers section
    in_speakers = False
    for line in lines:
        line = line.strip()
        if line == "Identify Speakers:":
            in_speakers = True
            continue
        if in_speakers:
            if line.startswith("["):
                in_speakers = False
            elif line:
                result["speakers"].append(line)
    
    # Parse segments: [start - end] Speaker: Text
    segment_pattern = r'\[(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\]\s*([^:]+):\s*(.+)'
    for line in lines:
        match = re.match(segment_pattern, line.strip())
        if match:
            start, end, speaker, text = match.groups()
            result["segments"].append({
                "start": float(start),
                "end": float(end),
                "speaker": speaker.strip(),
                "text": text.strip()
            })
    
    return result


def load_cached_transcription(filepath: Path) -> dict:
    """Load the cached transcription with word-level timestamps."""
    with open(filepath, 'r') as f:
        return json.load(f)


def main():
    app_id = os.getenv("INSTANT_APP_ID")
    admin_secret = os.getenv("INSTANT_ADMIN_SECRET")
    
    if not app_id or not admin_secret:
        print("Error: INSTANT_APP_ID and INSTANT_ADMIN_SECRET must be set")
        return False
    
    print(f"Using App ID: {app_id[:8]}...")
    
    from src.data.impl.instant_db_adapter import InstantDBVideoRepository
    repo = InstantDBVideoRepository(app_id, admin_secret)
    
    # Paths
    ground_truth_file = project_root / "data/clips/clip_youtube_jAlKYYr1bpY_0_60_ground_truth.txt"
    transcription_cache = project_root / "data/cache/transcriptions/clip_youtube_jAlKYYr1bpY_0_60.json"
    clip_path = project_root / "data/clips/clip_youtube_jAlKYYr1bpY_0_60.wav"
    
    if not ground_truth_file.exists():
        print(f"Error: Ground truth file not found: {ground_truth_file}")
        return False
    
    if not transcription_cache.exists():
        print(f"Error: Transcription cache not found: {transcription_cache}")
        return False
    
    print("\n" + "=" * 60)
    print("INGESTING GROUND TRUTH DATA")
    print("=" * 60)
    
    # 1. Parse ground truth
    print("\n1. Parsing ground truth file...")
    gt = parse_ground_truth(ground_truth_file)
    print(f"   Title: {gt['title']}")
    print(f"   Clip ID: {gt['clip_id']}")
    print(f"   Speakers: {gt['speakers']}")
    print(f"   Segments: {len(gt['segments'])}")
    
    # 2. Load transcription
    print("\n2. Loading cached transcription...")
    transcription = load_cached_transcription(transcription_cache)
    total_words = sum(len(s.get('words', [])) for s in transcription.get('segments', []))
    print(f"   Segments: {len(transcription.get('segments', []))}")
    print(f"   Total words: {total_words}")
    
    # 3. Create entities
    print("\n3. Creating entities in InstantDB...")
    
    steps = []
    now = datetime.now().isoformat()
    
    # Video
    video_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"video_{gt['clip_id']}"))
    steps.append(["update", "videos", video_id, {
        "title": gt["title"],
        "url": "https://www.youtube.com/watch?v=jAlKYYr1bpY",
        "filepath": str(clip_path),
        "duration": float(gt["duration"]),
        "ingested_at": now,
        "description": "MSSP Ep 569 - Joe DeRosa (0-60s verified ground truth)",
    }])
    print(f"   ✓ Video: {video_id[:8]}...")
    
    # Speakers
    speaker_ids = {}
    for speaker_name in gt["speakers"]:
        speaker_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"speaker_{speaker_name}"))
        speaker_ids[speaker_name] = speaker_id
        steps.append(["update", "speakers", speaker_id, {
            "name": speaker_name,
            "is_human": speaker_name != "MSSP Theme Music",
            "ingested_at": now,
        }])
        print(f"   ✓ Speaker: {speaker_name} ({speaker_id[:8]}...)")
    
    # Transcription Config
    trans_config_id = str(uuid.uuid4())
    steps.append(["update", "transcriptionConfigs", trans_config_id, {
        "tool": "mlx_whisper",
        "model": "mlx-community/whisper-large-v3-turbo",
        "word_timestamps": True,
        "created_at": now,
    }])
    
    # Transcription Run
    trans_run_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"trans_run_{gt['clip_id']}_ground_truth"))
    steps.append(["update", "transcriptionRuns", trans_run_id, {
        "tool_version": "mlx-whisper-0.4.1",
        "is_preferred": True,
        "executed_at": now,
        "pipeline_script": "ingest_ground_truth.py",
    }])
    steps.append(["link", "videos", video_id, {"transcriptionRuns": trans_run_id}])
    steps.append(["link", "transcriptionRuns", trans_run_id, {"config": trans_config_id}])
    print(f"   ✓ TranscriptionRun: {trans_run_id[:8]}...")
    
    # Words (from transcription cache)
    word_count = 0
    for seg_idx, segment in enumerate(transcription.get('segments', [])):
        for word_idx, word in enumerate(segment.get('words', [])):
            word_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"word_{gt['clip_id']}_{seg_idx}_{word_idx}"))
            steps.append(["update", "words", word_id, {
                "text": word['word'].strip(),
                "start_time": word['start'],
                "end_time": word['end'],
                "confidence": word.get('probability', 0.0),
                "segment_index": seg_idx,
                "word_index": word_idx,
                "ingested_at": now,
            }])
            steps.append(["link", "transcriptionRuns", trans_run_id, {"words": word_id}])
            word_count += 1
    print(f"   ✓ Words: {word_count}")
    
    # Diarization Config
    diar_config_id = str(uuid.uuid4())
    steps.append(["update", "diarizationConfigs", diar_config_id, {
        "tool": "manual",
        "embedding_model": "human_verified",
        "created_at": now,
    }])
    
    # Diarization Run
    diar_run_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"diar_run_{gt['clip_id']}_ground_truth"))
    steps.append(["update", "diarizationRuns", diar_run_id, {
        "workflow": "ground_truth_manual",
        "is_preferred": True,
        "executed_at": now,
        "num_speakers_detected": len(gt["speakers"]),
        "pipeline_script": "ingest_ground_truth.py",
    }])
    steps.append(["link", "videos", video_id, {"diarizationRuns": diar_run_id}])
    steps.append(["link", "diarizationRuns", diar_run_id, {"config": diar_config_id}])
    print(f"   ✓ DiarizationRun: {diar_run_id[:8]}...")
    
    # Diarization Segments + Speaker Assignments
    for seg_idx, segment in enumerate(gt["segments"]):
        seg_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"diar_seg_{gt['clip_id']}_{seg_idx}"))
        steps.append(["update", "diarizationSegments", seg_id, {
            "start_time": segment["start"],
            "end_time": segment["end"],
            "speaker_label": segment["speaker"],
            "is_invalidated": False,
            "confidence": 1.0,  # Ground truth = 100% confident
            "created_at": now,
        }])
        steps.append(["link", "diarizationRuns", diar_run_id, {"diarizationSegments": seg_id}])
        
        # Create speaker assignment
        speaker_id = speaker_ids.get(segment["speaker"])
        if speaker_id:
            assign_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"assign_{gt['clip_id']}_{seg_idx}"))
            steps.append(["update", "speakerAssignments", assign_id, {
                "source": "ground_truth",
                "confidence": 1.0,
                "assigned_by": "human_verified",
                "assigned_at": now,
                "note": "Verified ground truth from manual labeling",
            }])
            steps.append(["link", "diarizationSegments", seg_id, {"speakerAssignments": assign_id}])
            steps.append(["link", "speakerAssignments", assign_id, {"speaker": speaker_id}])
    
    print(f"   ✓ DiarizationSegments: {len(gt['segments'])} (with speaker assignments)")
    
    # Execute transaction
    print("\n4. Executing transaction...")
    try:
        repo._transact(steps)
        print("   ✓ Transaction successful!")
    except Exception as e:
        print(f"   ✗ Transaction failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Verify
    print("\n5. Verifying data...")
    q = {
        "videos": {
            "$": {"where": {"id": video_id}},
            "transcriptionRuns": {
                "words": {}
            },
            "diarizationRuns": {
                "diarizationSegments": {
                    "speakerAssignments": {
                        "speaker": {}
                    }
                }
            }
        }
    }
    result = repo._query(q)
    videos = result.get("videos", [])
    
    if videos:
        video = videos[0]
        trans_runs = video.get("transcriptionRuns", [])
        diar_runs = video.get("diarizationRuns", [])
        
        if trans_runs:
            words = trans_runs[0].get("words", [])
            print(f"   ✓ Video found with {len(words)} words")
        
        if diar_runs:
            segments = diar_runs[0].get("diarizationSegments", [])
            print(f"   ✓ Video found with {len(segments)} diarization segments")
            
            # Check speaker assignments
            assigned = sum(1 for s in segments if s.get("speakerAssignments"))
            print(f"   ✓ {assigned} segments have speaker assignments")
    
    print("\n" + "=" * 60)
    print("✓ GROUND TRUTH INGESTION COMPLETE!")
    print("=" * 60)
    print(f"\nVideo ID: {video_id}")
    print(f"Open Ground Truth UI to view: http://localhost:8000/data/clips/ground_truth_instant.html")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

