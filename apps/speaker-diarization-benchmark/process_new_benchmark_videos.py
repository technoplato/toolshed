import os
import json
import subprocess
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SOURCE_DIR = Path("data/downloads/source-videos")
CLIPS_DIR = Path("data/clips")
MANIFEST_FILE = CLIPS_DIR / "manifest.json"

VIDEOS = [
    {
        "filename": "Matt and Shane_s Secret Podcast Ep. 147 - Ephemerality [Sep. 8, 2019].mp3",
        "clip_id": "clip_local_mssp_ep147_0_180.mp3",
        "title": "MSSP Ep. 147 (0-180s)",
        "start": 0,
        "duration": 180
    },
    {
        "filename": "Matt and Shane_s Secret Podcast Ep. 78 - Children of the Bread [Apr. 25, 2018].mp3",
        "clip_id": "clip_local_mssp_ep78_0_180.mp3",
        "title": "MSSP Ep. 78 (0-180s)",
        "start": 0,
        "duration": 180
    }
]

def run_command(cmd):
    logger.info(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def main():
    if not MANIFEST_FILE.exists():
        logger.error("Manifest not found")
        return

    with open(MANIFEST_FILE) as f:
        manifest = json.load(f)

    for video in VIDEOS:
        source_path = SOURCE_DIR / video["filename"]
        clip_path = CLIPS_DIR / video["clip_id"]
        
        if not source_path.exists():
            logger.error(f"Source not found: {source_path}")
            continue

        # 1. Extract Clip
        if not clip_path.exists():
            logger.info(f"Extracting clip for {video['title']}...")
            cmd = f"ffmpeg -y -i \"{source_path}\" -ss {video['start']} -t {video['duration']} -acodec copy \"{clip_path}\""
            run_command(cmd)
        else:
            logger.info(f"Clip exists: {clip_path}")

        # 2. Add to Manifest
        # Check if exists
        existing = next((c for c in manifest if c['id'] == video['clip_id']), None)
        if not existing:
            logger.info(f"Adding {video['clip_id']} to manifest...")
            new_entry = {
                "id": video['clip_id'],
                "clip_path": str(clip_path), # Absolute path or relative? Let's use relative to repo root or absolute.
                # Existing entries use absolute path in 'clip_path' field usually, but we fixed IDs to be basename.
                # Let's use the full path as per other entries.
                "clip_path": str(clip_path.absolute()), 
                "title": video['title'],
                "duration": video['duration'],
                "start_time": video['start'],
                "original_url": "local",
                "transcriptions": {}
            }
            manifest.append(new_entry)
        else:
            logger.info(f"Entry {video['clip_id']} already in manifest.")

    # Save manifest updates
    with open(MANIFEST_FILE, 'w') as f:
        json.dump(manifest, f, indent=4)

    # 3. Process Pipeline
    for video in VIDEOS:
        clip_abs_path = (CLIPS_DIR / video["clip_id"]).absolute()
        
        # Transcribe
        logger.info(f"Transcribing {video['clip_id']}...")
        run_command(f"uv run python transcribe_mlx.py \"{clip_abs_path}\"")
        
        # Diarize (with identification)
        logger.info(f"Diarizing {video['clip_id']}...")
        run_command(f"uv run python experiment_segment_embedding.py --clip-id {video['clip_id']}")
        
    # Cleanup
    logger.info("Cleaning up manifest...")
    run_command("uv run python cleanup_manifest_v2.py")
    
    logger.info("Done processing new videos.")

if __name__ == "__main__":
    main()
