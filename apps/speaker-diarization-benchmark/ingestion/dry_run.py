"""
HOW:
  from ingestion.dry_run import print_dry_run_output
  
  print_dry_run_output(config)  # Prints comprehensive dry-run info
  
  [Inputs]
  - config: IngestConfig, TranscribeConfig, DiarizeConfig, or IdentifyConfig

  [Outputs]
  - Formatted dry-run output to stdout showing what would happen

  [Side Effects]
  - Console output only

WHO:
  Claude AI, User
  (Context: Dry-run output for audio ingestion)

WHAT:
  Generates comprehensive, self-documenting dry-run output that shows:
  1. What each step will do
  2. Which files implement each step
  3. Why we use specific tools/defaults
  4. How to customize with flags
  5. The exact command to execute

WHEN:
  2025-12-08

WHERE:
  apps/speaker-diarization-benchmark/ingestion/dry_run.py

WHY:
  Users need to understand what will happen before running pipelines.
  Self-documenting output reduces the need to read source code.
"""

from pathlib import Path
from typing import Optional, Union

from .config import IngestConfig, TranscribeConfig, DiarizeConfig, IdentifyConfig


# Box drawing characters for beautiful output
BOX_H = "━"
BOX_V = "│"
BOX_TL = "┏"
BOX_TR = "┓"
BOX_BL = "┗"
BOX_BR = "┛"
LINE_H = "─"


def _header(title: str, emoji: str = "🔍") -> str:
    """Create a section header."""
    width = 72
    line = BOX_H * width
    return f"\n{line}\n{emoji} {title}\n{line}"


def _subheader(title: str) -> str:
    """Create a subsection header."""
    return f"\n{LINE_H * 40}\n{title}\n{LINE_H * 40}"


def _format_time_range(start: float, end: Optional[float]) -> str:
    """Format time range for display."""
    end_str = f"{end}s" if end is not None else "end"
    return f"{start}s - {end_str}"


def _check_file_status(path: Path) -> tuple[str, str]:
    """
    Check if a file exists and get its size.
    
    Returns:
        Tuple of (status_emoji, status_message)
    """
    if path.exists():
        size_mb = path.stat().st_size / (1024 * 1024)
        return "✅", f"Already exists ({size_mb:.1f} MB)"
    return "⏳", "Will be created"


def _get_cache_status(cache_path: Path) -> tuple[str, str]:
    """Check if cache exists."""
    if cache_path.exists():
        return "✅", "Using cached result"
    return "⏳", "Will be computed"


def print_transcribe_dry_run(config: TranscribeConfig) -> None:
    """Print dry-run output for transcribe command."""
    print(_header("DRY RUN: Transcribe", "📝"))
    
    print(f"""
📂 Input
   Audio: {config.audio_path}
   Time range: {_format_time_range(config.start_time, config.end_time)}
   
🔧 Configuration
   Runner: {config.runner}
   Model: {config.model}
   
📁 Implementation: transcribe.py
🔧 Uses: MLX Whisper for fast Apple Silicon inference

💡 Why MLX Whisper Turbo?
   • Fastest inference on Apple Silicon (M1/M2/M3)
   • Native word-level timestamps
   • Distilled model optimized for speed

🎛️  To customize:
   --start-time <sec>     Start time in seconds
   --end-time <sec>       End time in seconds
   --runner <name>        Change transcription runner
   --model <name>         Change model
""")
    
    _print_execute_command("transcribe", config.audio_path, config)


def print_diarize_dry_run(config: DiarizeConfig) -> None:
    """Print dry-run output for diarize command."""
    print(_header("DRY RUN: Diarize", "🎙️"))
    
    print(f"""
📂 Input
   Audio: {config.audio_path}
   Time range: {_format_time_range(config.start_time, config.end_time)}
   
🔧 Configuration
   Workflow: {config.workflow.name}
   Pipeline: {config.pipeline}
   Threshold: {config.workflow.threshold}
   
📁 Implementation: ingestion/workflows/local/pyannote.py
🔧 Uses: PyAnnote Audio for speaker segmentation

💡 Why pyannote-local?
   • Runs entirely on local hardware (no API costs)
   • Full control over model parameters
   • Consistent results across runs

🎛️  To customize:
   --start-time <sec>     Start time in seconds
   --end-time <sec>       End time in seconds  
   --workflow <name>      Change workflow (pyannote, wespeaker, etc.)
   --pipeline <name>      Change PyAnnote pipeline version
   --min-speakers <n>     Minimum expected speakers
   --max-speakers <n>     Maximum expected speakers
""")
    
    _print_execute_command("diarize", config.audio_path, config)


