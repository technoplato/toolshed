"""
HOW:
  Import to type-hint the repository dependency.
  `from src.data.repository import VideoAnalysisRepository`
  
  [Inputs]
  - None (Abstract Base Class)

  [Outputs]
  - Interface definition.

WHO:
  Antigravity, User
  (Context: Defining strict contract for data access)

WHAT:
  Abstract Base Class that defines the standard operations for the Video Analysis pipeline.
  All data storage backends (JSON, InstantDB, Postgres) must implement this interface.
  
  Methods cover:
  - Video retrieval/storage
  - Transcription/Diarization run management
  - Segment retrieval (Stable & Dynamic)
  - Speaker & Embedding management

WHEN:
  2025-12-05

WHERE:
  apps/speaker-diarization-benchmark/src/data/repository.py

WHY:
  To decouple the application logic (benchmarking, UI) from the underlying storage mechanism.
  This allows us to seamlessly swap between the legacy JSON file and the production Database
  without rewriting the core business logic.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np
from .models import (
    Video, 
    TranscriptionRun, 
    DiarizationRun, 
    TranscriptionSegment, 
    DiarizationSegment, 
    StableSegment, 
    CorrectedSegment,
    Speaker,
    ShazamMatch
)

class VideoAnalysisRepository(ABC):
    
    # -------------------------------------------------------------------------
    # Video Operations
    # -------------------------------------------------------------------------
    @abstractmethod
    def get_video(self, video_id: str) -> Optional[Video]:
        """Retrieve a video by its internal ID (UUID)."""
        raise NotImplementedError
        
    @abstractmethod
    def get_video_by_external_id(self, external_id: str) -> Optional[Video]:
        """Retrieve a video by its external ID (e.g. YouTube ID)."""
        raise NotImplementedError

    @abstractmethod
    def get_video_by_url(self, url: str) -> Optional[Video]:
        """Retrieve a video by its external URL."""
        raise NotImplementedError

    @abstractmethod
    def save_video(self, video: Video) -> str:
        """Persist a video and ensure internal consistency (e.g. anchors)."""
        raise NotImplementedError
        
    @abstractmethod
    def delete_video(self, video_id: str):
        """Delete a video and CASCADINGLY delete its related entities (Runs, Segments, etc.)."""
        raise NotImplementedError
        
    @abstractmethod
    def wipe_database(self):
        """Delete ALL entities in the database (Nuclear option)."""
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # Analysis Run Operations
    # -------------------------------------------------------------------------
    @abstractmethod
    def save_transcription_run(self, run: TranscriptionRun, segments: List[TranscriptionSegment]) -> str:
        """Save a transcription run and its associated segments."""
        raise NotImplementedError
        
    @abstractmethod
    def get_transcription_run(self, run_id: str) -> Optional[TranscriptionRun]:
        raise NotImplementedError
        
    @abstractmethod
    def get_transcription_segments_by_run_id(self, run_id: str) -> List[TranscriptionSegment]:
        raise NotImplementedError

    @abstractmethod
    def save_diarization_run(self, run: DiarizationRun, segments: List[DiarizationSegment]) -> str:
        """Save a diarization run and its associated segments."""
        raise NotImplementedError

    @abstractmethod
    def get_diarization_run(self, run_id: str) -> Optional[DiarizationRun]:
        raise NotImplementedError
        
    @abstractmethod
    def get_diarization_segments_by_run_id(self, run_id: str) -> List[DiarizationSegment]:
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # Stable Segments & Corrections
    # -------------------------------------------------------------------------
    @abstractmethod
    def get_stable_segments_by_video_id(self, video_id: str, start: float = 0, end: float = None) -> List[StableSegment]:
        """Get stable segments overlapping a time range."""
        raise NotImplementedError
        
    @abstractmethod
    def save_corrected_segment(self, segment: CorrectedSegment) -> str:
        """Save a manual correction."""
        raise NotImplementedError
        
    @abstractmethod
    def get_corrected_segments_by_video_id(self, video_id: str) -> List[CorrectedSegment]:
        """Get all corrections for a video."""
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # Speaker & Embeddings
    # -------------------------------------------------------------------------
    @abstractmethod
    def get_speaker(self, speaker_id: str) -> Optional[Speaker]:
        raise NotImplementedError
        
    @abstractmethod
    def save_speaker(self, speaker: Speaker) -> str:
        raise NotImplementedError
        
    @abstractmethod
    def search_speakers(self, embedding: np.ndarray, threshold: float = 0.5) -> List[Speaker]:
        """Find speakers with similar embeddings."""
        raise NotImplementedError
        
    @abstractmethod
    def save_speaker_embedding(self, speaker_id: str, embedding: np.ndarray):
        """Store the high-dimensional vector for a speaker."""
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # Shazam / Audio Fingerprinting
    # -------------------------------------------------------------------------
    @abstractmethod
    def save_shazam_match(self, match: ShazamMatch) -> str:
        raise NotImplementedError
        
    @abstractmethod
    def get_shazam_matches_by_video_id(self, video_id: str) -> List[ShazamMatch]:
        """Get all recognized music tracks for a video."""
        raise NotImplementedError
