"""
WHO:
  Antigravity
  (Context: Audio Ingestion System)

WHAT:
  Configuration objects using Pydantic for the audio ingestion pipeline.
  
  [Classes]
  - WorkflowConfig: Settings for specific diarization workflows (thresholds, models).
  - IngestionConfig: Settings for the main ingestion process (input paths, flags).
  - DownloadConfig: Settings for the video download process (URL, output).

  [Inputs]
  - None (these are data structures)

  [Outputs]
  - Pydantic models for type-safe configuration.

WHEN:
  2025-12-03
  Last Modified: 2025-12-05
  Change Log:
  - 2025-12-05: Added `DownloadConfig` class.

WHERE:
  apps/speaker-diarization-benchmark/ingestion/config.py

WHY:
  To provide a structured, type-safe, and immutable way to pass configuration around the system,
  leveraging Pydantic for validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from pathlib import Path

class WorkflowConfig(BaseModel):
    name: str
    threshold: float = 0.5
    window: int = 0
    cluster_threshold: float = 0.5
    id_threshold: float = 0.4
    model_name: Optional[str] = None
    min_speakers: Optional[int] = None
    max_speakers: Optional[int] = None

class IngestionConfig(BaseModel):
    clip_path: Path
    workflow: WorkflowConfig
    output_dir: Path = Path(".")
    append_to: Optional[Path] = None
    identify: bool = False
    overwrite: bool = False
    verbose: bool = False
    dry_run: bool = False

class DownloadConfig(BaseModel):
    url: str
    output_dir: Path = Path(".")
    verbose: bool = False
    dry_run: bool = False

class ServerConfig(BaseModel):
    port: int = 8000
    host: str = "0.0.0.0"
    verbose: bool = False