def print_identify_dry_run(config: IdentifyConfig) -> None:
    """Print dry-run output for identify command."""
    print(_header("DRY RUN: Identify Speakers", "🔍"))
    
    # Try to get speaker counts from postgres
    speaker_info = _get_speaker_info()
    
    print(f"""
📂 Input
   Video ID: {config.video_id}
   Time range: {_format_time_range(config.start_time, config.end_time)}
   
🔧 Configuration
   Method: KNN search (PostgreSQL pgvector)
   Threshold: {config.threshold} (cosine distance)
   Top-K: {config.top_k} nearest neighbors
{speaker_info}
   
📁 Implementation: scripts/one_off/identify_speakers.py
🔧 Uses: pgvector for fast KNN search

💡 Why KNN identification?
   • Compares voice embeddings to known speakers
   • Sub-second search across 200+ embeddings
   • Threshold controls confidence level

🎛️  To customize:
   --threshold <float>    Distance threshold (lower = stricter)
   --top-k <int>          Number of nearest neighbors
   --execute              Actually save results (default is dry-run)
""")
    
    print(f"""
{BOX_H * 72}
📋 To execute, run:
{BOX_H * 72}

uv run audio_ingestion.py identify \\
  --video-id "{config.video_id}" \\
  --start-time {config.start_time} \\
  {'--end-time ' + str(config.end_time) + ' \\' if config.end_time else ''}
  --threshold {config.threshold} \\
  --execute

{BOX_H * 72}
""")


def print_ingest_dry_run(config: IngestConfig) -> None:
    """Print comprehensive dry-run output for full ingest pipeline."""
    print(_header("DRY RUN: Audio Ingestion Pipeline", "🔍"))
    
    # Determine audio path
    if config.is_url:
        video_id = _extract_video_id(config.source)
        audio_path = config.output_dir / f"{video_id}.wav"
        download_status, download_msg = _check_file_status(audio_path)
    else:
        audio_path = Path(config.source)
        video_id = audio_path.stem
        download_status, download_msg = "⏭️", "Skipping (local file)"
    
    # Check transcription cache
    cache_dir = Path(__file__).parent.parent / "data/cache/transcriptions"
    cache_file = cache_dir / f"{video_id}.json"
    trans_status, trans_msg = _get_cache_status(cache_file)
    
    # Get speaker info
    speaker_info = _get_speaker_info()
    
    # Step 1: Download
    print(f"""
📥 Step 1: Download
{LINE_H * 40}
   URL: {config.source if config.is_url else '(local file)'}
   Output: {audio_path}
   Status: {download_status} {download_msg}
   
   📁 Implementation: ingestion/download.py
   🔧 Uses: yt-dlp to download and extract audio
   
   To customize:
     --output-dir <path>    Change download directory
     --format <fmt>         Change output format (wav, mp3)
""")
    
    # Step 2: Transcribe
    print(f"""
📝 Step 2: Transcribe
{LINE_H * 40}
   Audio: {audio_path}
   Time range: {_format_time_range(config.start_time, config.end_time)}
   Runner: mlx-whisper
   Model: mlx-community/whisper-large-v3-turbo
   Cache: {trans_status} {trans_msg}
   
   📁 Implementation: transcribe.py
   🔧 Uses: MLX Whisper for fast Apple Silicon inference
   💾 Cache: data/cache/transcriptions/{video_id}.json
   
   Why MLX Whisper Turbo?
   • Fastest inference on Apple Silicon (M1/M2/M3)
   • Native word-level timestamps
   • Distilled model optimized for speed
   
   To customize:
     --start-time <sec>     Start time in seconds
     --end-time <sec>       End time in seconds
""")
    
    # Step 3: Diarize
    print(f"""
🎙️ Step 3: Diarize
{LINE_H * 40}
   Workflow: {config.workflow}
   Pipeline: {config.pipeline}
   Time range: {_format_time_range(config.start_time, config.end_time)}
   Expected segments: ~50-100 (estimated)
   
   📁 Implementation: ingestion/workflows/local/pyannote.py
   🔧 Uses: PyAnnote Audio for speaker segmentation
   💾 Cache: data/cache/diarization/{video_id}__{workflow}.json
   
   ⚡ Audio Slicing Optimization:
   • Full audio file can be 767MB+ (1+ hour episodes)
   • Audio is sliced to requested time range BEFORE diarization
   • data/cache/sliced/{video_id}__0_60_*.wav (~10MB for 60s)
   • Speeds up diarization from 10+ min to ~30 seconds
   
   Why pyannote-local?
   • Runs entirely on local hardware (no API costs)
   • Full control over model parameters
   • Consistent results across runs
   
   To customize:
     --workflow <name>      Change workflow (pyannote, wespeaker)
     --pipeline <name>      Change PyAnnote pipeline version
""")
    
    # Step 4: Identify (if not skipped)
    if not config.skip_identify:
        print(f"""
🔍 Step 4: Identify
{LINE_H * 40}
   Method: KNN search (PostgreSQL pgvector)
   Threshold: {config.threshold} (cosine distance)
   Top-K: 5 nearest neighbors
{speaker_info}
   
   📁 Implementation: ingestion/identify.py
   🔧 Uses: pgvector for fast KNN search
   
   Why KNN identification?
   • Compares voice embeddings to known speakers
   • Sub-second search across 200+ embeddings
   • Threshold controls confidence level
   
   To customize:
     --threshold <float>    Distance threshold (lower = stricter)
     --skip-identify        Skip this step entirely
""")
    else:
        print(f"""
🔍 Step 4: Identify
{LINE_H * 40}
   Status: ⏭️  SKIPPED (--skip-identify flag)
""")
    
    # Step 5: Save
    print(f"""
💾 Step 5: Save to InstantDB
{LINE_H * 40}
   Will create:
     • 1 Video entity
     • 1 TranscriptionRun with word timestamps
     • 1 DiarizationRun with speaker segments
     • SpeakerAssignment records (if identification run)
   
   📁 Implementation: ingestion/instant_client.py → instant_server.ts
   🔧 Uses: TypeScript server wrapping InstantDB Admin SDK
   
   Why InstantDB?
   • Real-time sync to UI (WebSocket)
   • Official TypeScript SDK (reliable)
   • Schema validation and relationships
""")
    
    # Final command
    print(f"""
{BOX_H * 72}
📋 To execute this pipeline, run:
{BOX_H * 72}

uv run audio_ingestion.py ingest \\
  "{config.source}" \\
  --start-time {config.start_time} \\
  {'--end-time ' + str(config.end_time) + ' \\' if config.end_time else ''}
  {'--title "' + config.title + '" \\' if config.title else ''}
  --workflow {config.workflow}

{BOX_H * 72}
""")


