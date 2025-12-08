"""
HOW:
  from ingestion.cache import (
      TranscriptionCache,
      DiarizationCache,
      IdentificationCache,
      PreviewCache,
      extract_video_id,
  )
  
  # Check if transcription is cached for a range
  cache = TranscriptionCache(video_id, tool, model)
  if cache.has_range(start_time=10, end_time=50):
      result = cache.get_filtered(start_time=10, end_time=50)
  else:
      result = transcribe(...)
      cache.save(result, end_time=50)

  [Inputs]
  - video_id: Extracted from URL or filename
  - Various config options (tool, model, workflow, threshold, etc.)

  [Outputs]
  - Cached results filtered to requested time range

  [Side Effects]
  - Reads/writes JSON files in data/cache/

WHO:
  Claude AI, User
  (Context: Caching for audio ingestion pipeline)

WHAT:
  Caching layer for the audio ingestion pipeline. Each step has its own
  cache with appropriate keys and invalidation logic.
  
  Key principle: Cache from [0, max_end] and filter on retrieval.
  This way [0-60] cached can serve [10-50], [0-30], etc.

WHEN:
  2025-12-08

WHERE:
  apps/speaker-diarization-benchmark/ingestion/cache.py

WHY:
  To avoid recomputing expensive steps (transcription, diarization, identification)
  when the requested range is within already-computed data.
  
  - Transcription: ~1 min for 4 min audio
  - Diarization: ~30s for 4 min audio
  - Identification: ~5s for 100 segments
"""

import json
import hashlib
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, TYPE_CHECKING
from dataclasses import dataclass, asdict
from datetime import datetime


# Cache directory base
CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"


