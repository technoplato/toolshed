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
  (Context: Schema redesign - Dec 2025)

WHAT:
  Abstract Base Class that defines the standard operations for the Video Analysis pipeline.
  All data storage backends (InstantDB, Postgres) must implement this interface.
  
  Methods cover (New Schema):
  - Publication management
  - Video retrieval/storage
  - Transcription runs with Words
  - Diarization runs with Segments
  - Speaker assignments (history preserved)
  - Word text corrections (history preserved)
  - Shazam matches

WHEN:
  Created: 2025-12-05
  Last Modified: 2025-12-07
  [Change Log:
    - 2025-12-07: Updated for new schema. Removed stable segments, 
                  added words, speaker assignments, segment splits.
  ]

WHERE:
  apps/speaker-diarization-benchmark/src/data/repository.py

WHY:
  To decouple the application logic (benchmarking, UI) from the underlying storage mechanism.
  This allows us to seamlessly swap backends without rewriting the core business logic.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np
from .models import (
    Publication,
    Video,
    TranscriptionRun,
    DiarizationRun,
    Word,
    DiarizationSegment,
    Speaker,
    ShazamMatch,
)


class VideoAnalysisRepository(ABC):
    """
    Abstract interface for video analysis data storage.
    
    Implementations must handle:
    - Entity persistence (InstantDB)
    - Relationship linking
    - Cascading deletes
    - History preservation for corrections
    """

    # =========================================================================
    # Publication Operations
    # =========================================================================

    @abstractmethod
    def save_publication(self, publication: Publication) -> str:
        """Save a publication (YouTube channel, podcast, etc.)."""
        raise NotImplementedError

    @abstractmethod
    def get_publication_by_url(self, url: str) -> Optional[Publication]:
        """Get publication by URL."""
        raise NotImplementedError

    # =========================================================================
    # Video Operations
    # =========================================================================

    @abstractmethod
    def get_video(self, video_id: str) -> Optional[Video]:
        """Retrieve a video by its internal ID (UUID)."""
        raise NotImplementedError

    @abstractmethod
    def get_video_by_url(self, url: str) -> Optional[Video]:
        """Retrieve a video by its external URL."""
        raise NotImplementedError

    @abstractmethod
    def save_video(self, video: Video, publication_id: Optional[str] = None) -> str:
        """
        Persist a video.
        
        Args:
            video: The video to save
            publication_id: Optional publication to link to
        """
        raise NotImplementedError

    @abstractmethod
    def delete_video(self, video_id: str):
        """Delete a video and CASCADE delete related entities."""
        raise NotImplementedError

    @abstractmethod
    def wipe_database(self):
        """Delete ALL entities in the database (Nuclear option)."""
        raise NotImplementedError

    # =========================================================================
    # Transcription Run Operations
    # =========================================================================

    @abstractmethod
    def save_transcription_run(
        self, run: TranscriptionRun, words: List[Word]
    ) -> str:
        """
        Save a transcription run and its words.
        
        Args:
            run: The transcription run metadata
            words: List of Word objects produced by transcription
        """
        raise NotImplementedError

    @abstractmethod
    def get_transcription_run(self, run_id: str) -> Optional[TranscriptionRun]:
        """Get a transcription run by ID."""
        raise NotImplementedError

    @abstractmethod
    def get_words_by_run_id(self, run_id: str) -> List[Word]:
        """Get all words for a transcription run, ordered by start_time."""
        raise NotImplementedError

    # =========================================================================
    # Diarization Run Operations
    # =========================================================================

    @abstractmethod
    def save_diarization_run(
        self, run: DiarizationRun, segments: List[DiarizationSegment]
    ) -> str:
        """
        Save a diarization run and its segments.
        
        Args:
            run: The diarization run metadata
            segments: List of DiarizationSegment objects
        """
        raise NotImplementedError

    @abstractmethod
    def get_diarization_run(self, run_id: str) -> Optional[DiarizationRun]:
        """Get a diarization run by ID."""
        raise NotImplementedError

    @abstractmethod
    def get_diarization_segments_by_run_id(
        self, run_id: str
    ) -> List[DiarizationSegment]:
        """Get all segments for a diarization run, ordered by start_time."""
        raise NotImplementedError

    # =========================================================================
    # Speaker Operations
    # =========================================================================

    @abstractmethod
    def get_speaker(self, speaker_id: str) -> Optional[Speaker]:
        """Get speaker by ID."""
        raise NotImplementedError

    @abstractmethod
    def get_speaker_by_name(self, name: str) -> Optional[Speaker]:
        """Get speaker by name."""
        raise NotImplementedError

    @abstractmethod
    def save_speaker(self, speaker: Speaker) -> str:
        """Save a speaker."""
        raise NotImplementedError

    @abstractmethod
    def search_speakers(
        self, embedding: np.ndarray, threshold: float = 0.5
    ) -> List[Speaker]:
        """Find speakers with similar embeddings (requires pgvector)."""
        raise NotImplementedError

    @abstractmethod
    def save_speaker_embedding(self, speaker_id: str, embedding: np.ndarray):
        """Store embedding for a speaker (requires pgvector)."""
        raise NotImplementedError

    # =========================================================================
    # Speaker Assignment Operations
    # =========================================================================

    @abstractmethod
    def save_speaker_assignment(
        self,
        segment_id: str,
        speaker_id: str,
        source: str,
        assigned_by: str,
        confidence: Optional[float] = None,
        note: Optional[str] = None,
    ) -> str:
        """
        Create a speaker assignment for a diarization segment.
        History is preserved - multiple assignments can exist.
        
        Args:
            segment_id: The diarization segment to assign
            speaker_id: The speaker being assigned
            source: "model" | "user" | "propagated"
            assigned_by: User/system ID making the assignment
            confidence: Optional confidence score
            note: Optional explanation
        """
        raise NotImplementedError

    # =========================================================================
    # Shazam / Audio Fingerprinting
    # =========================================================================

    @abstractmethod
    def save_shazam_match(self, match: ShazamMatch) -> str:
        """Save a music detection result."""
        raise NotImplementedError

    @abstractmethod
    def get_shazam_matches_by_video_id(self, video_id: str) -> List[ShazamMatch]:
        """Get all recognized music tracks for a video."""
        raise NotImplementedError
