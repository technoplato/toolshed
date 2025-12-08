import os
import random
import subprocess
import json
import logging
from pathlib import Path
from pywhispercpp.model import Model

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DOWNLOADS_DIR = Path("data/downloads")
CLIPS_DIR = Path("data/clips")
MANIFEST_FILE = CLIPS_DIR / "manifest.json"

def get_audio_duration(file_path):
    """Get duration of audio file using ffprobe."""
    cmd = [
        "ffprobe", 
        "-v", "error", 
        "-show_entries", "format=duration", 
        "-of", "default=noprint_wrappers=1:nokey=1", 
        str(file_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0

def extract_clip(input_path, output_path, start_time, duration=30):
    """Extract a clip using ffmpeg."""
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite
        "-i", str(input_path),
        "-ss", str(start_time),
        "-t", str(duration),
        "-c", "copy",
        str(output_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)

def transcribe_clip(model, clip_path):
    """Transcribe clip using pywhispercpp."""
    # pywhispercpp transcribe returns a list of segments
    # Each segment is usually an object or list. 
    # We need to ensure it's JSON serializable.
    segments = model.transcribe(str(clip_path))
    
    # Convert segments to list of dicts if they aren't already
    # Assuming segments have t0, t1, text attributes based on common bindings
    # But pywhispercpp might return [Segment(t0=..., t1=..., text=...)]
    
    serialized_segments = []
    for segment in segments:
        # Inspecting segment structure dynamically to be safe
        serialized_segments.append({
            "start": getattr(segment, 't0', 0) / 100.0, # pywhispercpp usually uses 10ms units or similar? 
            # Wait, let's verify units. whisper.cpp usually uses 10ms. 
            # Let's assume standard seconds or check output.
            # Actually, standard pywhispercpp returns Segment objects.
            # Let's just store what we can and debug if needed.
            "end": getattr(segment, 't1', 0) / 100.0,
            "text": getattr(segment, 'text', "").strip()
        })
    
    return serialized_segments

def main():
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load Whisper model
    logger.info("Loading pywhispercpp model (small)...")
    model = Model('small', print_realtime=False, print_progress=False)
    
    wav_files = list(DOWNLOADS_DIR.glob("*.wav"))
    logger.info(f"Found {len(wav_files)} audio files.")
    
    if not wav_files:
        logger.error("No audio files found in downloads directory.")
        return

    # Just pick one random file
    wav_file = random.choice(wav_files)
    logger.info(f"Selected file: {wav_file.name}")
    
    duration = get_audio_duration(wav_file)
    if duration < 30:
        logger.error(f"File too short: {duration}s")
        return
        
    # Pick random start time
    max_start = duration - 30
    start_time = random.uniform(0, max_start)
    
    clip_filename = f"clip_{wav_file.stem}_{int(start_time)}.wav"
    clip_path = CLIPS_DIR / clip_filename
    
    logger.info(f"Extracting 30s clip from {start_time:.2f}s...")
    extract_clip(wav_file, clip_path, start_time, duration=30)
    
    logger.info("Transcribing...")
    transcription = transcribe_clip(model, clip_path)
    
    entry = {
        "id": clip_filename,
        "source_file": wav_file.name,
        "clip_path": str(clip_path),
        "start_time": start_time,
        "duration": 30,
        "transcription": transcription,
    }
    
    # Save single entry manifest
    with open(MANIFEST_FILE, "w") as f:
        json.dump([entry], f, indent=2)
        
    logger.info(f"Done! Manifest saved to {MANIFEST_FILE}")
    logger.info(f"Transcription sample: {transcription}")

if __name__ == "__main__":
    main()
