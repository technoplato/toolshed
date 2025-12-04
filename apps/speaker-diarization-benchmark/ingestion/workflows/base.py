"""
WHO:
  Antigravity
  (Context: Audio Ingestion System)

WHAT:
  Abstract Base Class for Diarization Workflows.

WHEN:
  2025-12-03

WHERE:
  apps/speaker-diarization-benchmark/ingestion/workflows/base.py

WHY:
  To define a common interface for all diarization workflows.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from pathlib import Path
from ..config import WorkflowConfig

class Workflow(ABC):
    def __init__(self, config: WorkflowConfig):
        self.config = config

    @abstractmethod
    def run(self, clip_path: Path, transcription_result: Any) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        """
        Runs the diarization workflow.
        
        Args:
            clip_path: Path to the audio clip.
            transcription_result: The result from the transcription step (contains segments and words).
            
        Returns:
            A tuple containing:
            - List of segments (dict with start, end, text, speaker)
            - Dictionary of timing statistics
        """
        pass
