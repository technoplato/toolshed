"""
HOW:
  Usage:
  ```python
  from src.data.impl.instant_db_adapter import InstantDBVideoRepository
  import os
  
  repo = InstantDBVideoRepository(
      app_id=os.environ["INSTANT_APP_ID"],
      admin_secret=os.environ["INSTANT_ADMIN_SECRET"]
  )
  repo.save_video(video_obj)
  ```

  [Inputs]
  - app_id: The InstantDB Application ID.
  - admin_secret: The Admin Secret for the app.

  [Outputs]
  - Implements VideoAnalysisRepository interface.

  [Side Effects]
  - Network calls to InstantDB API.

WHO:
  Antigravity, User
  (Context: Schema redesign - Dec 2025)

WHAT:
  A production-grade implementation of VideoAnalysisRepository that persists data
  to InstantDB via the Admin API. Updated to match the new schema design:
  - Words as first-class entities (not buried in JSON)
  - Diarization independent of transcription
  - Speaker assignments with history preservation
  - No more stable segments (replaced by time-based queries)

WHEN:
  Created: 2025-12-05
  Last Modified: 2025-12-07
  [Change Log:
    - 2025-12-07: Complete rewrite for new schema. Removed stable segments,
                  added words, speaker assignments, segment splits.
  ]

WHERE:
  apps/speaker-diarization-benchmark/src/data/impl/instant_db_adapter.py

WHY:
  To provide a robust, persistent storage layer for the benchmarking pipeline.
  The new schema design enables:
  1. Word-level sync with audio playback
  2. Independent transcription and diarization experiments
  3. Full history preservation for corrections
  4. Time-based range queries for speaker attribution
"""

import uuid
import requests
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
import numpy as np

from ..repository import VideoAnalysisRepository
from ..models import (
    Video,
    Publication,
    TranscriptionRun,
    DiarizationRun,
    TranscriptionConfig,
    DiarizationConfig,
    Word,
    DiarizationSegment,
    SpeakerAssignment,
    Speaker,
    ShazamMatch,
    TranscriptionSegment,
)


