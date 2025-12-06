import os
import json
import logging
import subprocess
from pathlib import Path
import yt_dlp
from pywhispercpp.model import Model
from prepare_ground_truth import transcribe_clip
# Import diarization logic (we'll import the function or run the script)
# To keep it clean, I'll just run the add_diarization script at the end.

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
CLIPS_DIR = DATA_DIR / "clips"
MANIFEST_FILE = CLIPS_DIR / "manifest.json"

def download_audio(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': str(DATA_DIR / 'audio' / '%(id)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return Path(DATA_DIR / 'audio' / f"{info['id']}.wav"), info['id']

def extract_clip(audio_path, clip_id, start_time=300, duration=30): # Start at 5 mins to skip intro
    clip_path = CLIPS_DIR / f"{clip_id}_{start_time}_{duration}.wav"
    if clip_path.exists():
        return clip_path
        
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_time),
        "-t", str(duration),
        "-i", str(audio_path),
        "-ac", "1", "-ar", "16000",
        str(clip_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return clip_path

def main():
    url = "https://www.youtube.com/watch?v=13CZPWmke6A"
    logger.info(f"Processing {url}...")
    
    # 1. Download
    audio_path, video_id = download_audio(url)
    logger.info(f"Downloaded: {audio_path}")
    
    # 2. Extract Clip (skipping intro)
    clip_path = extract_clip(audio_path, f"clip_youtube_{video_id}", start_time=600) # 10 mins in
    logger.info(f"Extracted clip: {clip_path}")
    
    # 3. Transcribe (Small Model)
    logger.info("Transcribing with pywhispercpp (small)...")
    model = Model('small', print_realtime=False, print_progress=False)
    transcription = transcribe_clip(model, clip_path)
    # Add full video to manifest
    # (TODO) ShazamKit Integration for audio fingerprinting
    
    # 4. Update Manifest
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE) as f:
            manifest = json.load(f)
    else:
        manifest = []
        
    # Check if exists
    entry = next((e for e in manifest if e["id"] == clip_path.name), None)
    if not entry:
        entry = {
            "id": clip_path.name,
            "clip_path": str(clip_path.relative_to(Path(".").resolve(), walk_up=True) if clip_path.is_absolute() else clip_path),
            "transcriptions": {}
        }
        manifest.append(entry)
    
    entry["transcriptions"]["pywhispercpp.small"] = transcription
    
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2)
        
    logger.info("Manifest updated. Now running diarization...")
    
    # 5. Run Diarization (reusing existing script)
    subprocess.run(["uv", "run", "add_diarization.py"], check=True)

if __name__ == "__main__":
    main()
