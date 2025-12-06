"""
HOW:
  Used internally by DatabaseFactory.
  `repo = LegacyJsonRepository('data/clips/manifest.json', 'data/speaker_embeddings.json')`

  [Inputs]
  - manifest_path: Path to the clips manifest JSON.
  - embeddings_path: Path to the speaker embeddings JSON.

  [Outputs]
  - Repository instance.

WHO:
  Antigravity, User
  (Context: Maintaining backward compatibility)

WHAT:
  Implements the VideoAnalysisRepository interface using local JSON files.
  - Maps `manifest.json` entries to `Video` and `TranscriptionRun`.
  - Maps `speaker_embeddings.json` to `Speaker`.
  - Generates `StableSegment` objects on-the-fly based on video duration (virtual entities).
  - Handles basic persistence by re-writing the JSON files.

WHEN:
  2025-12-05

WHERE:
  apps/speaker-diarization-benchmark/src/data/impl/json_adapter.py

WHY:
  To allow the new application architecture to function with the existing data 
  until the full database migration is complete.
"""

import json
import os
import uuid
import math
import numpy as np
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from ..repository import VideoAnalysisRepository
from ..models import (
    Video, TranscriptionRun, DiarizationRun, 
    TranscriptionSegment, DiarizationSegment, 
    StableSegment, CorrectedSegment, Speaker,
    ShazamMatch
)

