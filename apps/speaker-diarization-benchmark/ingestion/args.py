"""
HOW:
  from ingestion.args import parse_args
  
  config = parse_args()
  # Returns one of: TranscribeConfig, DiarizeConfig, IdentifyConfig, 
  #                 IngestConfig, DownloadConfig, ServerConfig

  [Commands]
  - transcribe <audio_path> [--start-time N] [--end-time N]
  - diarize <audio_path> [--start-time N] [--end-time N] [--workflow W]
  - identify <video_id> [--start-time N] [--end-time N] [--threshold T]
  - ingest <URL_or_path> [--start-time N] [--end-time N] [--title T]
  - download <URL> [--output-dir D]
  - server start [--port P]

  [Inputs]
  - Command line arguments (sys.argv)

  [Outputs]
  - Config object for the requested command

  [Side Effects]
  - Prints help message and exits if arguments are invalid

WHO:
  Antigravity, Claude AI
  (Context: Audio Ingestion System)

WHAT:
  Argument parsing logic for the audio ingestion CLI.
  Converts command-line arguments into structured configuration objects.

WHEN:
  2025-12-03
  Last Modified: 2025-12-08
  Change Log:
  - 2025-12-05: Added download subcommand support
  - 2025-12-08: Added transcribe, identify, ingest subcommands with time ranges

WHERE:
  apps/speaker-diarization-benchmark/ingestion/args.py

WHY:
  To handle command-line arguments and convert them into structured configuration
  objects, separating CLI concern from business logic.
"""

import argparse
from pathlib import Path
from typing import Union
from .config import (
    WorkflowConfig,
    TranscribeConfig,
    DiarizeConfig,
    IdentifyConfig,
    IngestConfig,
    IngestionConfig,
    DownloadConfig,
    ServerConfig,
)

# All available workflow choices
WORKFLOW_CHOICES = [
    "pyannote",
    "pyannote_community",
    "pyannote_3.1",
    "pyannote_precision",
    "wespeaker",
    "segment_level",
    "segment_level_matching",
    "segment_level_nearest_neighbor",
    "word_level",
    "whisperplus_diarize",
    "overlapped_speech",
    "deepgram",
    "assemblyai"
]

# Type alias for all config types
ConfigType = Union[
    TranscribeConfig,
    DiarizeConfig,
    IdentifyConfig,
    IngestConfig,
    IngestionConfig,
    DownloadConfig,
    ServerConfig,
]


