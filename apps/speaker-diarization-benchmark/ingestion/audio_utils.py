"""
HOW:
  from ingestion.audio_utils import slice_audio, get_audio_duration
  
  # Slice audio to a time range
  sliced_path = slice_audio(
      audio_path="full_episode.wav",
      start_time=0,
      end_time=60,
      output_dir=Path("data/cache/sliced")
  )
  
  # Get audio duration
  duration = get_audio_duration("audio.wav")

  [Inputs]
  - audio_path: Path to audio file
  - start_time, end_time: Time range in seconds
  - output_dir: Where to save sliced files

  [Outputs]
  - Path to sliced audio file

  [Side Effects]
  - Creates sliced audio file using ffmpeg

WHO:
  Claude AI, User
  (Context: Audio slicing for faster diarization)

WHAT:
  Utility functions for audio file manipulation.
  Primary use: slicing audio to requested time ranges so that
  diarization doesn't process entire files unnecessarily.

WHEN:
  2025-12-08

WHERE:
  apps/speaker-diarization-benchmark/ingestion/audio_utils.py

WHY:
  PyAnnote diarization processes the entire audio file passed to it.
  For a 767MB (1+ hour) file, requesting 0-60s still processes everything.
  
  By slicing the audio first:
  - 767MB → ~10MB for 60s of audio
  - Diarization: 10+ min → ~30 seconds
  
  This is critical for fast iteration during development.
"""

import subprocess
import hashlib
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Default cache directory for sliced audio
SLICED_CACHE_DIR = Path(__file__).parent.parent / "data" / "cache" / "sliced"


def get_audio_duration(audio_path: str) -> Optional[float]:
    """
    Get the duration of an audio file in seconds.
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Duration in seconds, or None if unable to determine
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(audio_path)
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return float(result.stdout.strip())
    except Exception as e:
        logger.warning(f"Could not get audio duration: {e}")
        return None


def slice_audio(
    audio_path: str,
    start_time: float,
    end_time: float,
    output_dir: Optional[Path] = None,
    force: bool = False,
) -> Path:
    """
    Slice an audio file to a specific time range.
    
    Uses ffmpeg for fast, accurate slicing. Results are cached
    based on source file, start time, and end time.
    
    Args:
        audio_path: Path to source audio file
        start_time: Start time in seconds
        end_time: End time in seconds  
        output_dir: Directory for output (default: data/cache/sliced/)
        force: Force re-slice even if cached
        
    Returns:
        Path to sliced audio file
        
    Example:
        # Slice first 60 seconds
        sliced = slice_audio("episode.wav", 0, 60)
        # Returns: data/cache/sliced/episode__0_60.wav
    """
    source_path = Path(audio_path)
    
    if output_dir is None:
        output_dir = SLICED_CACHE_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate cache key based on source file and time range
    # Include file modification time to invalidate if source changes
    mtime = source_path.stat().st_mtime
    cache_key = f"{source_path.stem}__{int(start_time)}_{int(end_time)}_{int(mtime)}"
    output_path = output_dir / f"{cache_key}.wav"
    
    # Check if already cached
    if output_path.exists() and not force:
        logger.info(f"   ✅ Using cached sliced audio: {output_path.name}")
        return output_path
    
    # Calculate duration
    duration = end_time - start_time
    
    logger.info(f"   ⏳ Slicing audio: {start_time}s - {end_time}s ({duration}s)")
    
    try:
        # Use ffmpeg to slice
        # -ss before -i for fast seeking
        # -t for duration
        # -c copy for fast copy without re-encoding (if possible)
        # -y to overwrite
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", str(start_time),
            "-i", str(source_path),
            "-t", str(duration),
            "-c", "copy",  # Try copy first (fast)
            str(output_path),
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        
        # If copy failed, try re-encoding
        if result.returncode != 0 or not output_path.exists():
            logger.debug("Copy mode failed, trying re-encode...")
            cmd = [
                "ffmpeg",
                "-y", 
                "-ss", str(start_time),
                "-i", str(source_path),
                "-t", str(duration),
                "-ar", "16000",  # 16kHz sample rate (standard for speech)
                "-ac", "1",      # Mono
                str(output_path),
            ]
            subprocess.run(cmd, check=True, capture_output=True)
        
        # Verify output
        if output_path.exists():
            size_mb = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"   ✅ Sliced audio created: {output_path.name} ({size_mb:.1f}MB)")
            return output_path
        else:
            raise RuntimeError("Output file not created")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"   ❌ ffmpeg failed: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"   ❌ Audio slicing failed: {e}")
        raise


def get_slice_cache_path(
    audio_path: str,
    start_time: float,
    end_time: float,
) -> Tuple[Path, bool]:
    """
    Get the expected cache path for a sliced audio file.
    
    Args:
        audio_path: Source audio path
        start_time: Start time
        end_time: End time
        
    Returns:
        Tuple of (cache_path, exists)
    """
    source_path = Path(audio_path)
    mtime = source_path.stat().st_mtime if source_path.exists() else 0
    cache_key = f"{source_path.stem}__{int(start_time)}_{int(end_time)}_{int(mtime)}"
    output_path = SLICED_CACHE_DIR / f"{cache_key}.wav"
    
    return output_path, output_path.exists()

