"""
WHO:
  Antigravity
  (Context: Audio Ingestion System)

WHAT:
  Configuration objects for the audio ingestion pipeline.
  
  [Classes]
  - IngestionConfig: Main configuration object.
  - WorkflowConfig: Configuration for specific workflows.

WHEN:
  2025-12-03

WHERE:
  apps/speaker-diarization-benchmark/ingestion/config.py

WHY:
  To provide a structured way to pass configuration around the system.
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

