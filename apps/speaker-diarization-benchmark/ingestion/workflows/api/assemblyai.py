"""
WHO:
  Antigravity
  (Context: Audio Ingestion System)

WHAT:
  AssemblyAI Diarization Workflow.

WHEN:
  2025-12-03

WHERE:
  apps/speaker-diarization-benchmark/ingestion/workflows/assemblyai.py

WHY:
  To implement diarization using the AssemblyAI API.
"""

import os
import time
import logging
import assemblyai as aai
from typing import List, Dict, Any, Tuple
from pathlib import Path
from ingestion.workflows.base import Workflow

logger = logging.getLogger(__name__)

class AssemblyAIWorkflow(Workflow):
    def run(self, clip_path: Path, transcription_result: Any) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        stats = {'embedding_time': 0, 'segmentation_time': 0, 'clustering_time': 0}
        
        logger.warning("INVOKING ASSEMBLYAI API. THIS MAY INCUR COSTS.")

        api_key = os.getenv("ASSEMBLYAI_API_KEY")
        if not api_key:
            logger.error("ASSEMBLYAI_API_KEY not found in environment variables.")
            return [], stats
            
        aai.settings.api_key = api_key
        transcriber = aai.Transcriber()
        
        config = aai.TranscriptionConfig(
            speaker_labels=True,
            speakers_expected=self.config.min_speakers # Use min_speakers as expected count if provided
        )
        
        logger.info("Submitting audio to AssemblyAI...")
        start_time = time.time()
        
        try:
            transcript = transcriber.transcribe(str(clip_path), config)
        except Exception as e:
            logger.error(f"AssemblyAI transcription failed: {e}")
            return [], stats
            
        if transcript.status == aai.TranscriptStatus.error:
            logger.error(f"AssemblyAI error: {transcript.error}")
            return [], stats
            
        # AssemblyAI does everything in one go, so we attribute it all to segmentation for now
        # or split it evenly? Let's put it in segmentation.
        stats['segmentation_time'] = time.time() - start_time
        
        segments = []
        for utterance in transcript.utterances:
            segments.append({
                "start": utterance.start / 1000.0, # Convert ms to s
                "end": utterance.end / 1000.0,
                "text": utterance.text,
                "speaker": f"SPEAKER_{utterance.speaker}" # Normalize speaker ID
            })
            
        return segments, stats
