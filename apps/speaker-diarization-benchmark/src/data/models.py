"""
HOW:
  Import these models to type-check data in the analysis pipeline.
  `from src.data.models import Video, TranscriptionRun, Segment`
  
  [Inputs]
  - None (Pydantic definitions)

  [Outputs]
  - Pydantic models for validation.

WHO:
  Antigravity, User
  (Context: Designing robust data model for video analysis)

WHAT:
  Defines the core domain entities for the Video Analysis Pipeline.
  Entities:
  - Video: Metadata about the source file.
  - StableSegment: Immutable 10s time anchors.
  - TranscriptionRun: A specific execution of a STT model.
  - DiarizationRun: A specific execution of a clustering model.
  - TranscriptionSegment: A text prediction tied to a run.
  - DiarizationSegment: A speaker prediction tied to a run.
  - CorrectedSegment: A user-verified truth tied to a StableSegment.
  - Speaker: Identity management.

WHEN:
  2025-12-05

WHERE:
  apps/speaker-diarization-benchmark/src/data/models.py

WHY:
  To provide a single source of truth for data structures, ensuring consistency 
  between the Legacy JSON format and the future InstantDB/Postgres backend.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

# -----------------------------------------------------------------------------
# Base Models
# -----------------------------------------------------------------------------
class BaseEntity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

# -----------------------------------------------------------------------------
# Core Entities
# -----------------------------------------------------------------------------
class Video(BaseEntity):
    title: str
    url: Optional[str] = None
    filepath: Optional[str] = None # Local path
    duration: float
    created_at: datetime = Field(default_factory=datetime.now)
    channel_id: Optional[str] = None
    upload_date: Optional[str] = None # YYYY-MM-DD
    view_count: Optional[int] = None
    
class Speaker(BaseEntity):
    name: str # e.g. "SPEAKER_01" or "Joe Rogan"
    is_labeled: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    # Note: Embedding is not stored here, fetched separately from Vector DB

# -----------------------------------------------------------------------------
# Segment Definitions
# -----------------------------------------------------------------------------
class BaseSegment(BaseModel):
    start: float
    end: float

class TranscriptionSegment(BaseSegment):
    text: str
    confidence: Optional[float] = None
    # No speaker here - strictly what was said

class DiarizationSegment(BaseSegment):
    speaker_id: str
    confidence: Optional[float] = None

class StableSegment(BaseSegment):
    """
    Immutable 10s anchor. index 0 = 0-10s, index 1 = 10-20s.
    """
    video_id: str
    index: int
    
class CorrectedSegment(BaseSegment):
    """
    A manual assertion of truth, linked to a StableSegment anchor.
    """
    stable_segment_id: str
    text: str
    speaker_id: str
    # verification_status?

# -----------------------------------------------------------------------------
# Runs (Execution Metadata)
# -----------------------------------------------------------------------------
class TranscriptionRun(BaseEntity):
    video_id: str
    model: str # e.g. "whisper-large-v3"
    name: str # Unique run name e.g. "benchmark_t0.5_w2"
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Benchmarking Parameters
    segmentation_threshold: Optional[float] = None
    context_window: Optional[int] = None
    
    parameters: Dict[str, Any] = Field(default_factory=dict) # Other params

class DiarizationRun(BaseEntity):
    video_id: str
    transcription_run_id: str # Links to the text this diarization is for
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Benchmarking Parameters
    clustering_threshold: Optional[float] = None
    identification_threshold: Optional[float] = None
    embedding_model: Optional[str] = None
    
    parameters: Dict[str, Any] = Field(default_factory=dict)

# -----------------------------------------------------------------------------
# Audio Fingerprinting (ShazamKit)
# -----------------------------------------------------------------------------
class ShazamMatch(BaseEntity):
    video_id: str
    start_time: float
    end_time: float
    
    shazam_track_id: str
    title: str
    artist: str
    match_offset: float # Where in the song did we match?
    
    created_at: datetime = Field(default_factory=datetime.now)