def extract_video_id(url_or_path: str) -> str:
    """
    Extract a normalized video ID from a URL or file path.
    
    Handles multiple YouTube URL formats:
    - https://www.youtube.com/watch?v=jAlKYYr1bpY
    - https://youtu.be/jAlKYYr1bpY
    - https://www.youtube.com/embed/jAlKYYr1bpY
    - https://www.youtube.com/v/jAlKYYr1bpY
    - https://m.youtube.com/watch?v=jAlKYYr1bpY
    
    For local files, returns the stem (filename without extension).
    
    Args:
        url_or_path: URL or local file path
        
    Returns:
        Normalized video ID
    """
    # YouTube URL patterns
    youtube_patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com/watch\?.*v=)([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in youtube_patterns:
        match = re.search(pattern, url_or_path)
        if match:
            return match.group(1)
    
    # Local file - return stem
    if '/' in url_or_path or '\\' in url_or_path or url_or_path.endswith(('.wav', '.mp3', '.m4a')):
        return Path(url_or_path).stem
    
    # Fallback - hash the input
    return hashlib.md5(url_or_path.encode()).hexdigest()[:11]


@dataclass
class CacheMetadata:
    """Metadata stored with each cache entry."""
    cached_at: str
    cached_end: float
    config_hash: str


class TranscriptionCache:
    """
    Cache for transcription results.
    
    Key: {video_id}__{tool}__{model}  (double underscore separator)
    Stores: [0, cached_end] of transcription
    
    Hit logic:
      - Request [10-50] with cached [0-60] → HIT, filter to [10-50]
      
    Miss logic:
      - Request [0-120] with cached [0-60] → MISS
      - For now: recompute [0-120] entirely (safe, Whisper needs context)
      - Future optimization: compute [55-120] with 5s overlap, merge
    """
    
    def __init__(self, video_id: str, tool: str, model: str):
        self.video_id = video_id
        self.tool = tool
        self.model = model
        
        # Sanitize for filesystem (replace / and : with _)
        safe_model = model.replace('/', '_').replace(':', '_')
        # Use double underscore as separator between key segments
        self.cache_key = f"{video_id}__{tool}__{safe_model}"
        
        self.cache_dir = CACHE_DIR / "transcription"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / f"{self.cache_key}.json"
    
    @property
    def cache_path(self) -> Path:
        """Alias for cache_file (for logging consistency)."""
        return self.cache_file
    
    def has_range(self, end_time: float) -> bool:
        """Check if we have cached data covering [0, end_time]."""
        if not self.cache_file.exists():
            return False
        
        try:
            with open(self.cache_file) as f:
                data = json.load(f)
            return data.get("cached_end", 0) >= end_time
        except Exception:
            return False
    
    def get_cached_end(self) -> Optional[float]:
        """Get the end time of cached data, or None if not cached."""
        if not self.cache_file.exists():
            return None
        
        try:
            with open(self.cache_file) as f:
                data = json.load(f)
            return data.get("cached_end")
        except Exception:
            return None
    
    def get_compute_range(self, requested_end: float) -> Tuple[float, float]:
        """
        Determine what range needs to be computed for a request.
        
        Args:
            requested_end: The end time being requested
            
        Returns:
            Tuple of (start, end) that needs to be computed.
            
        Current behavior (safe):
            - Always returns (0, requested_end) - full recompute
            
        Future optimization:
            - If cached [0-60] and request [0-120], return (55, 120)
            - 5s overlap for context, then merge results
        """
        cached_end = self.get_cached_end()
        
        if cached_end is None:
            # No cache, compute from start
            return (0, requested_end)
        
        if requested_end <= cached_end:
            # Cache hit - no compute needed
            return (0, 0)  # Signal: nothing to compute
        
        # Cache miss - for now, recompute everything
        # Future: return (cached_end - 5, requested_end) for overlap merge
        return (0, requested_end)
    
    def get_filtered(self, start_time: float, end_time: float) -> Optional[Dict[str, Any]]:
        """
        Get cached transcription filtered to [start_time, end_time].
        
        Returns None if cache doesn't cover the range.
        """
        if not self.has_range(end_time):
            return None
        
        try:
            with open(self.cache_file) as f:
                data = json.load(f)
            
            result = data.get("result", {})
            
            # Filter segments to time range
            filtered_segments = []
            for seg in result.get("segments", []):
                seg_start = seg.get("start", 0)
                seg_end = seg.get("end", 0)
                
                # Include if segment overlaps with requested range
                if seg_end > start_time and seg_start < end_time:
                    # Filter words within segment too
                    filtered_words = [
                        w for w in seg.get("words", [])
                        if w.get("end", 0) > start_time and w.get("start", 0) < end_time
                    ]
                    filtered_seg = {**seg, "words": filtered_words}
                    filtered_segments.append(filtered_seg)
            
            return {
                **result,
                "segments": filtered_segments,
            }
        except Exception as e:
            print(f"⚠️ Cache read error: {e}")
            return None
    
    def save(
        self, 
        result: Dict[str, Any], 
        end_time: float, 
        metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Save transcription result to cache with optional metrics."""
        data = {
            "cached_at": datetime.now().isoformat(),
            "cached_end": end_time,
            "video_id": self.video_id,
            "tool": self.tool,
            "model": self.model,
            "result": result,
        }
        
        if metrics:
            data["metrics"] = metrics
        
        with open(self.cache_file, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Transcription cached: {self.cache_key} [0-{end_time}s]")
    
    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """Get cache metadata including metrics."""
        if not self.cache_file.exists():
            return None
        
        try:
            with open(self.cache_file) as f:
                data = json.load(f)
            return {
                "cached_at": data.get("cached_at"),
                "cached_end": data.get("cached_end"),
                "metrics": data.get("metrics"),
            }
        except Exception:
            return None


class DiarizationCache:
    """
    Cache for diarization results.
    
    Key: {video_id}__{workflow}  (double underscore separator)
    Stores: [0, cached_end] of diarization
    
    Hit logic:
      - Request [10-50] with cached [0-60] → HIT, filter to [10-50]
      
    Miss logic:
      - Request [0-120] with cached [0-60] → MISS
      - Diarization CAN be extended: compute [60-120] and merge
      - Segments at boundary may need special handling
      
    Workflow examples:
      - pyannote (default local)
      - pyannote_api (PyAnnote cloud API)
      - wespeaker
    """
    
    def __init__(self, video_id: str, workflow: str):
        self.video_id = video_id
        self.workflow = workflow
        
        # Use double underscore as separator
        self.cache_key = f"{video_id}__{workflow}"
        
        self.cache_dir = CACHE_DIR / "diarization"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / f"{self.cache_key}.json"
    
    @property
    def cache_path(self) -> Path:
        """Alias for cache_file (for logging consistency)."""
        return self.cache_file
    
    def has_range(self, end_time: float) -> bool:
        """Check if we have cached data covering [0, end_time]."""
        if not self.cache_file.exists():
            return False
        
        try:
            with open(self.cache_file) as f:
                data = json.load(f)
            return data.get("cached_end", 0) >= end_time
        except Exception:
            return False
    
    def get_cached_end(self) -> Optional[float]:
        """Get the end time of cached data."""
        if not self.cache_file.exists():
            return None
        
        try:
            with open(self.cache_file) as f:
                data = json.load(f)
            return data.get("cached_end")
        except Exception:
            return None
    
    def get_filtered(self, start_time: float, end_time: float) -> Optional[List[Dict[str, Any]]]:
        """Get cached diarization segments filtered to [start_time, end_time]."""
        if not self.has_range(end_time):
            return None
        
        try:
            with open(self.cache_file) as f:
                data = json.load(f)
            
            segments = data.get("segments", [])
            
            # Filter segments to time range
            filtered = [
                seg for seg in segments
                if seg.get("end", 0) > start_time and seg.get("start", 0) < end_time
            ]
            
            return filtered
        except Exception as e:
            print(f"⚠️ Cache read error: {e}")
            return None
    
    def get_stats(self) -> Optional[Dict[str, Any]]:
        """Get cached stats."""
        if not self.cache_file.exists():
            return None
        
        try:
            with open(self.cache_file) as f:
                data = json.load(f)
            return data.get("stats")
        except Exception:
            return None
    
    def save(
        self, 
        segments: List[Dict[str, Any]], 
        stats: Dict[str, Any], 
        end_time: float,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Save diarization result to cache with optional metrics."""
        data = {
            "cached_at": datetime.now().isoformat(),
            "cached_end": end_time,
            "video_id": self.video_id,
            "workflow": self.workflow,
            "segments": segments,
            "stats": stats,
        }
        
        if metrics:
            data["metrics"] = metrics
        
        with open(self.cache_file, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Diarization cached: {self.cache_key} [0-{end_time}s]")
    
    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """Get cache metadata including metrics."""
        if not self.cache_file.exists():
            return None
        
        try:
            with open(self.cache_file) as f:
                data = json.load(f)
            return {
                "cached_at": data.get("cached_at"),
                "cached_end": data.get("cached_end"),
                "metrics": data.get("metrics"),
            }
        except Exception:
            return None


class IdentificationCache:
    """
    Cache for speaker identification results.
    
    Key: {video_id}__{strategy}__{threshold}__{embedding_count}  (double underscore separator)
    Auto-invalidates when embedding_count changes (new speakers added).
    
    Strategy values:
      - knn: K-nearest neighbors search in pgvector
      - pyannote_api: PyAnnote cloud identification API (future)
      - cosine_threshold: Simple cosine similarity threshold (future)
    
    Hit logic:
      - Request [10-50] with cached [0-60] → HIT, filter to [10-50]
      
    Invalidation:
      - embedding_count changes → cache key changes → automatic miss
      - threshold changes → cache key changes → automatic miss
    """
    
    def __init__(self, video_id: str, strategy: str, threshold: float, embedding_count: int):
        self.video_id = video_id
        self.strategy = strategy  # e.g., "knn", "pyannote_api"
        self.threshold = threshold
        self.embedding_count = embedding_count
        
        # Use double underscore as separator
        self.cache_key = f"{video_id}__{strategy}__{threshold}__{embedding_count}"
        
        self.cache_dir = CACHE_DIR / "identification"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / f"{self.cache_key}.json"
    
    @property
    def cache_path(self) -> Path:
        """Alias for cache_file (for logging consistency)."""
        return self.cache_file
    
    def has_range(self, end_time: float) -> bool:
        """Check if we have cached data covering [0, end_time]."""
        if not self.cache_file.exists():
            return False
        
        try:
            with open(self.cache_file) as f:
                data = json.load(f)
            return data.get("cached_end", 0) >= end_time
        except Exception:
            return False
    
    def get_cached_end(self) -> Optional[float]:
        """Get the end time of cached data."""
        if not self.cache_file.exists():
            return None
        
        try:
            with open(self.cache_file) as f:
                data = json.load(f)
            return data.get("cached_end")
        except Exception:
            return None
    
    def get_filtered(self, start_time: float, end_time: float) -> Optional[Dict[str, Any]]:
        """Get cached identification results filtered to [start_time, end_time]."""
        if not self.has_range(end_time):
            return None
        
        try:
            with open(self.cache_file) as f:
                data = json.load(f)
            
            results = data.get("results", [])
            
            # Filter to time range
            filtered = [
                r for r in results
                if r.get("segment_end", 0) > start_time and r.get("segment_start", 0) < end_time
            ]
            
            return {
                **data,
                "results": filtered,
            }
        except Exception as e:
            print(f"⚠️ Cache read error: {e}")
            return None
    
    def save(self, plan_data: Dict[str, Any], end_time: float) -> None:
        """Save identification plan to cache."""
        data = {
            "cached_at": datetime.now().isoformat(),
            "cached_end": end_time,
            "video_id": self.video_id,
            "strategy": self.strategy,
            "threshold": self.threshold,
            "embedding_count": self.embedding_count,
            **plan_data,
        }
        
        with open(self.cache_file, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Identification cached: {self.cache_key} [0-{end_time}s]")


class PreviewCache:
    """
    Cache for complete preview/wet-run state.
    
    Stores the entire computed state so that --yes can load and save
    without recomputing.
    """
    
    def __init__(self, config_hash: str):
        self.config_hash = config_hash
        
        self.cache_dir = CACHE_DIR / "preview"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / f"{config_hash}.json"
    
    @staticmethod
    def compute_config_hash(config: Dict[str, Any]) -> str:
        """Compute a hash of the config for cache key."""
        # Normalize and sort for consistent hashing
        normalized = json.dumps(config, sort_keys=True)
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def exists(self) -> bool:
        """Check if preview cache exists."""
        return self.cache_file.exists()
    
    def load(self) -> Optional[Dict[str, Any]]:
        """Load cached preview state."""
        if not self.exists():
            return None
        
        try:
            with open(self.cache_file) as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Preview cache read error: {e}")
            return None
    
    def save(self, state: Dict[str, Any]) -> Path:
        """
        Save complete preview state.
        
        Returns the path to the cache file.
        """
        data = {
            "cached_at": datetime.now().isoformat(),
            "config_hash": self.config_hash,
            **state,
        }
        
        with open(self.cache_file, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Preview cached: {self.config_hash}")
        return self.cache_file
    
    def save_markdown(self, preview_content: str, video_id: str) -> Path:
        """
        Save preview as markdown for human review.
        
        Returns path to the markdown file.
        """
        md_file = self.cache_dir / f"{video_id}_preview.md"
        
        with open(md_file, "w") as f:
            f.write(preview_content)
        
        print(f"📄 Preview saved: {md_file}")
        return md_file


def get_embedding_count() -> int:
    """
    Get the current total embedding count from PostgreSQL.
    Used for cache invalidation in IdentificationCache.
    """
    try:
        import psycopg
        
        conn = psycopg.connect(
            "postgresql://diarization:diarization_dev@localhost:5433/speaker_embeddings",
            connect_timeout=2
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM speaker_embeddings")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0