class LegacyJsonRepository(VideoAnalysisRepository):
    
    def __init__(self, manifest_path: str, embeddings_path: str):
        self.manifest_path = Path(manifest_path)
        self.embeddings_path = Path(embeddings_path)
        self._ensure_files()
        
    def _ensure_files(self):
        if not self.manifest_path.exists():
            with open(self.manifest_path, 'w') as f:
                json.dump([], f)
        if not self.embeddings_path.exists():
            with open(self.embeddings_path, 'w') as f:
                json.dump({}, f)

    def _load_manifest(self) -> List[Dict]:
        with open(self.manifest_path, 'r') as f:
            return json.load(f)

    def _save_manifest(self, data: List[Dict]):
        with open(self.manifest_path, 'w') as f:
            json.dump(data, f, indent=4)

    def _load_embeddings(self) -> Dict[str, List[List[float]]]:
        if not self.embeddings_path.exists(): return {}
        with open(self.embeddings_path, 'r') as f:
            return json.load(f)

    # -------------------------------------------------------------------------
    # Video Operations
    # -------------------------------------------------------------------------
    def get_video(self, video_id: str) -> Optional[Video]:
        manifest = self._load_manifest()
        entry = next((item for item in manifest if item['id'] == video_id), None)
        if not entry:
            return None
            
        return Video(
            id=entry['id'],
            title=entry.get('title', 'Unknown'),
            url=entry.get('titleUrl'), # Legacy naming
            filepath=entry.get('clip_path'),
            duration=entry.get('duration', 0.0),
            # Infer others or leave default
        )

    def get_video_by_path(self, filepath: str) -> Optional[Video]:
        manifest = self._load_manifest()
        # Loose matching on filename
        fname = Path(filepath).name
        entry = next((item for item in manifest if Path(item.get('clip_path', '')).name == fname), None)
        if not entry:
            return None
        return self.get_video(entry['id'])

    def save_video(self, video: Video) -> str:
        manifest = self._load_manifest()
        # Check if exists
        existing_idx = next((i for i, item in enumerate(manifest) if item['id'] == video.id), -1)
        
        entry = {
            "id": video.id,
            "title": video.title,
            "titleUrl": video.url,
            "clip_path": video.filepath,
            "duration": video.duration,
            "transcriptions": {} # Preserve if exists, handled below
        }
        
        if existing_idx >= 0:
            # Preserve existing specific fields key
            entry['transcriptions'] = manifest[existing_idx].get('transcriptions', {})
            entry['transcription_metadata'] = manifest[existing_idx].get('transcription_metadata', {})
            manifest[existing_idx].update(entry)
        else:
            manifest.append(entry)
            
        self._save_manifest(manifest)
        return video.id

    # -------------------------------------------------------------------------
    # Analysis Run Operations
    # -------------------------------------------------------------------------
    def save_transcription_run(self, run: TranscriptionRun, segments: List[TranscriptionSegment]) -> str:
        manifest = self._load_manifest()
        entry = next((item for item in manifest if item['id'] == run.video_id), None)
        if not entry:
            raise ValueError(f"Video {run.video_id} not found")
            
        # Legacy format stores transcriptions in a dict keyed by run_name
        if 'transcriptions' not in entry:
            entry['transcriptions'] = {}
        if 'transcription_metadata' not in entry:
            entry['transcription_metadata'] = {}
            
        # Convert segments to legacy dict
        legacy_segments = [
            {"start": s.start, "end": s.end, "text": s.text} for s in segments
        ]
        
        entry['transcriptions'][run.name] = legacy_segments
        
        # Save metadata
        metadata = run.parameters.copy()
        metadata.update({
            "model": run.model,
            "created_at": run.created_at.isoformat(),
            "segmentation_threshold": run.segmentation_threshold,
            "context_window": run.context_window
        })
        entry['transcription_metadata'][run.name] = metadata
        
        self._save_manifest(manifest)
        return run.id

    def get_transcription_run(self, run_id: str) -> Optional[TranscriptionRun]:
        # In legacy, run_id is the run NAME (e.g. "benchmark_t0.5")
        # But we need video_id to find it. This is a limitation of the JSON structure.
        # We'll assume the caller knows the video_id or we scan (slow).
        # For this adapter, we might need to parse the composite ID if we start using UUIDs.
        # BUT, the legacy system uses the key as the ID.
        return None # Hard to implement efficiently without video_id context

    def get_transcription_segments(self, run_id: str) -> List[TranscriptionSegment]:
        # See limitation above. This adapter is best used when we know video_id.
        return []

    # Helper method that fits JSON pattern better
    def get_transcriptions_for_video(self, video_id: str) -> List[TranscriptionRun]:
        manifest = self._load_manifest()
        entry = next((item for item in manifest if item['id'] == video_id), None)
        if not entry: return []
        
        runs = []
        meta = entry.get('transcription_metadata', {})
        for key in entry.get('transcriptions', {}).keys():
            m = meta.get(key, {})
            runs.append(TranscriptionRun(
                id=key, # Use key as ID for legacy
                video_id=video_id,
                name=key,
                model=m.get('model', 'unknown'),
                segmentation_threshold=m.get('segmentation_threshold'),
                context_window=m.get('context_window'),
                parameters=m
            ))
        return runs

    def save_diarization_run(self, run: DiarizationRun, segments: List[DiarizationSegment]) -> str:
        # In legacy, diarization is often just mixed into transcriptions or a separate key
        # For strict separation, we'll store it as a new key in 'transcriptions' 
        # but with speaker labels.
        manifest = self._load_manifest()
        entry = next((item for item in manifest if item['id'] == run.video_id), None)
        if not entry: raise ValueError("Video not found")
        
        # For legacy compatibility, we might just overwrite the entry in 'transcriptions'
        # if the run name matches.
        # We will simulate this by storing it in `transcriptions` as usual, since that supports speakers.
        
        if 'transcriptions' not in entry: entry['transcriptions'] = {}
        
        legacy_segments = [
            {"start": s.start, "end": s.end, "speaker": s.speaker_id} for s in segments
        ]
        
        # We need a name for this key. 
        # If run.transcription_run_id is a key, maybe combine them?
        # Ideally, DiarizationRun should have a name too?
        # Using a simple composite key to avoid collision if possible, or just the run ID if it's string friendly
        key = f"{run.transcription_run_id}_diarized"
        if hasattr(run, 'id') and run.id: 
             key = run.id # Use explicit ID if provided
            
        entry['transcriptions'][key] = legacy_segments
        self._save_manifest(manifest)
        return key

    def get_diarization_run(self, run_id: str) -> Optional[DiarizationRun]:
        return None

    def get_diarization_segments(self, run_id: str) -> List[DiarizationSegment]:
        return []

    # -------------------------------------------------------------------------
    # Stable Segments (Virtual)
    # -------------------------------------------------------------------------
    def ensure_stable_segments(self, video_id: str, duration: float):
        # No-op for JSON. We calculate on fly.
        pass

    def get_stable_segments(self, video_id: str, start: float, end: float) -> List[StableSegment]:
        # Generate virtual segments
        # 10s intervals
        s_idx = math.floor(start / 10.0)
        e_idx = math.ceil(end / 10.0)
        
        segments = []
        for i in range(s_idx, e_idx):
            segments.append(StableSegment(
                video_id=video_id,
                index=i,
                start=i * 10.0,
                end=(i + 1) * 10.0
            ))
        return segments

    def save_corrected_segment(self, segment: CorrectedSegment) -> str:
        # We'll validly store this in a new field "corrections" in the video entry
        manifest = self._load_manifest()
        # Find video via stable segment logic parsing
        # Stable ID format: "video_id|index" expected elsewhere, but here we depend on caller knowing video
        # Actually CorrectedSegment doesn't have video_id field in updated model?
        # Let's check models.py... it does NOT.
        # BUT StableSegment has video_id.
        # This implies we must parse video_id from stable_segment_id OR dependency injection.
        # For JSON adapter simplicity, we will assume stable_segment_id is "video_id|index"
        
        parts = segment.stable_segment_id.split("|")
        if len(parts) < 2: 
             # Fallback or error?
             # If we can't find video, we can't save to JSON manifest structure
             raise ValueError(f"Invalid Stable ID {segment.stable_segment_id} for JSON adapter. Expected 'videoid|index'")
        
        vid_id = parts[0]
        
        entry = next((item for item in manifest if item['id'] == vid_id), None)
        if not entry: raise ValueError("Video not found")
        
        if 'corrections' not in entry: entry['corrections'] = []
        
        # Add or Update logic
        # Ideally we replace if same stable_segment and offset?
        # For now, just append
        entry['corrections'].append(segment.dict()) 
        self._save_manifest(manifest)
        return "saved"

    def get_corrected_segments(self, video_id: str) -> List[CorrectedSegment]:
        manifest = self._load_manifest()
        entry = next((item for item in manifest if item['id'] == video_id), None)
        if not entry or 'corrections' not in entry: return []
        
        return [CorrectedSegment(**c) for c in entry['corrections']]

    # -------------------------------------------------------------------------
    # Speakers
    # -------------------------------------------------------------------------
    def get_speaker(self, speaker_id: str) -> Optional[Speaker]:
        # Minimal implementation
        return Speaker(name=speaker_id, id=speaker_id)

    def save_speaker(self, speaker: Speaker) -> str:
        return speaker.id

    def search_speakers(self, embedding: np.ndarray, threshold: float = 0.5) -> List[Speaker]:
        # Brute force cosine search on JSON file
        data = self._load_embeddings()
        results = []
        for name, vectors in data.items():
            if not vectors: continue
            # Average vector
            centroid = np.mean(vectors, axis=0)
            # Cosine distance
            dist = 1 - np.dot(embedding, centroid) / (np.linalg.norm(embedding) * np.linalg.norm(centroid))
            if dist < threshold:
                results.append(Speaker(name=name, id=name))
        return results

    def save_speaker_embedding(self, speaker_id: str, embedding: np.ndarray):
        data = self._load_embeddings()
        if speaker_id not in data:
            data[speaker_id] = []
        data[speaker_id].append(embedding.tolist())
        
        with open(self.embeddings_path, 'w') as f:
            json.dump(data, f)

    # -------------------------------------------------------------------------
    # Shazam Operations
    # -------------------------------------------------------------------------
    def save_shazam_match(self, match: ShazamMatch) -> str:
        manifest = self._load_manifest()
        entry = next((item for item in manifest if item['id'] == match.video_id), None)
        if not entry: raise ValueError("Video not found")
        
        if 'shazam_matches' not in entry:
            entry['shazam_matches'] = []
            
        # Check for duplicate?
        # For now just append
        entry['shazam_matches'].append(match.dict())
        self._save_manifest(manifest)
        return match.id

    def get_shazam_matches(self, video_id: str) -> List[ShazamMatch]:
        manifest = self._load_manifest()
        entry = next((item for item in manifest if item['id'] == video_id), None)
        if not entry: return []
        
        raw_matches = entry.get('shazam_matches', [])
        # Handle conversion if needed (datetime strings, etc)
        # Pydantic v2 handles string->datetime automatically usually
        return [ShazamMatch(**m) for m in raw_matches]
