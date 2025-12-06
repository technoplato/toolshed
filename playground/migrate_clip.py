"""
HOW:
  `uv run --with requests --with python-dotenv playground/migrate_clip.py`

  [Inputs]
  - manifest.json
  - .env

  [Outputs]
  - Uploads one video and its runs to InstantDB using the Repository Pattern.
"""

import argparse
from typing import List, Dict, Any
import requests
import sys
import json
import os
import uuid
import time
from pathlib import Path
from dotenv import load_dotenv

# Hack to import from src
sys.path.append(os.path.join(os.path.dirname(__file__), "../apps/speaker-diarization-benchmark"))

from src.data.impl.instant_db_adapter import InstantDBVideoRepository
from src.data.models import Video, TranscriptionRun, TranscriptionSegment

# Load .env explicitly
load_dotenv()

INSTANT_APP_ID = os.environ.get("INSTANT_APP_ID")
INSTANT_ADMIN_SECRET = os.environ.get("INSTANT_ADMIN_SECRET")

if not INSTANT_APP_ID or not INSTANT_ADMIN_SECRET:
    print("Error: INSTANT_APP_ID or INSTANT_ADMIN_SECRET not set in environment.")
    sys.exit(1)

def main():
    print(f"Targeting App ID: {INSTANT_APP_ID}")
    
    # 1. Initialize Repo
    repo = InstantDBVideoRepository(INSTANT_APP_ID, INSTANT_ADMIN_SECRET)
    
    # 2. Load Data
    manifest_path = Path("apps/speaker-diarization-benchmark/data/clips/manifest.json")
    if not manifest_path.exists():
        print(f"Manifest not found at {manifest_path}")
        return

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
        
    if not manifest:
        print("Manifest empty.")
        return

    parser = argparse.ArgumentParser(description="Migrate a clip to InstantDB.")
    parser.add_argument("--wipe", action="store_true", help="Wipe the ENTIRE database before migrating.")
    args = parser.parse_args()

    # Select the 4th clip
    entry = manifest[3] 
    print(f"Migrating Video: {entry['id']}")
    
    # Check if exists and cleanup
    if args.wipe:
        print("!!! WARNING: Wiping the ENTIRE database in 5 seconds... !!!")
        print("!!! Press Ctrl+C to cancel !!!")
        time.sleep(5)
        print("Cleaning up database (WIPE)...")
        repo.wipe_database()
    else:
        print("Note: Running in append/update mode. Use --wipe to clear DB first.")

    # 3. Create Domain Models
    video = Video(
        id=entry['id'],
        title=entry.get("title", entry["id"]),
        filepath=entry.get("clip_path", ""),
        url=entry.get("titleUrl", ""),
        duration=entry.get("duration", 0)
    )
    
    # 4. Save Video via Repo (Handles Anchors internall)
    print("Saving Video (and generating anchors)...")
    internal_id = repo.save_video(video)
    print(f"Video Saved. Internal UUID: {internal_id}")
    
    # 5. Save Runs
    if "transcriptions" in entry:
        for run_name, segments_data in entry["transcriptions"].items():
            run = TranscriptionRun(
                video_id=internal_id, # Link to Internal ID
                name=run_name,
                model="unknown",
            )
            segments = [
                TranscriptionSegment(
                    start=s.get("start", 0),
                    end=s.get("end", 0),
                    text=s.get("text", "")
                ) for s in segments_data
            ]
            
            print(f"Saving Run: {run_name} with {len(segments)} segments...")
            repo.save_transcription_run(run, segments)
            
            # Let's add a mock Diarization Run if speakers exist
            # (Diarization run saving logic would go here, mimicking the adapter logic)
            # The Repo implementation currently does basic saving. Update Repo to handle complex logic if needed.

    # 6. Verify by retrieval
    print("Verifying...")
    time.sleep(1)
    
    fetched_video = repo.get_video(internal_id)
    if fetched_video:
        print(f"SUCCESS: Retrieved Video: {fetched_video.title}")
        
        # Verify anchors
        anchors = repo.get_stable_segments_by_video_id(internal_id)
        print(f"Stable Segments Found: {len(anchors)}")
        if anchors:
            print(f"First Anchor: {anchors[0].start}-{anchors[0].end} (Index {anchors[0].index})")
    else:
        print("FAILURE: Could not retrieve video.")

if __name__ == "__main__":
    main()
