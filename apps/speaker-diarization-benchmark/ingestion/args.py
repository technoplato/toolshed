"""
WHO:
  Antigravity
  (Context: Audio Ingestion System)

WHAT:
  Argument parsing logic for the audio ingestion CLI.

WHEN:
  2025-12-03

WHERE:
  apps/speaker-diarization-benchmark/ingestion/args.py

WHY:
  To handle command-line arguments and convert them into configuration objects.
"""

import argparse
from pathlib import Path
from pathlib import Path
from typing import Union
from .config import IngestionConfig, WorkflowConfig, DownloadConfig

def parse_args() -> Union[IngestionConfig, DownloadConfig]:
    parser = argparse.ArgumentParser(description="Audio Ingestion CLI")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Diarize command (maps to old benchmark functionality)
    diarize_parser = subparsers.add_parser("diarize", help="Run diarization/benchmarking workflow")
    diarize_parser.add_argument("clip_path", type=str, help="Path to the audio clip.")
    diarize_parser.add_argument("--workflow", type=str, default="pyannote", 
                                choices=WORKFLOW_CHOICES, 
                                help="Embedding/Diarization workflow to use.")
    
    # Workflow specific args
    diarize_parser.add_argument("--threshold", type=float, default=0.5, help="Cosine distance threshold for segmentation.")
    diarize_parser.add_argument("--window", type=int, default=0, help="Number of context words on each side (0 = no window).")
    diarize_parser.add_argument("--cluster-threshold", type=float, default=0.5, help="Clustering distance threshold.")
    diarize_parser.add_argument("--id-threshold", type=float, default=0.4, help="Identification distance threshold.")
    
    # Global/Output args
    diarize_parser.add_argument("--output-dir", type=str, default=".", help="Directory to save the output text file.")
    diarize_parser.add_argument("--append-to", type=str, help="Path to an existing file to append results to.")
    diarize_parser.add_argument("--identify", action="store_true", help="Run speaker identification using local embeddings.")
    diarize_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing identifications in output.")
    diarize_parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging.")
    diarize_parser.add_argument("--dry-run", action="store_true", help="Simulate actions.")

    # Download command
    download_parser = subparsers.add_parser(
        "download", 
        help="Download video using yt-dlp",
        description="Download a video from a URL using yt-dlp. Check the logs for progress. The video will be saved to the specified output directory. If the video already exists, it will be skipped."
    )
    download_parser.add_argument("url", type=str, help="URL of the video to download.")
    download_parser.add_argument("--output-dir", type=str, default=".", help="Directory to save the downloaded video. Defaults to current directory. Filename format: 'Title [ID].ext'.")
    download_parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging.")
    download_parser.add_argument("--dry-run", action="store_true", help="Simulate actions without downloading.")

    args = parser.parse_args()
    
    if args.command == "diarize":
        workflow_config = WorkflowConfig(
            name=args.workflow,
            threshold=args.threshold,
            window=args.window,
            cluster_threshold=args.cluster_threshold,
            id_threshold=args.id_threshold
        )
        
        return IngestionConfig(
            clip_path=Path(args.clip_path).resolve(),
            workflow=workflow_config,
            output_dir=Path(args.output_dir),
            append_to=Path(args.append_to) if args.append_to else None,
            identify=args.identify,
            overwrite=args.overwrite,
            verbose=args.verbose,
            dry_run=args.dry_run
        )
    elif args.command == "download":
        return DownloadConfig(
            url=args.url,
            output_dir=Path(args.output_dir),
            verbose=args.verbose,
            dry_run=args.dry_run
        )
    else:
        parser.print_help()
        exit(1)

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

def get_workflow(config: WorkflowConfig):
    if config.name == "pyannote":
        # Default to 3.1
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
