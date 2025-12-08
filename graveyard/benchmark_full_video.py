import mlx_whisper
import time
from pathlib import Path
import logging
import subprocess
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

AUDIO_PATH = Path("data/downloads/mssp-old-test-ep-1.wav")
MODEL_NAME = "mlx-community/whisper-small-mlx"

def get_audio_duration(path):
    try:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        logger.error(f"Failed to get duration: {e}")
        return 0.0

def main():
    if not AUDIO_PATH.exists():
        logger.error(f"File not found: {AUDIO_PATH}")
        return

    duration = get_audio_duration(AUDIO_PATH)
    logger.info(f"Audio Duration: {duration:.2f}s ({duration/60:.2f} min)")

    # Warmup
    logger.info("Warming up model with 10s clip...")
    warmup_start = time.time()
    # We can use clip_timestamps to transcribe just a part for warmup?
    # Or just transcribe a small file. 
    # mlx_whisper.transcribe supports clip_timestamps="0,10" ?
    # Signature said clip_timestamps: Union[str, List[float]] = '0'
    # Let's try transcribing the first 10 seconds.
    try:
        mlx_whisper.transcribe(str(AUDIO_PATH), path_or_hf_repo=MODEL_NAME, clip_timestamps="0,10", word_timestamps=True)
    except Exception as e:
        logger.warning(f"Warmup with clip_timestamps failed: {e}. Transcribing full file might be slow initially.")
        # Fallback: just run a dummy transcription on a small array if possible, but let's trust the cache.
    
    warmup_end = time.time()
    logger.info(f"Warmup took: {warmup_end - warmup_start:.2f}s")

    # Full Run
    logger.info(f"Starting full transcription of {AUDIO_PATH}...")
    start_time = time.time()
    result = mlx_whisper.transcribe(str(AUDIO_PATH), path_or_hf_repo=MODEL_NAME, word_timestamps=True)
    end_time = time.time()
    
    process_time = end_time - start_time
    speed_factor = duration / process_time if process_time > 0 else 0
    
    logger.info(f"Full Transcription Finished!")
    logger.info(f"Processing Time: {process_time:.2f}s")
    logger.info(f"Speed Factor: {speed_factor:.2f}x realtime")
    
    # Save result to check
    output_file = "full_transcription_mlx.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    logger.info(f"Saved transcription to {output_file}")

if __name__ == "__main__":
    main()
