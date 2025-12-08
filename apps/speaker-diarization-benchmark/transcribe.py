"""
HOW:
  # As a module
  from transcribe import transcribe, TranscriptionResult, Segment, Word
  result = transcribe("audio.wav")
  
  # As a CLI
  uv run transcribe.py <audio_file>
  uv run transcribe.py audio.wav --start-time 0 --end-time 60
  
  [Inputs]
  - audio_path: Path to audio file (wav, mp3, etc.)
  - start_time: Optional start time in seconds (default: 0)
  - end_time: Optional end time in seconds (default: None = full file)

  [Outputs]
  - TranscriptionResult with text, segments (with word timestamps), and language

  [Side Effects]
  - Loads MLX model if not cached
  - May create temporary files for time-range extraction

WHO:
  Antigravity, Claude AI
  (Context: Audio transcription with MLX Whisper)

WHAT:
  Transcribes audio files using MLX Whisper with word-level timestamps.
  This is the canonical transcription module for the speaker diarization
  benchmark system.

WHEN:
  2025-12-05
  Last Modified: 2025-12-08
  Change Log:
  - 2025-12-08: Added --start-time/--end-time support, moved from graveyard

WHERE:
  apps/speaker-diarization-benchmark/transcribe.py

WHY:
  MLX Whisper provides fast inference on Apple Silicon with native word-level
  timestamps. We standardized on whisper-large-v3-turbo for optimal speed/quality
  trade-off.
"""

import mlx_whisper
from pydantic import BaseModel, Field
from typing import List, Optional

# NOTE: The only combination of transcription we should be using is mlx-community/whisper-large-v3-turbo.
# Do not change this model configuration without explicit approval.
MODEL_NAME = "mlx-community/whisper-large-v3-turbo"


class Word(BaseModel):
    """A single word with timing and confidence."""
    word: str
    start: float
    end: float
    probability: float


class Segment(BaseModel):
    """A transcription segment with words."""
    start: float
    end: float
    text: str
    words: List[Word] = Field(default_factory=list)
    speaker: Optional[str] = "UNKNOWN"


class TranscriptionResult(BaseModel):
    """Complete transcription result."""
    text: str
    segments: List[Segment]
    language: str = "en"


def transcribe(
    audio_path: str,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
) -> TranscriptionResult:
    """
    Transcribes the given audio file using mlx_whisper with the standardized model.
    
    Args:
        audio_path: Path to the audio file
        start_time: Optional start time in seconds (slices audio)
        end_time: Optional end time in seconds (slices audio)
    
    Returns:
        A structured TranscriptionResult with word-level timestamps
    """
    # Handle time range slicing
    actual_path = audio_path
    temp_path = None
    
    if start_time is not None or end_time is not None:
        import tempfile
        import subprocess
        from pathlib import Path
        
        # Create temp file for sliced audio
        suffix = Path(audio_path).suffix
        temp_fd, temp_path = tempfile.mkstemp(suffix=suffix)
        actual_path = temp_path
        
        # Build ffmpeg command
        cmd = ["ffmpeg", "-y", "-i", audio_path]
        if start_time is not None and start_time > 0:
            cmd.extend(["-ss", str(start_time)])
        if end_time is not None:
            duration = end_time - (start_time or 0)
            cmd.extend(["-t", str(duration)])
        cmd.extend(["-c", "copy", temp_path])
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            # Fall back to re-encoding if copy fails
            cmd = ["ffmpeg", "-y", "-i", audio_path]
            if start_time is not None and start_time > 0:
                cmd.extend(["-ss", str(start_time)])
            if end_time is not None:
                duration = end_time - (start_time or 0)
                cmd.extend(["-t", str(duration)])
            cmd.extend([temp_path])
            subprocess.run(cmd, check=True, capture_output=True)
    
    try:
        print(f"Transcribing {audio_path} with {MODEL_NAME}...")
        if start_time is not None or end_time is not None:
            time_range = f"{start_time or 0}s - {end_time or 'end'}s"
            print(f"  Time range: {time_range}")
        
        # Run transcription with word timestamps
        result = mlx_whisper.transcribe(
            actual_path, 
            path_or_hf_repo=MODEL_NAME, 
            word_timestamps=True
        )
        
        # Parse into Pydantic models
        segments = []
        time_offset = start_time or 0
        
        for seg in result.get('segments', []):
            words = []
            if 'words' in seg:
                for w in seg['words']:
                    words.append(Word(
                        word=w['word'],
                        start=w['start'] + time_offset,
                        end=w['end'] + time_offset,
                        probability=w.get('probability', 0.0)
                    ))
            
            segments.append(Segment(
                start=seg['start'] + time_offset,
                end=seg['end'] + time_offset,
                text=seg['text'].strip(),
                words=words
            ))
            
        return TranscriptionResult(
            text=result.get('text', "").strip(),
            segments=segments,
            language=result.get('language', "en")
        )
    finally:
        # Clean up temp file
        if temp_path:
            import os
            try:
                os.unlink(temp_path)
            except:
                pass


if __name__ == "__main__":
    import sys
    import json
    import argparse
    
    parser = argparse.ArgumentParser(description="Transcribe audio using MLX Whisper")
    parser.add_argument("audio_file", help="Path to audio file")
    parser.add_argument("--start-time", type=float, help="Start time in seconds")
    parser.add_argument("--end-time", type=float, help="End time in seconds")
    
    args = parser.parse_args()
    
    try:
        transcription = transcribe(
            args.audio_file,
            start_time=args.start_time,
            end_time=args.end_time,
        )
        print(json.dumps(transcription.model_dump(), indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

