#!/usr/bin/env -S uv run python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "numpy",
#     "torch",
#     "scipy",
#     "scikit-learn",
#     "pyannote.audio",
#     "mlx-whisper",
#     "omegaconf",
#     "pytorch-lightning",
#     "pydantic",
# ]
# ///

"""
WHO:   Antigravity, User
       (Context: Created to automate processing of new clips for the Ground Truth UI)

WHAT:  Processes a specific audio clip to generate transcription and diarization data, 
       then updates the manifest.json file so the clip can be viewed in the UI.
       
       [Inputs]
       - clip_path: Path to the audio clip (e.g., data/clips/clip_name.wav)
       - --manifest: Path to manifest.json (default: data/clips/manifest.json)
       
       [Outputs]
       - Updates manifest.json with a new entry containing:
         - Transcription (mlx_whisper_turbo)
         - Segment Level Matching results
         - Segment Level Nearest Neighbor results
       
       [Side Effects]
       - Caches transcription in data/cache/transcriptions/
       - Modifies manifest.json

WHEN:  2025-12-02
       [Change Log:
        - 2025-12-02: Initial creation to support UI integration of new clips]

WHERE: apps/speaker-diarization-benchmark/process_new_clip.py
       Run via `uv run apps/speaker-diarization-benchmark/process_new_clip.py <clip_path>`

WHY:   To allow the user to easily visualize and verify the performance of different 
       diarization workflows on new clips without manually editing JSON files.
"""

import json
import logging
import argparse
from pathlib import Path
import sys

# Add parent directory to path to import benchmark_baseline
sys.path.append(str(Path(__file__).parent / "plain-text-benchmark"))
from benchmark_baseline import (
    transcribe, 
    run_segment_level_matching_workflow, 
    run_segment_level_nearest_neighbor_workflow,
    TranscriptionResult, Segment, Word
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Process a clip and update manifest.json")
    parser.add_argument("clip_path", type=str, help="Path to the audio clip")
    parser.add_argument("--manifest", type=str, default="apps/speaker-diarization-benchmark/data/clips/manifest.json", help="Path to manifest.json")
    args = parser.parse_args()

    clip_path = Path(args.clip_path).resolve()
    if not clip_path.exists():
        logger.error(f"Clip not found: {clip_path}")
        return

    # Load Manifest
    manifest_path = Path(args.manifest).resolve()
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    else:
        manifest = []

    # Check if clip exists in manifest
    clip_id = clip_path.name
    clip_entry = next((c for c in manifest if c['id'] == clip_id), None)
    
    if not clip_entry:
        logger.info(f"Creating new manifest entry for {clip_id}")
        clip_entry = {
            "id": clip_id,
            "title": clip_id,
            "duration": 120.0, # Approximate, maybe get actual
            "transcriptions": {},
            "transcription_metadata": {}
        }
        manifest.append(clip_entry)
    
    # 1. Transcribe (or load cache)
    # We can reuse benchmark_baseline logic or just call transcribe
    # benchmark_baseline caches to data/cache/transcriptions
    # Let's just call transcribe, it uses mlx_whisper
    logger.info("Transcribing...")
    try:
        # Check cache first (manual check as benchmark_baseline does it inside main)
        cache_dir = Path("apps/speaker-diarization-benchmark/data/cache/transcriptions")
        cache_file = cache_dir / f"{clip_path.stem}.json"
        
        transcription_result = None
        if cache_file.exists():
            logger.info(f"Loading transcription from cache: {cache_file}")
            with open(cache_file, 'r') as f:
                data = json.load(f)
                segments = []
                for s in data['segments']:
                    words = [Word(**w) for w in s['words']]
                    segments.append(Segment(start=s['start'], end=s['end'], text=s['text'], words=words))
                transcription_result = TranscriptionResult(text=data['text'], segments=segments, language=data['language'])
        else:
            transcription_result = transcribe(str(clip_path))
            # Save to cache
            cache_dir.mkdir(parents=True, exist_ok=True)
            with open(cache_file, 'w') as f:
                if hasattr(transcription_result, 'model_dump'):
                    data = transcription_result.model_dump()
                else:
                    data = transcription_result.dict()
                json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return

    # Update manifest with raw transcription
    # Convert segments to dicts
    seg_dicts = []
    for s in transcription_result.segments:
        seg_dicts.append({
            "start": s.start,
            "end": s.end,
            "text": s.text,
            "speaker": "UNKNOWN"
        })
    clip_entry['transcriptions']['mlx_whisper_turbo'] = seg_dicts

    # 2. Run Segment Level Matching
    logger.info("Running Segment Level Matching...")
    class MockArgs:
        threshold = 0.5
        window = 0
        cluster_threshold = 0.5
        id_threshold = 0.4 # Default
    
    segments_matching, _ = run_segment_level_matching_workflow(clip_path, transcription_result.segments, MockArgs())
    clip_entry['transcriptions']['segment_level_matching'] = segments_matching

    # 3. Run Segment Level Nearest Neighbor
    logger.info("Running Segment Level Nearest Neighbor...")
    MockArgs.id_threshold = 0.8 # Higher threshold as per previous run
    segments_nn, _ = run_segment_level_nearest_neighbor_workflow(clip_path, transcription_result.segments, MockArgs())
    clip_entry['transcriptions']['segment_level_nearest_neighbor'] = segments_nn

    # Save Manifest
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Updated manifest at {manifest_path}")

if __name__ == "__main__":
    main()
