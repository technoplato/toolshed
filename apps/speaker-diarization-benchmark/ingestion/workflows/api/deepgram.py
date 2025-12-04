"""
WHO:
  Antigravity, Michael Lustig
  (Context: Speaker Diarization Benchmark)

WHAT:
  Deepgram workflow implementation.
  [Inputs]
  - Audio file path
  - Configuration (API key)
  [Outputs]
  - List of segments with speaker labels
  [Side Effects]
  - Calls Deepgram API

WHEN:
  2025-12-04
  Last Modified: 2025-12-04
  Change Log:
    - 2025-12-04: Initial creation

WHERE:
  apps/speaker-diarization-benchmark/ingestion/workflows/deepgram.py

WHY:
  To benchmark Deepgram's diarization performance.
"""

import os
import logging
from typing import List, Dict, Any, Tuple
from pathlib import Path
from dotenv import load_dotenv

from ingestion.workflows.base import Workflow
from ingestion.config import WorkflowConfig

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class DeepgramWorkflow(Workflow):
    def __init__(self, config: WorkflowConfig):
        super().__init__(config)
        self.api_key = os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPGRAM_API_KEY environment variable not set.")

    def run(self, clip_path: Path, transcription_result: Any) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        stats = {'embedding_time': 0, 'segmentation_time': 0, 'clustering_time': 0}
        
        logger.warning("INVOKING DEEPGRAM API. THIS MAY INCUR COSTS.")
        
        try:
            from deepgram import DeepgramClient, PrerecordedOptions, FileSource
        except ImportError:
            logger.error("deepgram-sdk not installed. Please install it with `pip install deepgram-sdk`.")
            return [], stats # Return empty list and stats

        logger.info(f"Running Deepgram workflow on {clip_path}")

        try:
            deepgram = DeepgramClient(self.api_key)

            with open(audio_path, "rb") as file:
                buffer_data = file.read()

            payload: FileSource = {
                "buffer": buffer_data,
            }

            options = PrerecordedOptions(
                model="nova-2",
                smart_format=True,
                diarize=True,
                punctuate=True,
                utterances=True,
            )

            response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)
            
            # Parse response
            segments = []
            
            # Deepgram returns words or utterances. We want segments.
            # Using utterances is usually better for diarization segments.
            if response.results and response.results.utterances:
                for utterance in response.results.utterances:
                    segments.append({
                        "start": utterance.start,
                        "end": utterance.end,
                        "text": utterance.transcript,
                        "speaker": f"SPEAKER_{utterance.speaker}" if utterance.speaker is not None else "UNKNOWN"
                    })
            elif response.results and response.results.channels:
                # Fallback to words if utterances not available (shouldn't happen with utterances=True)
                # But grouping words by speaker is complex.
                logger.warning("No utterances found in Deepgram response. Falling back to channel alternatives.")
                # Implementation for word-level grouping omitted for brevity/simplicity for now.
                pass

            logger.info(f"Deepgram processing complete. Found {len(segments)} segments.")
            return segments

        except Exception as e:
            logger.error(f"Deepgram API failed: {e}")
            return []
