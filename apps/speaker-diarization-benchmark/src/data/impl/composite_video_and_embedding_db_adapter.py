"""
HOW:
  Used internally by DatabaseFactory.
  `repo = CompositeVideoAndEmbeddingDbAdapter({"instant_app_id": "...", "postgres_dsn": "..."})`

  [Inputs]
  - config: Dict with 'instant_app_id', 'instant_api_key', 'postgres_dsn'.

  [Outputs]
  - Repository instance.

WHO:
  Antigravity, User
  (Context: Production-grade data access)

WHAT:
  Implements VideoAnalysisRepository using a hybrid approach:
  - InstantDB (via HTTP API) for high-speed, structural metadata (Videos, Runs, Segments).
  - Postgres (via PgVectorClient) for dense vector embeddings logic.
  
  This splits the concern: InstantDB handles the graph/UI sync, Postgres handles the heavy math.

WHEN:
  2025-12-05

WHERE:
  apps/speaker-diarization-benchmark/src/data/impl/composite_video_and_embedding_db_adapter.py

WHY:
  To provide the robustness of SQL for vectors while keeping the flexibility
  of InstantDB for the frontend.
"""

import requests
import uuid
import numpy as np
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..repository import VideoAnalysisRepository
from ..models import (
    Video, TranscriptionRun, DiarizationRun, 
    TranscriptionSegment, DiarizationSegment, 
    StableSegment, CorrectedSegment, Speaker,
    ShazamMatch
)
from ...embeddings.pgvector_client import PgVectorClient

class CompositeVideoAndEmbeddingDbAdapter(VideoAnalysisRepository):
    
    def __init__(self, config: Dict[str, Any]):
        self.app_id = config.get("instant_app_id")
        self.api_key = config.get("instant_api_key")
        self.api_url = f"https://api.instantdb.com/v1/apps/{self.app_id}"
        
        # Postgres Data Source Name (Connection String)
        # e.g. "postgresql://user:password@localhost:5432/dbname"
        # Used by PgVectorClient to connect to the database.
        dsn = config.get("postgres_dsn")
        self.pg_client = PgVectorClient(dsn) if dsn else None
        
    def _instant_query(self, query: Dict):
        # Placeholder for InstantDB Query/Mutate API
        # Needs actual implementation based on InstantDB REST API docs
        headers = {"Authorization": f"Bearer {self.api_key}"}
        # response = requests.post(f"{self.api_url}/query", json=query, headers=headers)
        # return response.json()
        raise NotImplementedError

    def _instant_transact(self, steps: List[Dict]):
        # Placeholder for transaction
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # Video Operations
    # -------------------------------------------------------------------------
    def get_video(self, video_id: str) -> Optional[Video]:
        # TODO: Implement InstantDB fetch
        return None

    def get_video_by_external_id(self, external_id: str) -> Optional[Video]:
        raise NotImplementedError
        
    def get_video_by_url(self, url: str) -> Optional[Video]:
        raise NotImplementedError

    def save_video(self, video: Video) -> str:
        # TODO: Implement InstantDB mutation
        # self._instant_transact([
        #   {"op": "update", "entity": "videos", "id": video.id, "args": video.dict()}
        # ])
        return video.id
        
    def delete_video(self, video_id: str):
        raise NotImplementedError
        
    def wipe_database(self):
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # Analysis Run Operations
    # -------------------------------------------------------------------------
    def save_transcription_run(self, run: TranscriptionRun, segments: List[TranscriptionSegment]) -> str:
        # 1. Save Run Entity
        # 2. Batch Save Segments
        # 3. Create Links
        return run.id
        
    def get_transcription_run(self, run_id: str) -> Optional[TranscriptionRun]:
        return None
        
    def get_transcription_segments_by_run_id(self, run_id: str) -> List[TranscriptionSegment]:
        return []

    def save_diarization_run(self, run: DiarizationRun, segments: List[DiarizationSegment]) -> str:
        return run.id

    def get_diarization_run(self, run_id: str) -> Optional[DiarizationRun]:
        return None
        
    def get_diarization_segments_by_run_id(self, run_id: str) -> List[DiarizationSegment]:
        return []

    # -------------------------------------------------------------------------
    # Stable Segments & Corrections
    # -------------------------------------------------------------------------
    def get_stable_segments_by_video_id(self, video_id: str, start: float = 0, end: float = None) -> List[StableSegment]:
        return []
        
    def save_corrected_segment(self, segment: CorrectedSegment) -> str:
        return segment.stable_segment_id # Should return Correction ID
        
    def get_corrected_segments_by_video_id(self, video_id: str) -> List[CorrectedSegment]:
        return []

    # -------------------------------------------------------------------------
    # Speaker & Embeddings (Hybrid)
    # -------------------------------------------------------------------------
    def get_speaker(self, speaker_id: str) -> Optional[Speaker]:
        # Fetch metadata from InstantDB
        return None
        
    def save_speaker(self, speaker: Speaker) -> str:
        # Save metadata to InstantDB
        return speaker.id
        
    def search_speakers(self, embedding: np.ndarray, threshold: float = 0.5) -> List[Speaker]:
        # 1. Search Postgres for IDs
        if not self.pg_client: return []
        matches = self.pg_client.search(embedding.tolist(), limit=10)
        
        results = []
        for spk_id, dist in matches:
            if dist < threshold:
                # 2. Fetch Metadata from InstantDB (optimized: batch fetch)
                # spk = self.get_speaker(spk_id)
                results.append(Speaker(id=spk_id, name="TODO")) 
        return results
        
    def save_speaker_embedding(self, speaker_id: str, embedding: np.ndarray):
        """
        Store the high-dimensional vector for a speaker.
        Expected shape: (512,) float32 array (standard Pyannote output).
        """
        if self.pg_client:
            self.pg_client.add_embedding(speaker_id, embedding.tolist())

    # -------------------------------------------------------------------------
    # Shazam Operations
    # -------------------------------------------------------------------------
    def save_shazam_match(self, match: ShazamMatch) -> str:
        # Store metadata in InstantDB (Time, VideoID)
        # Store match data?
        
        # self._instant_transact([...])
        return match.id
        
    def get_shazam_matches_by_video_id(self, video_id: str) -> List[ShazamMatch]:
        # Fetch nested link videoShazamMatches
        return []
