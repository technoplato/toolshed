"""
WHO:
  Antigravity
  (Context: Audio Ingestion System)

WHAT:
  Module to handle video downloading using yt-dlp.
  
  [Inputs]
  - DownloadConfig object containing URL and output directory.

  [Outputs]
  - Downloads a video file to the specified directory.
  - Logs progress to stdout.

  [Side Effects]
  - Creates files on disk.
  - Network usage.

  [How to run/invoke it]
  - `download_video(config)`

WHEN:
  2025-12-05
  Last Modified: 2025-12-05

WHERE:
  apps/speaker-diarization-benchmark/ingestion/download.py

WHY:
  To allow downloading videos directly from the audio ingestion CLI using the robust yt-dlp library.
"""

import logging
from pathlib import Path
import yt_dlp
from .config import DownloadConfig

logger = logging.getLogger(__name__)

def download_video(config: DownloadConfig):
    """
    Downloads a video using yt-dlp.
    """
    logger.info(f"Preparing to download video from: {config.url}")
    
    # Create output directory if it doesn't exist
    config.output_dir.mkdir(parents=True, exist_ok=True)
    
    if config.dry_run:
        logger.info(f"Dry run: Would download {config.url} to {config.output_dir}")
        return

    # Helper function for progress hook
    def progress_hook(d):
        if d['status'] == 'downloading':
            try:
                p = d.get('_percent_str', 'N/A').strip()
                logger.info(f"Downloading: {p}")
            except:
                pass
        elif d['status'] == 'finished':
            logger.info(f"Download complete: {d.get('filename', 'Unknown file')}")

    ydl_opts = {
        'outtmpl': str(config.output_dir / '%(title)s [%(id)s].%(ext)s'),
        'format': 'bestvideo+bestaudio/best',  # Download best video and best audio
        'merge_output_format': 'mp4', # Merge into mp4
        'noplaylist': True,
        'quiet': not config.verbose,
        'progress_hooks': [progress_hook],
        # Add checks to not re-download if file exists (yt-dlp does this by default usually, but good to be explicit if needed)
        # 'nooverwrites': True, # Optional, depends on desired behavior. yt-dlp defaults to skipping if file exists.
    }
    
    # If verbose is on, let yt-dlp print to stdout/stderr as usual
    if config.verbose:
        ydl_opts['quiet'] = False
        ydl_opts['verbose'] = True

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # yt-dlp expects a list of URLs
            logger.info("Starting download...")
            ydl.download([config.url])
            logger.info("Download process finished.")
    except Exception as e:
        logger.error(f"Failed to download video: {e}")
        raise
