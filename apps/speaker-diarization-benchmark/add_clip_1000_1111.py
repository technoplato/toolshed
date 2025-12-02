import json
import logging
import subprocess
from pathlib import Path
import yt_dlp
from pywhispercpp.model import Model
from prepare_ground_truth import transcribe_clip

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
CLIPS_DIR = DATA_DIR / "clips"
MANIFEST_FILE = CLIPS_DIR / "manifest.json"

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
    url = "https://www.youtube.com/watch?v=13CZPWmke6A"
    start_time = 1000
    end_time = 1111
    duration = end_time - start_time
    clip_id = f"clip_youtube_13CZPWmke6A_{start_time}_{duration}.wav"
    clip_path = CLIPS_DIR / clip_id
    
    logger.info(f"Processing {url} from {start_time} to {end_time}...")
    
    # 1. Download Clip directly
    if not clip_path.exists():
        download_clip(url, start_time, end_time, clip_path)
        logger.info(f"Downloaded: {clip_path}")
    else:
        logger.info(f"Clip already exists: {clip_path}")
    
    # 2. Transcribe (Small Model)
    logger.info("Transcribing with pywhispercpp (small)...")
    model = Model('small', print_realtime=False, print_progress=False)
    transcription = transcribe_clip(model, clip_path)
    
    # 3. Update Manifest
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE) as f:
            manifest = json.load(f)
    else:
        manifest = []
        
    # Check if entry exists
    entry = next((e for e in manifest if e["id"] == clip_id), None)
    if not entry:
        entry = {
            "id": clip_id,
            "clip_path": str(clip_path), # Relative path logic if needed, but absolute/relative consistency matters
            "transcriptions": {}
        }
        manifest.append(entry)
    
    # Ensure path is correct in manifest (relative to repo root or absolute?)
    # Existing manifest uses "data/clips/..."
    entry["clip_path"] = f"data/clips/{clip_id}"
    entry["transcriptions"]["pywhispercpp.small"] = transcription
    
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2)
        
    logger.info("Manifest updated. Now running diarization...")
    
    # 4. Run Diarization
    subprocess.run(["uv", "run", "add_diarization.py"], check=True)

if __name__ == "__main__":
    main()
