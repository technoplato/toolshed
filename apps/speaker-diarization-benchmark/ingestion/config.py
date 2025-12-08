"""
HOW:
  from ingestion.config import TranscribeConfig, DiarizeConfig, IdentifyConfig, IngestConfig

  # Create configs directly or via parse_args()
  config = TranscribeConfig(
      audio_path=Path("audio.wav"),
      start_time=0,
      end_time=240,
  )

  [Inputs]
  - None (these are data structures)

  [Outputs]
  - Pydantic models for type-safe configuration

WHO:
  Antigravity, Claude AI
  (Context: Audio Ingestion System)

WHAT:
  Configuration objects using Pydantic for the audio ingestion pipeline.
  
  [Classes]
  - WorkflowConfig: Settings for specific diarization workflows (thresholds, models)
  - TranscribeConfig: Settings for transcription (audio path, time range, model)
  - DiarizeConfig: Settings for diarization (audio path, time range, workflow)
  - IdentifyConfig: Settings for speaker identification (video ID, threshold)
  - IngestConfig: Settings for full pipeline (URL/path, all options)
  - DownloadConfig: Settings for video download (URL, output dir)
  - ServerConfig: Settings for Ground Truth server

WHEN:
  2025-12-03
  Last Modified: 2025-12-08
  Change Log:
  - 2025-12-05: Added DownloadConfig class
  - 2025-12-08: Added TranscribeConfig, IdentifyConfig, IngestConfig with time range

WHERE:
  apps/speaker-diarization-benchmark/ingestion/config.py

WHY:
  To provide a structured, type-safe, and immutable way to pass configuration
  around the system, leveraging Pydantic for validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Union
from pathlib import Path


class WorkflowConfig(BaseModel):
    """Configuration for diarization workflows."""
    name: str
    threshold: float = 0.5
    window: int = 0
    cluster_threshold: float = 0.5
    id_threshold: float = 0.4
    model_name: Optional[str] = None
    min_speakers: Optional[int] = None
    max_speakers: Optional[int] = None


class TranscribeConfig(BaseModel):
    """
    Configuration for transcription command.
    
    Attributes:
        audio_path: Path to the audio file
        start_time: Start time in seconds (default: 0)
        end_time: End time in seconds (None = full file)
        runner: Transcription runner to use
        model: Model name/path
        dry_run: Show what would happen without executing
        verbose: Enable verbose logging
    """
    audio_path: Path
    start_time: float = 0
    end_time: Optional[float] = None
    runner: str = "mlx-whisper"
    model: str = "mlx-community/whisper-large-v3-turbo"
    dry_run: bool = False
    verbose: bool = False
    
    class Config:
        arbitrary_types_allowed = True


class DiarizeConfig(BaseModel):
    """
    Configuration for diarization command (replaces IngestionConfig).
    
    Attributes:
        audio_path: Path to the audio file
        start_time: Start time in seconds
        end_time: End time in seconds (None = full file)
        workflow: Workflow configuration
        pipeline: PyAnnote pipeline name
        dry_run: Show what would happen without executing
        verbose: Enable verbose logging
    """
    audio_path: Path
    start_time: float = 0
    end_time: Optional[float] = None
    workflow: WorkflowConfig = Field(default_factory=lambda: WorkflowConfig(name="pyannote"))
    pipeline: str = "pyannote/speaker-diarization-3.1"
    dry_run: bool = False
    verbose: bool = False
    
    class Config:
        arbitrary_types_allowed = True


class IdentifyConfig(BaseModel):
    """
    Configuration for speaker identification command.
    
    Attributes:
        video_id: InstantDB video UUID
        start_time: Start time in seconds
        end_time: End time in seconds (None = full file)
        threshold: KNN distance threshold for identification
        top_k: Number of nearest neighbors to consider
        audio_path: Optional audio file path (auto-detected from video)
        execute: Actually save results (default is dry-run)
        verbose: Enable verbose logging
    """
    video_id: str
    start_time: float = 0
    end_time: Optional[float] = None
    threshold: float = 0.5
    top_k: int = 5
    audio_path: Optional[Path] = None
    execute: bool = False
    verbose: bool = False
    
    class Config:
        arbitrary_types_allowed = True


class IngestConfig(BaseModel):
    """
    Configuration for the full ingestion pipeline.
    
    Attributes:
        source: URL or local path to audio/video
        start_time: Start time in seconds
        end_time: End time in seconds (None = full file)
        title: Video title for InstantDB (auto-detected if URL)
        skip_download: Skip download step (assumes local file)
        skip_identify: Skip speaker identification step
        workflow: Diarization workflow to use
        threshold: KNN threshold for identification
        dry_run: Show plan without running any compute
        preview: Run compute and show what would be saved (without saving)
        yes: Skip confirmation prompt and proceed with save
        verbose: Enable verbose logging
    """
    source: str
    start_time: float = 0
    end_time: Optional[float] = None
    title: Optional[str] = None
    skip_download: bool = False
    skip_identify: bool = False
    workflow: str = "pyannote"
    pipeline: str = "pyannote/speaker-diarization-3.1"
    threshold: float = 0.5
    output_dir: Path = Path("data/clips")
    dry_run: bool = False
    preview: bool = False
    yes: bool = False
    verbose: bool = False
    
    class Config:
        arbitrary_types_allowed = True
    
    @property
    def is_url(self) -> bool:
        """Check if source is a URL."""
        return self.source.startswith(("http://", "https://"))
    
    @property
    def audio_path(self) -> Optional[Path]:
        """Get audio path (only if source is a local file)."""
        if not self.is_url:
            return Path(self.source)
        return None


# Legacy configs (kept for backward compatibility)
class IngestionConfig(BaseModel):
    """
    Legacy configuration for diarization workflow.
    Deprecated: Use DiarizeConfig instead.
    """
    clip_path: Path
    workflow: WorkflowConfig
    output_dir: Path = Path(".")
    append_to: Optional[Path] = None
    identify: bool = False
    overwrite: bool = False
    verbose: bool = False
    dry_run: bool = False
    
    class Config:
        arbitrary_types_allowed = True


class DownloadConfig(BaseModel):
    """Configuration for video download."""
    url: str
    output_dir: Path = Path(".")
    format: str = "wav"
    verbose: bool = False
    dry_run: bool = False
    
    class Config:
        arbitrary_types_allowed = True


class ServerConfig(BaseModel):
    """Configuration for Ground Truth server."""
    port: int = 8000
    host: str = "0.0.0.0"
    verbose: bool = False