class InstantDBVideoRepository(VideoAnalysisRepository):
    def __init__(
        self,
        app_id: str,
        admin_secret: str,
        base_url: str = "https://api.instantdb.com/admin",
    ):
        self.app_id = app_id
        self.admin_secret = admin_secret
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {admin_secret}",
            "App-Id": app_id,
        }

    def _transact(self, steps: List[any]) -> Dict[str, Any]:
        """Execute a transaction against InstantDB."""
        if not steps:
            return {}

        resp = requests.post(
            f"{self.base_url}/transact",
            json={"steps": steps},
            headers=self.headers,
            timeout=30,
        )

        if resp.status_code != 200:
            raise Exception(
                f"InstantDB Transaction Failed ({resp.status_code}): {resp.text}"
            )

        return resp.json()

    def _query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an InstaQL query."""
        resp = requests.post(
            f"{self.base_url}/query",
            json={"query": query},
            headers=self.headers,
            timeout=30,
        )
        if resp.status_code != 200:
            raise Exception(
                f"InstantDB Query Failed ({resp.status_code}): {resp.text}"
            )

        return resp.json()

    def _generate_uuid(self, namespace_str: str) -> str:
        """Generate a deterministic UUID from a string."""
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, namespace_str))

    # =========================================================================
    # Publication Operations
    # =========================================================================

    def save_publication(self, publication: Publication) -> str:
        """Save a publication (YouTube channel, podcast, etc.)."""
        pub_uuid = publication.id or self._generate_uuid(publication.url)

        steps = [
            [
                "update",
                "publications",
                pub_uuid,
                {
                    "name": publication.name,
                    "publication_type": publication.publication_type,
                    "url": publication.url,
                    "external_id": publication.external_id,
                    "raw_metadata": publication.raw_metadata,
                    "ingested_at": publication.ingested_at.isoformat(),
                },
            ]
        ]
        self._transact(steps)
        return pub_uuid

    def get_publication_by_url(self, url: str) -> Optional[Publication]:
        """Get publication by URL."""
        q = {"publications": {"$": {"where": {"url": url}}}}
        res = self._query(q)
        data = res.get("publications", [])
        if not data:
            return None

        p = data[0]
        return Publication(
            id=p.get("id"),
            name=p.get("name"),
            publication_type=p.get("publication_type"),
            url=p.get("url"),
            external_id=p.get("external_id"),
            raw_metadata=p.get("raw_metadata"),
        )

    # =========================================================================
    # Video Operations
    # =========================================================================

    def get_video(self, video_id: str) -> Optional[Video]:
        """Get video by internal UUID."""
        q = {"videos": {"$": {"where": {"id": video_id}}}}
        return self._fetch_single_video(q)

    def get_video_by_url(self, url: str) -> Optional[Video]:
        """Get video by URL."""
        q = {"videos": {"$": {"where": {"url": url}}}}
        return self._fetch_single_video(q)

    def _fetch_single_video(self, query: Dict[str, Any]) -> Optional[Video]:
        res = self._query(query)
        data = res.get("videos", [])
        if not data:
            return None

        v = data[0]
        return Video(
            id=v.get("id"),
            title=v.get("title", ""),
            filepath=v.get("filepath"),
            url=v.get("url"),
            duration=v.get("duration"),
            description=v.get("description"),
            external_published_at=v.get("external_published_at"),
            raw_metadata=v.get("raw_metadata"),
        )

    def save_video(self, video: Video, publication_id: Optional[str] = None) -> str:
        """
        Save a video to the database.
        
        Args:
            video: The video to save
            publication_id: Optional publication to link to
        """
        video_uuid = video.id or self._generate_uuid(video.url)

        steps = [
            [
                "update",
                "videos",
                video_uuid,
                {
                    "title": video.title,
                    "url": video.url,
                    "filepath": video.filepath,
                    "duration": video.duration or 0,
                    "description": video.description,
                    "external_published_at": video.external_published_at,
                    "raw_metadata": video.raw_metadata,
                    "ingested_at": video.ingested_at.isoformat(),
                },
            ]
        ]

        if publication_id:
            steps.append(
                ["link", "videos", video_uuid, {"publication": publication_id}]
            )

        self._transact(steps)
        return video_uuid

    def delete_video(self, video_id: str):
        """
        Delete a video and all related entities.
        
        Deletes: transcription runs, diarization runs, words, segments,
        speaker assignments, shazam matches.
        """
        q = {
            "videos": {
                "$": {"where": {"id": video_id}},
                "transcriptionRuns": {"words": {}},
                "diarizationRuns": {"diarizationSegments": {"speakerAssignments": {}}},
                "shazamMatches": {},
            }
        }
        res = self._query(q)
        v_list = res.get("videos", [])
        if not v_list:
            return

        v = v_list[0]
        steps = []

        # Delete words and transcription runs
        for tr in v.get("transcriptionRuns", []):
            for word in tr.get("words", []):
                steps.append(["delete", "words", word["id"]])
            steps.append(["delete", "transcriptionRuns", tr["id"]])

        # Delete speaker assignments, segments, and diarization runs
        for dr in v.get("diarizationRuns", []):
            for seg in dr.get("diarizationSegments", []):
                for sa in seg.get("speakerAssignments", []):
                    steps.append(["delete", "speakerAssignments", sa["id"]])
                steps.append(["delete", "diarizationSegments", seg["id"]])
            steps.append(["delete", "diarizationRuns", dr["id"]])

        # Delete shazam matches
        for match in v.get("shazamMatches", []):
            steps.append(["delete", "shazamMatches", match["id"]])

        # Delete the video itself
        steps.append(["delete", "videos", video_id])

        # Execute in batches
        batch_size = 100
        for i in range(0, len(steps), batch_size):
            self._transact(steps[i : i + batch_size])

    def wipe_database(self):
        """Nuclear option: Delete everything."""
        collections = [
            "publications",
            "videos",
            "speakers",
            "transcriptionConfigs",
            "diarizationConfigs",
            "transcriptionRuns",
            "diarizationRuns",
            "words",
            "diarizationSegments",
            "speakerAssignments",
            "segmentSplits",
            "wordTextCorrections",
            "shazamMatches",
        ]

        steps = []
        for col in collections:
            res = self._query({col: {}})
            items = res.get(col, [])
            for item in items:
                steps.append(["delete", col, item["id"]])

        print(f"Wiping {len(steps)} entities...")
        batch_size = 100
        for i in range(0, len(steps), batch_size):
            self._transact(steps[i : i + batch_size])

    # =========================================================================
    # Transcription Run Operations
    # =========================================================================

    def save_transcription_run(
        self,
        run: TranscriptionRun,
        words: List[Word],
    ) -> str:
        """
        Save a transcription run with all its words.
        
        Args:
            run: The transcription run metadata
            words: List of Word objects produced by the transcription
        """
        video_uuid = run.video_id
        run_uuid = self._generate_uuid(
            f"{video_uuid}_transcription_{run.tool_version}_{run.executed_at.isoformat()}"
        )

        steps = []

        # Save config if provided
        config_uuid = None
        if run.config:
            config_uuid = self._save_transcription_config(run.config, steps)

        # Save run
        steps.append(
            [
                "update",
                "transcriptionRuns",
                run_uuid,
                {
                    "tool_version": run.tool_version,
                    "git_commit_sha": run.git_commit_sha,
                    "pipeline_script": run.pipeline_script,
                    "is_preferred": run.is_preferred,
                    "processing_time_seconds": run.processing_time_seconds,
                    "logs": run.logs,
                    "executed_at": run.executed_at.isoformat(),
                },
            ]
        )

        # Link run to video
        steps.append(["link", "videos", video_uuid, {"transcriptionRuns": run_uuid}])

        # Link run to config
        if config_uuid:
            steps.append(
                ["link", "transcriptionRuns", run_uuid, {"config": config_uuid}]
            )

        # Save words
        for idx, word in enumerate(words):
            word_uuid = self._generate_uuid(f"{run_uuid}_word_{idx}")

            steps.append(
                [
                    "update",
                    "words",
                    word_uuid,
                    {
                        "text": word.text,
                        "start_time": word.start_time,
                        "end_time": word.end_time,
                        "confidence": word.confidence,
                        "transcription_segment_index": word.transcription_segment_index,
                        "ingested_at": word.ingested_at.isoformat(),
                    },
                ]
            )

            # Link word to run
            steps.append(["link", "transcriptionRuns", run_uuid, {"words": word_uuid}])

            # Batch transactions
            if len(steps) >= 100:
                self._transact(steps)
                steps = []

        if steps:
            self._transact(steps)

        return run_uuid

    def _save_transcription_config(
        self, config: TranscriptionConfig, steps: List
    ) -> str:
        """Save transcription config and return its UUID."""
        params_str = json.dumps(config.additional_params or {}, sort_keys=True)
        config_uuid = self._generate_uuid(
            f"transcription_config_{config.model}_{config.tool}_{params_str}"
        )

        steps.append(
            [
                "update",
                "transcriptionConfigs",
                config_uuid,
                {
                    "model": config.model,
                    "tool": config.tool,
                    "language": config.language,
                    "word_timestamps": config.word_timestamps,
                    "vad_filter": config.vad_filter,
                    "beam_size": config.beam_size,
                    "temperature": config.temperature,
                    "additional_params": config.additional_params,
                    "created_at": config.created_at.isoformat(),
                },
            ]
        )

        return config_uuid

    def get_transcription_run(self, run_id: str) -> Optional[TranscriptionRun]:
        """Get a transcription run by ID."""
        q = {
            "transcriptionRuns": {
                "$": {"where": {"id": run_id}},
                "video": {},
                "config": {},
            }
        }
        res = self._query(q)
        data = res.get("transcriptionRuns", [])
        if not data:
            return None

        r = data[0]
        video = r.get("video", [{}])[0] if r.get("video") else {}

        return TranscriptionRun(
            id=r.get("id"),
            video_id=video.get("id", ""),
            tool_version=r.get("tool_version"),
            git_commit_sha=r.get("git_commit_sha"),
            pipeline_script=r.get("pipeline_script"),
            is_preferred=r.get("is_preferred", False),
            processing_time_seconds=r.get("processing_time_seconds"),
            logs=r.get("logs"),
        )

    def get_words_by_run_id(self, run_id: str) -> List[Word]:
        """Get all words for a transcription run."""
        q = {
            "transcriptionRuns": {
                "$": {"where": {"id": run_id}},
                "words": {},
            }
        }
        res = self._query(q)
        runs = res.get("transcriptionRuns", [])
        if not runs:
            return []

        words_data = runs[0].get("words", [])
        words_data.sort(key=lambda x: x.get("start_time", 0))

        return [
            Word(
                id=w.get("id"),
                text=w.get("text"),
                start_time=w.get("start_time"),
                end_time=w.get("end_time"),
                confidence=w.get("confidence"),
                transcription_segment_index=w.get("transcription_segment_index"),
            )
            for w in words_data
        ]

    # =========================================================================
    # Diarization Run Operations
    # =========================================================================

    def save_diarization_run(
        self,
        run: DiarizationRun,
        segments: List[DiarizationSegment],
    ) -> str:
        """
        Save a diarization run with all its segments.
        
        Args:
            run: The diarization run metadata
            segments: List of DiarizationSegment objects
        """
        video_uuid = run.video_id
        run_uuid = self._generate_uuid(
            f"{video_uuid}_diarization_{run.workflow}_{run.executed_at.isoformat()}"
        )

        steps = []

        # Save config if provided
        config_uuid = None
        if run.config:
            config_uuid = self._save_diarization_config(run.config, steps)

        # Save run
        steps.append(
            [
                "update",
                "diarizationRuns",
                run_uuid,
                {
                    "workflow": run.workflow,
                    "tool_version": run.tool_version,
                    "git_commit_sha": run.git_commit_sha,
                    "pipeline_script": run.pipeline_script,
                    "is_preferred": run.is_preferred,
                    "processing_time_seconds": run.processing_time_seconds,
                    "num_speakers_detected": run.num_speakers_detected,
                    "logs": run.logs,
                    "executed_at": run.executed_at.isoformat(),
                },
            ]
        )

        # Link run to video
        steps.append(["link", "videos", video_uuid, {"diarizationRuns": run_uuid}])

        # Link run to config
        if config_uuid:
            steps.append(
                ["link", "diarizationRuns", run_uuid, {"config": config_uuid}]
            )

        # Save segments
        for idx, seg in enumerate(segments):
            seg_uuid = self._generate_uuid(f"{run_uuid}_segment_{idx}")

            steps.append(
                [
                    "update",
                    "diarizationSegments",
                    seg_uuid,
                    {
                        "start_time": seg.start_time,
                        "end_time": seg.end_time,
                        "speaker_label": seg.speaker_label,
                        "embedding_id": seg.embedding_id,
                        "confidence": seg.confidence,
                        "is_invalidated": seg.is_invalidated or False,
                        "created_at": seg.created_at.isoformat(),
                    },
                ]
            )

            # Link segment to run
            steps.append(
                ["link", "diarizationRuns", run_uuid, {"diarizationSegments": seg_uuid}]
            )

            # Batch transactions
            if len(steps) >= 100:
                self._transact(steps)
                steps = []

        if steps:
            self._transact(steps)

        return run_uuid

    def _save_diarization_config(self, config: DiarizationConfig, steps: List) -> str:
        """Save diarization config and return its UUID."""
        params_str = json.dumps(config.additional_params or {}, sort_keys=True)
        config_uuid = self._generate_uuid(
            f"diarization_config_{config.embedding_model}_{config.tool}_{params_str}"
        )

        steps.append(
            [
                "update",
                "diarizationConfigs",
                config_uuid,
                {
                    "embedding_model": config.embedding_model,
                    "tool": config.tool,
                    "clustering_method": config.clustering_method,
                    "cluster_threshold": config.cluster_threshold,
                    "identification_threshold": config.identification_threshold,
                    "additional_params": config.additional_params,
                    "created_at": config.created_at.isoformat(),
                },
            ]
        )

        return config_uuid

    def get_diarization_run(self, run_id: str) -> Optional[DiarizationRun]:
        """Get a diarization run by ID."""
        q = {
            "diarizationRuns": {
                "$": {"where": {"id": run_id}},
                "video": {},
                "config": {},
            }
        }
        res = self._query(q)
        data = res.get("diarizationRuns", [])
        if not data:
            return None

        r = data[0]
        video = r.get("video", [{}])[0] if r.get("video") else {}

        return DiarizationRun(
            id=r.get("id"),
            video_id=video.get("id", ""),
            workflow=r.get("workflow"),
            tool_version=r.get("tool_version"),
            git_commit_sha=r.get("git_commit_sha"),
            pipeline_script=r.get("pipeline_script"),
            is_preferred=r.get("is_preferred", False),
            processing_time_seconds=r.get("processing_time_seconds"),
            num_speakers_detected=r.get("num_speakers_detected"),
            logs=r.get("logs"),
        )

    def get_diarization_segments_by_run_id(
        self, run_id: str
    ) -> List[DiarizationSegment]:
        """Get all segments for a diarization run."""
        q = {
            "diarizationRuns": {
                "$": {"where": {"id": run_id}},
                "diarizationSegments": {"speakerAssignments": {"speaker": {}}},
            }
        }
        res = self._query(q)
        runs = res.get("diarizationRuns", [])
        if not runs:
            return []

        segments_data = runs[0].get("diarizationSegments", [])
        segments_data.sort(key=lambda x: x.get("start_time", 0))

        return [
            DiarizationSegment(
                id=s.get("id"),
                start_time=s.get("start_time"),
                end_time=s.get("end_time"),
                speaker_label=s.get("speaker_label"),
                embedding_id=s.get("embedding_id"),
                confidence=s.get("confidence"),
                is_invalidated=s.get("is_invalidated", False),
            )
            for s in segments_data
        ]

    # =========================================================================
    # Speaker Operations
    # =========================================================================

    def get_speaker(self, speaker_id: str) -> Optional[Speaker]:
        """Get speaker by ID."""
        q = {"speakers": {"$": {"where": {"id": speaker_id}}}}
        res = self._query(q)
        data = res.get("speakers", [])
        if not data:
            return None

        s = data[0]
        return Speaker(
            id=s.get("id"),
            name=s.get("name"),
            is_human=s.get("is_human", True),
            embedding_centroid_id=s.get("embedding_centroid_id"),
            metadata=s.get("metadata"),
        )

    def get_speaker_by_name(self, name: str) -> Optional[Speaker]:
        """Get speaker by name."""
        q = {"speakers": {"$": {"where": {"name": name}}}}
        res = self._query(q)
        data = res.get("speakers", [])
        if not data:
            return None

        s = data[0]
        return Speaker(
            id=s.get("id"),
            name=s.get("name"),
            is_human=s.get("is_human", True),
            embedding_centroid_id=s.get("embedding_centroid_id"),
            metadata=s.get("metadata"),
        )

    def save_speaker(self, speaker: Speaker) -> str:
        """Save a speaker."""
        speaker_uuid = speaker.id or self._generate_uuid(f"speaker_{speaker.name}")

        steps = [
            [
                "update",
                "speakers",
                speaker_uuid,
                {
                    "name": speaker.name,
                    "is_human": speaker.is_human,
                    "embedding_centroid_id": speaker.embedding_centroid_id,
                    "metadata": speaker.metadata,
                    "ingested_at": speaker.ingested_at.isoformat(),
                },
            ]
        ]
        self._transact(steps)
        return speaker_uuid

    def search_speakers(
        self, embedding: np.ndarray, threshold: float = 0.5
    ) -> List[Speaker]:
        """
        Search for speakers by embedding similarity.
        Note: This requires pgvector integration - currently returns empty.
        """
        # TODO: Implement with pgvector
        return []

    def save_speaker_embedding(self, speaker_id: str, embedding: np.ndarray):
        """
        Save speaker embedding to pgvector.
        Note: This requires pgvector integration - currently no-op.
        """
        # TODO: Implement with pgvector
        pass

    # =========================================================================
    # Speaker Assignment Operations
    # =========================================================================

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
        """
        assignment_uuid = self._generate_uuid(
            f"{segment_id}_{speaker_id}_{datetime.now().isoformat()}"
        )

        steps = [
            [
                "update",
                "speakerAssignments",
                assignment_uuid,
                {
                    "source": source,
                    "confidence": confidence,
                    "note": note,
                    "assigned_by": assigned_by,
                    "assigned_at": datetime.now().isoformat(),
                },
            ],
            [
                "link",
                "diarizationSegments",
                segment_id,
                {"speakerAssignments": assignment_uuid},
            ],
            ["link", "speakerAssignments", assignment_uuid, {"speaker": speaker_id}],
        ]

        self._transact(steps)
        return assignment_uuid

    # =========================================================================
    # Shazam Operations
    # =========================================================================

    def save_shazam_match(self, match: ShazamMatch) -> str:
        """Save a Shazam music match."""
        match_uuid = self._generate_uuid(
            f"{match.video_id}_{match.shazam_track_id}_{match.start_time}"
        )

        steps = [
            [
                "update",
                "shazamMatches",
                match_uuid,
                {
                    "start_time": match.start_time,
                    "end_time": match.end_time,
                    "shazam_track_id": match.shazam_track_id,
                    "title": match.title,
                    "artist": match.artist,
                    "match_offset": match.match_offset,
                    "created_at": match.created_at.isoformat(),
                },
            ],
            ["link", "videos", match.video_id, {"shazamMatches": match_uuid}],
        ]

        self._transact(steps)
        return match_uuid

    def get_shazam_matches_by_video_id(self, video_id: str) -> List[ShazamMatch]:
        """Get all Shazam matches for a video."""
        q = {
            "videos": {
                "$": {"where": {"id": video_id}},
                "shazamMatches": {},
            }
        }
        res = self._query(q)
        videos = res.get("videos", [])
        if not videos:
            return []

        matches = videos[0].get("shazamMatches", [])
        return [
            ShazamMatch(
                id=m.get("id"),
                video_id=video_id,
                start_time=m.get("start_time"),
                end_time=m.get("end_time"),
                shazam_track_id=m.get("shazam_track_id"),
                title=m.get("title"),
                artist=m.get("artist"),
                match_offset=m.get("match_offset"),
            )
            for m in matches
        ]

    # =========================================================================
    # Legacy Compatibility Methods
    # =========================================================================

    def save_transcription_run_legacy(
        self,
        run: TranscriptionRun,
        segments: List[TranscriptionSegment],
    ) -> str:
        """
        Legacy method: Save transcription run with segments.
        Converts segments to words internally.
        
        DEPRECATED: Use save_transcription_run with Word objects instead.
        """
        words = []
        for seg_idx, seg in enumerate(segments):
            # If segment has word-level data, use it
            if seg.words:
                for word_data in seg.words:
                    words.append(
                        Word(
                            text=word_data.get("word", word_data.get("text", "")),
                            start_time=word_data.get("start", 0),
                            end_time=word_data.get("end", 0),
                            confidence=word_data.get("probability", word_data.get("confidence")),
                            transcription_segment_index=seg_idx,
                        )
                    )
            else:
                # Create a single word for the whole segment
                words.append(
                    Word(
                        text=seg.text,
                        start_time=seg.start,
                        end_time=seg.end,
                        confidence=seg.confidence,
                        transcription_segment_index=seg_idx,
                    )
                )

        return self.save_transcription_run(run, words)

    # =========================================================================
    # Deprecated Methods (Removed in new schema)
    # =========================================================================

    def get_video_by_external_id(self, external_id: str) -> Optional[Video]:
        """DEPRECATED: Use get_video_by_url instead."""
        target_uuid = self._generate_uuid(external_id)
        return self.get_video(target_uuid)

    def get_stable_segments_by_video_id(self, video_id: str, start: float = 0, end: float = None):
        """DEPRECATED: Stable segments removed in new schema."""
        raise NotImplementedError(
            "Stable segments have been removed. Use time-based range queries on words/segments instead."
        )

    def save_corrected_segment(self, segment):
        """DEPRECATED: Use word text corrections or speaker assignments instead."""
        raise NotImplementedError(
            "Corrected segments removed. Use WordTextCorrection for text or SpeakerAssignment for speaker corrections."
        )

    def get_corrected_segments_by_video_id(self, video_id: str):
        """DEPRECATED: Query word text corrections or speaker assignments instead."""
        raise NotImplementedError(
            "Corrected segments removed. Query wordTextCorrections or speakerAssignments instead."
        )

    def get_transcription_segments_by_run_id(self, run_id: str) -> List[TranscriptionSegment]:
        """DEPRECATED: Use get_words_by_run_id instead."""
        words = self.get_words_by_run_id(run_id)
        
        # Group words by segment index
        segments_dict: Dict[int, List[Word]] = {}
        for word in words:
            idx = word.transcription_segment_index or 0
            if idx not in segments_dict:
                segments_dict[idx] = []
            segments_dict[idx].append(word)
        
        # Convert to TranscriptionSegment format
        segments = []
        for idx in sorted(segments_dict.keys()):
            seg_words = segments_dict[idx]
            segments.append(
                TranscriptionSegment(
                    start=seg_words[0].start_time,
                    end=seg_words[-1].end_time,
                    text=" ".join(w.text for w in seg_words),
                    words=[
                        {
                            "word": w.text,
                            "start": w.start_time,
                            "end": w.end_time,
                            "probability": w.confidence,
                        }
                        for w in seg_words
                    ],
                )
            )
        
        return segments
