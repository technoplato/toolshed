"""
WHO:
  Antigravity
  (Context: Audio Ingestion System)

WHAT:
  WhisperPlus Workflows (MLX, Lightning MLX, Diarization).
  Wraps the whisperplus library to provide additional benchmarking options.

WHEN:
  2025-12-04

WHERE:
  apps/speaker-diarization-benchmark/ingestion/workflows/local/whisperplus.py

WHY:
  To benchmark WhisperPlus implementations of Whisper (Apple MLX, Lightning)
  and their speaker diarization pipeline.
"""

import os
import time
import logging
from typing import List, Dict, Any, Tuple
from pathlib import Path
from ingestion.workflows.base import Workflow
from ingestion.config import WorkflowConfig

logger = logging.getLogger(__name__)

class WhisperPlusDiarizeWorkflow(Workflow):
    def run(self, clip_path: Path, transcription_result: Any) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        stats = {'embedding_time': 0, 'segmentation_time': 0, 'clustering_time': 0}
        
        logger.info("Running WhisperPlus Diarization Workflow (Vendored)...")
        start_time = time.time()
        
        try:
            # Import from local vendor
            from ingestion.workflows.local.vendor.whisperplus_diarize import ASRDiarizationPipeline
        except ImportError as e:
            logger.error(f"Failed to import vendored WhisperPlus pipeline: {e}")
            return [], stats

        try:
            import torch
            from ingestion.safe_globals import get_safe_globals
            
            device = "mps" if os.uname().sysname == "Darwin" else "cpu" # Try MPS for Mac
            
            with torch.serialization.safe_globals(get_safe_globals()):
                pipeline = ASRDiarizationPipeline.from_pretrained(
                    asr_model="openai/whisper-large-v3",
                    diarizer_model="pyannote/speaker-diarization-3.1",
                    chunk_length_s=30,
                    device=device,
                )
            
            output_text = pipeline(str(clip_path), num_speakers=None, min_speaker=None, max_speaker=None)
            
            logger.info(f"WhisperPlus Diarization Raw Output: {output_text}")

            segments = []
            if isinstance(output_text, list):
                for item in output_text:
                    segments.append({
                        "start": item.get('timestamp', (0,0))[0],
                        "end": item.get('timestamp', (0,0))[1],
                        "text": item.get('text', ''),
                        "speaker": item.get('speaker', 'UNKNOWN')
                    })
            else:
                 logger.warning(f"Unknown output format from Diarization Pipeline: {type(output_text)}")
            
            stats['clustering_time'] = time.time() - start_time
            return segments, stats

        except Exception as e:
            logger.error(f"WhisperPlus Diarization failed: {e}")
            return [], stats