def _get_speaker_info() -> str:
    """Try to get speaker info from postgres."""
    try:
        import psycopg
        
        conn = psycopg.connect(
            "postgresql://diarization:diarization_dev@localhost:5433/speaker_embeddings",
            connect_timeout=2
        )
        cursor = conn.cursor()
        cursor.execute("""
            SELECT speaker_id, COUNT(*) as count 
            FROM speaker_embeddings 
            WHERE speaker_id IS NOT NULL AND speaker_id != 'UNKNOWN'
            GROUP BY speaker_id 
            ORDER BY count DESC
        """)
        results = cursor.fetchall()
        conn.close()
        
        if results:
            total = sum(r[1] for r in results)
            lines = [f"   Known speakers: {total} embeddings across {len(results)} speakers"]
            for speaker_id, count in results[:5]:
                lines.append(f"     • {speaker_id}: {count} embeddings")
            if len(results) > 5:
                lines.append(f"     • ... and {len(results) - 5} more")
            return "\n".join(lines)
        else:
            return "   Known speakers: 0 embeddings (database is empty)"
    except Exception as e:
        # Log the actual error for debugging
        return f"   Known speakers: (PostgreSQL error: {type(e).__name__}: {str(e)[:50]})"


def _extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL."""
    import re
    
    # YouTube patterns
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([^&\n?#]+)',
        r'youtube\.com/embed/([^&\n?#]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # Fall back to URL hash
    import hashlib
    return hashlib.md5(url.encode()).hexdigest()[:11]


def _print_execute_command(command: str, audio_path: Path, config: Union[TranscribeConfig, DiarizeConfig]) -> None:
    """Print the command to execute."""
    print(f"""
{BOX_H * 72}
📋 To execute, run:
{BOX_H * 72}

uv run audio_ingestion.py {command} \\
  "{audio_path}" \\
  --start-time {config.start_time} \\
  {'--end-time ' + str(config.end_time) if config.end_time else ''}

{BOX_H * 72}
""")


def print_dry_run_output(config: Union[IngestConfig, TranscribeConfig, DiarizeConfig, IdentifyConfig]) -> None:
    """
    Print dry-run output for any config type.
    
    Args:
        config: Configuration object
    """
    if isinstance(config, IngestConfig):
        print_ingest_dry_run(config)
    elif isinstance(config, TranscribeConfig):
        print_transcribe_dry_run(config)
    elif isinstance(config, DiarizeConfig):
        print_diarize_dry_run(config)
    elif isinstance(config, IdentifyConfig):
        print_identify_dry_run(config)
    else:
        print(f"⚠️  Dry-run not implemented for {type(config).__name__}")

