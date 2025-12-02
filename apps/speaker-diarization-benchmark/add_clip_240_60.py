import logging
import subprocess
from pathlib import Path
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
CLIPS_DIR = DATA_DIR / "clips"
DOWNLOADS_DIR = DATA_DIR / "downloads"

def create_clip_from_local(source_path, start, end, output_path):
    duration = end - start
    
    # Ensure 16kHz mono WAV
    # ffmpeg -ss <start> -t <duration> -i <source> -ar 16000 -ac 1 <output>
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-t", str(duration),
        "-i", str(source_path),
        "-ar", "16000", "-ac", "1",
        str(output_path)
    ]
    
    logger.info(f"Running ffmpeg: {' '.join(cmd)}")
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path

def main():
    # Configuration
    video_id = "jAlKYYr1bpY"
    source_filename = f"{video_id}.wav"
    source_path = DOWNLOADS_DIR / source_filename
    
    start_time = 240
    duration = 60
    end_time = start_time + duration
    
    clip_id = f"clip_youtube_{video_id}_{start_time}_{duration}.wav"
    clip_path = CLIPS_DIR / clip_id
    
    logger.info(f"Processing {clip_id} from {start_time} to {end_time}...")
    
    # 1. Create Clip from Local Source
    if not source_path.exists():
        logger.error(f"Source file not found at {source_path}")
        return

    if not clip_path.exists():
        create_clip_from_local(source_path, start_time, end_time, clip_path)
        logger.info(f"Created clip: {clip_path}")
    else:
        logger.info(f"Clip already exists: {clip_path}")
    
    # 2. Register in Manifest
    import json
    MANIFEST_FILE = CLIPS_DIR / "manifest.json"
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE, 'r') as f:
            manifest = json.load(f)
    else:
        manifest = []
        
    entry = next((e for e in manifest if e['id'] == clip_id), None)
    if not entry:
        logger.info(f"Adding {clip_id} to manifest...")
        entry = {
            "id": clip_id,
            "clip_path": f"data/clips/{clip_id}",
            "transcriptions": {},
            "title": "Ep 569 - A Derosa Garden (feat. Joe Derosa)",
            "original_url": f"https://www.youtube.com/watch?v={video_id}",
            "start_time": start_time,
            "duration": duration
        }
        manifest.append(entry)
        with open(MANIFEST_FILE, 'w') as f:
            json.dump(manifest, f, indent=2)
    else:
        logger.info(f"Clip {clip_id} already in manifest.")

    # 3. Transcribe (Standardized MLX)
    logger.info("Transcribing with transcribe_mlx.py...")
    subprocess.run(["uv", "run", "python", "transcribe_mlx.py", str(clip_path)], check=True)
    
    # 4. Diarize (Standardized Segment Embedding)
    logger.info("Diarizing with experiment_segment_embedding.py...")
    subprocess.run(["uv", "run", "python", "experiment_segment_embedding.py", "--clip-id", clip_id], check=True)
    
    # 5. Cleanup
    logger.info("Running cleanup...")
    subprocess.run(["uv", "run", "python", "cleanup_manifest_v2.py"], check=True)
    
    logger.info("Done! Check ground_truth_ui.html")

if __name__ == "__main__":
    main()
