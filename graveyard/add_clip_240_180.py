import logging
import subprocess
from pathlib import Path
import yt_dlp

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
CLIPS_DIR = DATA_DIR / "clips"

def download_clip(url, start, end, output_path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(output_path.with_suffix('')), # yt-dlp adds extension
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'download_ranges': yt_dlp.utils.download_range_func(None, [(start, end)]),
        'force_keyframes_at_cuts': True,
        'quiet': False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    # Ensure 16kHz mono WAV
    expected_path = output_path.with_suffix('.wav')
    if expected_path.exists():
        temp_path = expected_path.with_suffix('.tmp.wav')
        subprocess.run([
            "ffmpeg", "-y", "-i", str(expected_path),
            "-ar", "16000", "-ac", "1",
            str(temp_path)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        temp_path.replace(expected_path)
        
    return expected_path

def main():
    url = "https://www.youtube.com/watch?v=jAlKYYr1bpY"
    start_time = 240
    duration = 180 # 3 minutes
    end_time = start_time + duration
    
    clip_id = f"clip_youtube_jAlKYYr1bpY_{start_time}_{duration}.wav"
    clip_path = CLIPS_DIR / clip_id
    
    logger.info(f"Processing {url} from {start_time} to {end_time}...")
    
    # 1. Download Clip
    if not clip_path.exists():
        download_clip(url, start_time, end_time, clip_path)
        logger.info(f"Downloaded: {clip_path}")
    else:
        logger.info(f"Clip already exists: {clip_path}")
    
    # 1.5 Register in Manifest
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
            "original_url": url,
            "start_time": start_time,
            "duration": duration
        }
        manifest.append(entry)
        with open(MANIFEST_FILE, 'w') as f:
            json.dump(manifest, f, indent=2)
    else:
        logger.info(f"Clip {clip_id} already in manifest.")

    # 2. Transcribe (Standardized MLX)
    logger.info("Transcribing with transcribe_mlx.py...")
    subprocess.run(["uv", "run", "python", "transcribe_mlx.py", str(clip_path)], check=True)
    
    # 3. Diarize (Standardized Segment Embedding)
    logger.info("Diarizing with experiment_segment_embedding.py...")
    subprocess.run(["uv", "run", "python", "experiment_segment_embedding.py", "--clip-id", clip_id], check=True)
    
    # 4. Cleanup
    logger.info("Running cleanup...")
    subprocess.run(["uv", "run", "python", "cleanup_manifest_v2.py"], check=True)
    
    logger.info("Done! Check ground_truth_ui.html")

if __name__ == "__main__":
    main()
