"""
HOW:
  from ingestion.instant_client import InstantClient
  
  client = InstantClient()  # Uses default localhost:3001
  segments = client.get_diarization_segments(video_id="...")
  client.create_speaker_assignments(assignments=[...])

  [Inputs]
  - base_url: URL of the TypeScript InstantDB server (default: http://localhost:3001)

  [Outputs]
  - Various data from InstantDB via the TypeScript server

  [Side Effects]
  - HTTP requests to the InstantDB TypeScript server

WHO:
  Claude AI, User
  (Context: Python client for the TypeScript InstantDB server)

WHAT:
  A Python client that communicates with the TypeScript InstantDB server.
  This keeps all InstantDB SDK usage in TypeScript while allowing Python
  scripts to interact with the database.

WHEN:
  2025-12-07

WHERE:
  apps/speaker-diarization-benchmark/ingestion/instant_client.py

WHY:
  InstantDB's official SDK is TypeScript. Rather than use unreliable Python
  wrappers, we run a TypeScript server and call it from Python via HTTP.
  This provides reliability and consistency with InstantDB's official tooling.
"""

import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DiarizationSegment:
    """A diarization segment with its speaker assignments."""
    id: str
    start_time: float
    end_time: float
    speaker_label: str
    embedding_id: Optional[str]
    confidence: Optional[float]
    is_invalidated: bool
    speaker_assignments: List[Dict[str, Any]]
    
    @property
    def current_speaker_name(self) -> Optional[str]:
        """Get the most recent speaker assignment's speaker name."""
        if not self.speaker_assignments:
            return None
        # Sort by assigned_at descending and get most recent
        sorted_assignments = sorted(
            self.speaker_assignments,
            key=lambda a: a.get("assigned_at", ""),
            reverse=True
        )
        if sorted_assignments:
            speaker = sorted_assignments[0].get("speaker", [])
            if speaker and len(speaker) > 0:
                return speaker[0].get("name")
        return None
    
    @property
    def current_speaker_id(self) -> Optional[str]:
        """Get the most recent speaker assignment's speaker ID."""
        if not self.speaker_assignments:
            return None
        sorted_assignments = sorted(
            self.speaker_assignments,
            key=lambda a: a.get("assigned_at", ""),
            reverse=True
        )
        if sorted_assignments:
            speaker = sorted_assignments[0].get("speaker", [])
            if speaker and len(speaker) > 0:
                return speaker[0].get("id")
        return None


@dataclass
class Speaker:
    """A speaker entity."""
    id: str
    name: str
    is_human: bool
    embedding_centroid_id: Optional[str]


class InstantClient:
    """Python client for the TypeScript InstantDB server."""
    
    def __init__(self, base_url: str = "http://localhost:3001"):
        self.base_url = base_url.rstrip("/")
        self._check_health()
    
    def _check_health(self) -> None:
        """Check that the server is running."""
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=5)
            resp.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"Cannot connect to InstantDB server at {self.base_url}. "
                "Start it with: bun run apps/speaker-diarization-benchmark/ingestion/instant_server.ts"
            )
    
    def get_video(self, video_id: str) -> Dict[str, Any]:
        """Get a video with its diarization and transcription runs."""
        resp = requests.get(f"{self.base_url}/videos/{video_id}")
        resp.raise_for_status()
        return resp.json()
    
    def get_diarization_segments(
        self,
        video_id: Optional[str] = None,
        run_id: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> List[DiarizationSegment]:
        """
        Get diarization segments for a video or run.
        
        Args:
            video_id: Get segments from the preferred run for this video
            run_id: Get segments from a specific diarization run
            start_time: Filter segments that overlap with this time range (start)
            end_time: Filter segments that overlap with this time range (end)
        
        Returns:
            List of DiarizationSegment objects, sorted by start_time
        """
        params = {}
        if video_id:
            params["video_id"] = video_id
        if run_id:
            params["run_id"] = run_id
        if start_time is not None:
            params["start_time"] = str(start_time)
        if end_time is not None:
            params["end_time"] = str(end_time)
        
        resp = requests.get(f"{self.base_url}/diarization-segments", params=params)
        resp.raise_for_status()
        data = resp.json()
        
        segments = []
        for seg in data.get("segments", []):
            segments.append(DiarizationSegment(
                id=seg["id"],
                start_time=seg["start_time"],
                end_time=seg["end_time"],
                speaker_label=seg.get("speaker_label", "UNKNOWN"),
                embedding_id=seg.get("embedding_id"),
                confidence=seg.get("confidence"),
                is_invalidated=seg.get("is_invalidated", False),
                speaker_assignments=seg.get("speakerAssignments", []),
            ))
        
        return segments
    
    def get_speakers(self) -> List[Speaker]:
        """Get all speakers in the database."""
        resp = requests.get(f"{self.base_url}/speakers")
        resp.raise_for_status()
        data = resp.json()
        
        speakers = []
        for s in data.get("speakers", []):
            speakers.append(Speaker(
                id=s["id"],
                name=s["name"],
                is_human=s.get("is_human", True),
                embedding_centroid_id=s.get("embedding_centroid_id"),
            ))
        
        return speakers
    
    def get_or_create_speaker(self, name: str) -> tuple[Speaker, bool]:
        """
        Get a speaker by name, or create if doesn't exist.
        
        Returns:
            Tuple of (Speaker, created: bool)
        """
        resp = requests.post(f"{self.base_url}/speakers", json={"name": name})
        resp.raise_for_status()
        data = resp.json()
        
        s = data["speaker"]
        speaker = Speaker(
            id=s["id"],
            name=s["name"],
            is_human=s.get("is_human", True),
            embedding_centroid_id=s.get("embedding_centroid_id"),
        )
        
        return speaker, data.get("created", False)
    
    def create_speaker_assignments(
        self,
        assignments: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Create speaker assignments in batch.
        
        Args:
            assignments: List of assignment dicts with keys:
                - segment_id: ID of the diarization segment
                - speaker_id: ID of the speaker
                - source: How assignment was made (e.g., "auto_identify")
                - confidence: Confidence score (0.0 to 1.0)
                - note: JSON metadata about the assignment
                - assigned_by: User/system that made the assignment
        
        Returns:
            Result dict with success status and count
        """
        resp = requests.post(
            f"{self.base_url}/speaker-assignments",
            json={"assignments": assignments}
        )
        resp.raise_for_status()
        return resp.json()
    
    def query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a raw InstaQL query."""
        resp = requests.post(f"{self.base_url}/query", json={"query": query})
        resp.raise_for_status()
        return resp.json()
    
    def transact(self, transactions: List[Any]) -> Dict[str, Any]:
        """Execute raw transactions."""
        resp = requests.post(f"{self.base_url}/transact", json={"transactions": transactions})
        resp.raise_for_status()
        return resp.json()


if __name__ == "__main__":
    # Quick test
    print("Testing InstantClient...")
    client = InstantClient()
    
    print("\n📋 Getting speakers...")
    speakers = client.get_speakers()
    for s in speakers[:5]:
        print(f"  - {s.name} ({s.id[:8]}...)")
    if len(speakers) > 5:
        print(f"  ... and {len(speakers) - 5} more")
    
    print("\n✅ InstantClient working!")