def parse_args() -> ConfigType:
    """Parse command-line arguments and return appropriate config object."""
    parser = argparse.ArgumentParser(
        description="Audio Ingestion CLI - Process audio for speaker diarization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Transcribe audio
  uv run audio_ingestion.py transcribe audio.wav --start-time 0 --end-time 60

  # Run diarization
  uv run audio_ingestion.py diarize audio.wav --workflow pyannote

  # Identify speakers
  uv run audio_ingestion.py identify --video-id abc123 --threshold 0.4 --execute

  # Full ingestion pipeline
  uv run audio_ingestion.py ingest "https://youtube.com/watch?v=..." --end-time 240

  # Download video
  uv run audio_ingestion.py download "https://youtube.com/watch?v=..." --output-dir data/clips
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # === TRANSCRIBE COMMAND ===
    transcribe_parser = subparsers.add_parser(
        "transcribe",
        help="Transcribe audio with word timestamps",
        description="Transcribe an audio file using MLX Whisper with word-level timestamps.",
    )
    transcribe_parser.add_argument("audio_path", type=str, help="Path to the audio file")
    transcribe_parser.add_argument("--start-time", type=float, default=0, help="Start time in seconds (default: 0)")
    transcribe_parser.add_argument("--end-time", type=float, default=None, help="End time in seconds (default: full file)")
    transcribe_parser.add_argument("--runner", type=str, default="mlx-whisper", help="Transcription runner")
    transcribe_parser.add_argument("--model", type=str, default="mlx-community/whisper-large-v3-turbo", help="Model to use")
    transcribe_parser.add_argument("--dry-run", action="store_true", help="Show what would happen")
    transcribe_parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    # === DIARIZE COMMAND ===
    diarize_parser = subparsers.add_parser(
        "diarize",
        help="Run speaker diarization",
        description="Run speaker diarization on an audio file using PyAnnote or other workflows.",
    )
    diarize_parser.add_argument("audio_path", type=str, help="Path to the audio file")
    diarize_parser.add_argument("--start-time", type=float, default=0, help="Start time in seconds (default: 0)")
    diarize_parser.add_argument("--end-time", type=float, default=None, help="End time in seconds (default: full file)")
    diarize_parser.add_argument("--workflow", type=str, default="pyannote", choices=WORKFLOW_CHOICES, help="Diarization workflow")
    diarize_parser.add_argument("--pipeline", type=str, default="pyannote/speaker-diarization-3.1", help="PyAnnote pipeline")
    diarize_parser.add_argument("--threshold", type=float, default=0.5, help="Segmentation threshold")
    diarize_parser.add_argument("--window", type=int, default=0, help="Context window size")
    diarize_parser.add_argument("--cluster-threshold", type=float, default=0.5, help="Clustering threshold")
    diarize_parser.add_argument("--id-threshold", type=float, default=0.4, help="Identification threshold")
    diarize_parser.add_argument("--min-speakers", type=int, default=None, help="Minimum expected speakers")
    diarize_parser.add_argument("--max-speakers", type=int, default=None, help="Maximum expected speakers")
    diarize_parser.add_argument("--dry-run", action="store_true", help="Show what would happen")
    diarize_parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    # Legacy diarize args (for backward compatibility)
    diarize_parser.add_argument("--output-dir", type=str, default=".", help="Output directory (legacy)")
    diarize_parser.add_argument("--append-to", type=str, help="Append results to file (legacy)")
    diarize_parser.add_argument("--identify", action="store_true", help="Run identification (legacy)")
    diarize_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing (legacy)")

    # === IDENTIFY COMMAND ===
    identify_parser = subparsers.add_parser(
        "identify",
        help="Identify speakers via KNN search",
        description="Identify speakers in diarization segments by comparing voice embeddings.",
    )
    identify_parser.add_argument("--video-id", type=str, required=True, help="InstantDB video UUID")
    identify_parser.add_argument("--start-time", type=float, default=0, help="Start time in seconds (default: 0)")
    identify_parser.add_argument("--end-time", type=float, default=None, help="End time in seconds (default: full file)")
    identify_parser.add_argument("--threshold", type=float, default=0.5, help="KNN distance threshold (default: 0.5)")
    identify_parser.add_argument("--top-k", type=int, default=5, help="Number of nearest neighbors (default: 5)")
    identify_parser.add_argument("--audio-path", type=str, default=None, help="Audio file path (auto-detected if omitted)")
    identify_parser.add_argument("--execute", action="store_true", help="Save results (default is dry-run)")
    identify_parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    # === INGEST COMMAND ===
    ingest_parser = subparsers.add_parser(
        "ingest",
        help="Full pipeline: download → transcribe → diarize → identify",
        description="""
Run the complete audio ingestion pipeline:
1. Download (if URL provided)
2. Transcribe with MLX Whisper
3. Diarize with PyAnnote
4. Identify speakers (included by default, use --skip-identify to skip)
5. Save to InstantDB
        """,
    )
    ingest_parser.add_argument("source", type=str, help="Video URL or local audio file path")
    ingest_parser.add_argument("--start-time", type=float, default=0, help="Start time in seconds (default: 0)")
    ingest_parser.add_argument("--end-time", type=float, default=None, help="End time in seconds (default: full file)")
    ingest_parser.add_argument("--title", type=str, default=None, help="Video title for InstantDB (auto-detected if URL)")
    ingest_parser.add_argument("--skip-identify", action="store_true", help="Skip speaker identification step")
    ingest_parser.add_argument("--workflow", type=str, default="pyannote", choices=WORKFLOW_CHOICES, help="Diarization workflow")
    ingest_parser.add_argument("--pipeline", type=str, default="pyannote/speaker-diarization-3.1", help="PyAnnote pipeline")
    ingest_parser.add_argument("--threshold", type=float, default=0.5, help="KNN identification threshold")
    ingest_parser.add_argument("--output-dir", type=str, default="data/clips", help="Download output directory")
    ingest_parser.add_argument("--dry-run", action="store_true", help="Show what would happen")
    ingest_parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    # === DOWNLOAD COMMAND ===
    download_parser = subparsers.add_parser(
        "download",
        help="Download video using yt-dlp",
        description="Download a video from a URL using yt-dlp.",
    )
    download_parser.add_argument("url", type=str, help="URL of the video to download")
    download_parser.add_argument("--output-dir", type=str, default="data/clips", help="Output directory")
    download_parser.add_argument("--format", type=str, default="wav", help="Output format (wav, mp3)")
    download_parser.add_argument("--dry-run", action="store_true", help="Show what would happen")
    download_parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    # === SERVER COMMAND ===
    server_parser = subparsers.add_parser("server", help="Start the Ground Truth server")
    server_subparsers = server_parser.add_subparsers(dest="server_command", help="Server action")
    
    server_start_parser = server_subparsers.add_parser("start", help="Start the server")
    server_start_parser.add_argument("--port", type=int, default=8000, help="Port to run on")
    server_start_parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()
    
    # Handle each command
    if args.command == "transcribe":
        return TranscribeConfig(
            audio_path=Path(args.audio_path).resolve(),
            start_time=args.start_time,
            end_time=args.end_time,
            runner=args.runner,
            model=args.model,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )
    
    elif args.command == "diarize":
        workflow_config = WorkflowConfig(
            name=args.workflow,
            threshold=args.threshold,
            window=args.window,
            cluster_threshold=args.cluster_threshold,
            id_threshold=args.id_threshold,
            min_speakers=args.min_speakers,
            max_speakers=args.max_speakers,
        )
        
        # Check if using legacy mode (has identify flag)
        if args.identify or args.append_to:
            return IngestionConfig(
                clip_path=Path(args.audio_path).resolve(),
                workflow=workflow_config,
                output_dir=Path(args.output_dir),
                append_to=Path(args.append_to) if args.append_to else None,
                identify=args.identify,
                overwrite=args.overwrite,
                verbose=args.verbose,
                dry_run=args.dry_run,
            )
        
        return DiarizeConfig(
            audio_path=Path(args.audio_path).resolve(),
            start_time=args.start_time,
            end_time=args.end_time,
            workflow=workflow_config,
            pipeline=args.pipeline,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )
    
    elif args.command == "identify":
        return IdentifyConfig(
            video_id=args.video_id,
            start_time=args.start_time,
            end_time=args.end_time,
            threshold=args.threshold,
            top_k=args.top_k,
            audio_path=Path(args.audio_path) if args.audio_path else None,
            execute=args.execute,
            verbose=args.verbose,
        )
    
    elif args.command == "ingest":
        return IngestConfig(
            source=args.source,
            start_time=args.start_time,
            end_time=args.end_time,
            title=args.title,
            skip_identify=args.skip_identify,
            workflow=args.workflow,
            pipeline=args.pipeline,
            threshold=args.threshold,
            output_dir=Path(args.output_dir),
            dry_run=args.dry_run,
            verbose=args.verbose,
        )
    
    elif args.command == "download":
        return DownloadConfig(
            url=args.url,
            output_dir=Path(args.output_dir),
            format=args.format,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )
    
    elif args.command == "server" and args.server_command == "start":
        return ServerConfig(
            port=args.port,
            verbose=args.verbose,
        )
    
    else:
        parser.print_help()
        exit(1)


def get_workflow(config: WorkflowConfig):
    """
    Get the workflow instance for a given configuration.
    
    Args:
        config: WorkflowConfig with the workflow name and parameters
        
    Returns:
        Instantiated workflow object
    """
    if config.name == "pyannote":
        from .workflows.local.pyannote import PyannoteWorkflow
        config.model_name = "pyannote/speaker-diarization-3.1"
        return PyannoteWorkflow(config.dict())
    elif config.name == "pyannote_3.1":
        from .workflows.local.pyannote import PyannoteWorkflow
        config.model_name = "pyannote/speaker-diarization-3.1"
        return PyannoteWorkflow(config.dict())
    elif config.name == "pyannote_community":
        from .workflows.local.pyannote import PyannoteWorkflow
        config.model_name = "pyannote/speaker-diarization-community-1"
        return PyannoteWorkflow(config.dict())
    elif config.name == "pyannote_precision":
        from .workflows.local.pyannote import PyannoteWorkflow
        config.model_name = "pyannote/speaker-diarization-precision-2"
        return PyannoteWorkflow(config.dict())
    elif config.name == "wespeaker":
        from .workflows.local.wespeaker import WeSpeakerWorkflow
        return WeSpeakerWorkflow(config.dict())
    elif config.name == "segment_level":
        from .workflows.local.segment_level import SegmentLevelWorkflow
        return SegmentLevelWorkflow(config.dict())
    elif config.name == "segment_level_matching":
        from .workflows.local.segment_level import SegmentLevelMatchingWorkflow
        return SegmentLevelMatchingWorkflow(config.dict())
    elif config.name == "segment_level_nearest_neighbor":
        from .workflows.local.segment_level import SegmentLevelNearestNeighborWorkflow
        return SegmentLevelNearestNeighborWorkflow(config.dict())
    elif config.name == "word_level":
        from .workflows.local.word_level import WordLevelWorkflow
        return WordLevelWorkflow(config.dict())
    elif config.name == "whisperplus_diarize":
        from .workflows.local.whisperplus import WhisperPlusDiarizeWorkflow
        return WhisperPlusDiarizeWorkflow(config.dict())
    elif config.name == "overlapped_speech":
        from .workflows.local.overlapped_speech import OverlappedSpeechDetectionWorkflow
        return OverlappedSpeechDetectionWorkflow(config.dict())
    elif config.name == "deepgram":
        from .workflows.api.deepgram import DeepgramWorkflow
        return DeepgramWorkflow(config.dict())
    elif config.name == "assemblyai":
        from .workflows.api.assemblyai import AssemblyAIWorkflow
        return AssemblyAIWorkflow(config.dict())
    else:
        raise ValueError(f"Unknown workflow: {config.name}")
