"""
Video Processing Workflow Batch Runner

Context:
This script was created to automate the processing of YouTube watch history.
It serves as the orchestration layer that connects history fetching (via fetch_history.py)
with the video processing pipeline (via universal_transcriber/transcribe.py).

Purpose:
- Fetches the last N videos from the user's YouTube history.
- Filters out videos that are too long (> 3 hours).
- Concurrently downloads audio and generates transcriptions using whisper.cpp.
- Upserts metadata and transcription paths to InstantDB.

Usage:
    python apps/transcriber/batch_process.py --limit <N> --max-concurrent <M>

Arguments:
    - --limit (int): Number of most recent videos to fetch from history (default: 5).
    - --max-concurrent (int): Maximum number of parallel downloads/transcriptions (default: 3).

Outputs:
    - Audio files: apps/transcriber/downloads/<platform>_<id>_sound.wav
    - Transcriptions: apps/transcriber/transcriptions/<platform>_<id>_transcript.json
    - Database: Updates 'videos' and 'transcriptions' collections in InstantDB.
    - Console: Progress logs for fetching, filtering, and processing status.

Dependencies:
    - yt-dlp (for history and audio download)
    - pywhispercpp (for transcription)
    - instantdb_admin_client (for database updates)
    - ffmpeg (system dependency for audio conversion)
"""
import asyncio
import argparse
import sys
import os
from fetch_history import fetch_history
from universal_transcriber.transcribe import process_video
from config_model import BatchConfig, WhisperConfig

# Add parent directory to path to import modules
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

async def process_video_with_semaphore(sem, video, i, total, config: BatchConfig):
    async with sem:
        print(f"\n[{i}/{total}] Starting processing for: {video['title']}")
        await process_video(video['url'], whisper_config=config.whisper_config)
        print(f"[{i}/{total}] Finished processing for: {video['title']}")

async def batch_process(config: BatchConfig):
    print(f"Fetching last {config.limit} videos from history...")
    # fetch_history is synchronous, but that's fine as it's a single quick operation (relative to processing)
    # We might want to make it async later if we fetch huge amounts, but for 50 it's fine.
    # Note: fetch_history prints a lot, we might want to silence it or just let it be.
    videos = fetch_history(limit=config.limit)
    
    if not videos:
        print("No videos found to process.")
        return

    print(f"\nfetched {len(videos)} videos. Filtering...")
    
    filtered_videos = []
    for v in videos:
        duration = v.get('duration')
        # Duration can be int (seconds) or string "MM:SS" or "HH:MM:SS" or None
        seconds = 0
        if isinstance(duration, int) or isinstance(duration, float):
            seconds = int(duration)
        elif isinstance(duration, str):
            try:
                parts = list(map(int, duration.split(':')))
                if len(parts) == 2:
                    seconds = parts[0] * 60 + parts[1]
                elif len(parts) == 3:
                    seconds = parts[0] * 3600 + parts[1] * 60 + parts[2]
            except ValueError:
                print(f"Warning: Could not parse duration '{duration}' for {v['title']}. Skipping duration check.")
                seconds = 0 # Treat as short? or skip? Let's treat as short.
        
        if seconds > config.max_duration_hours * 3600:
            print(f"Skipping {v['title']} (Duration: {duration} > {config.max_duration_hours} hours)")
            continue
            
        filtered_videos.append(v)
        
    print(f"\nProcessing {len(filtered_videos)} videos with concurrency limit {config.max_concurrent}...")
    
    sem = asyncio.Semaphore(config.max_concurrent)
    tasks = []
    for i, video in enumerate(filtered_videos, 1):
        task = asyncio.create_task(process_video_with_semaphore(sem, video, i, len(filtered_videos), config))
        tasks.append(task)
        
    await asyncio.gather(*tasks)
    print("\nBatch processing complete!")

def main():
    parser = argparse.ArgumentParser(description="Batch process YouTube videos from history.")
    parser.add_argument("--limit", type=int, default=5, help="Number of videos to fetch")
    parser.add_argument("--max-concurrent", type=int, default=3, help="Max concurrent processings")
    parser.add_argument("--max-duration", type=int, default=5, help="Max duration in hours")
    
    args = parser.parse_args()
    
    # Create config from args
    config = BatchConfig(
        limit=args.limit,
        max_concurrent=args.max_concurrent,
        max_duration_hours=args.max_duration,
        whisper_config=WhisperConfig() # Use defaults for now, could expose args too
    )
    
    asyncio.run(batch_process(config))

if __name__ == "__main__":
    main()
