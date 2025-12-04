"""
WHO:
  Antigravity
  (Context: Audio Ingestion System)

WHAT:
  Pyannote Diarization Workflow.

WHEN:
  2025-12-03

WHERE:
  apps/speaker-diarization-benchmark/ingestion/workflows/pyannote.py

WHY:
  To implement diarization using Pyannote.
"""

import os
import time
import logging
import torch
from typing import List, Dict, Any, Tuple
from pathlib import Path
from .base import Workflow

logger = logging.getLogger(__name__)

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.model_name = self.config.get("model_name", "pyannote/speaker-diarization-3.1")
        self.use_auth_token = self.config.get("use_auth_token", True)

    def run(self, clip_path: Path, transcription_result: Any) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        stats = {'embedding_time': 0, 'segmentation_time': 0, 'clustering_time': 0}
        
        hf_token = os.getenv("HF_TOKEN")
        if self.use_auth_token and not hf_token:
            # Check for PYANNOTEAI_API_KEY if using precision model
            if "precision" in self.model_name:
                 hf_token = os.getenv("PYANNOTEAI_API_KEY")
                 if not hf_token:
                     logger.error("PYANNOTEAI_API_KEY not found in environment variables.")
                     return [], stats
            else:
                logger.error("HF_TOKEN not found in environment variables.")
                return [], stats

        logger.info(f"Loading {self.model_name} pipeline...")
        
        try:
            from pyannote.audio import Pipeline

            with torch.serialization.safe_globals(get_safe_globals()):
                try:
                    pipeline = Pipeline.from_pretrained(self.model_name, use_auth_token=hf_token)
                except TypeError:
                    # Fallback for newer versions that might use 'token' or no argument if logged in
                    pipeline = Pipeline.from_pretrained(self.model_name, token=hf_token)
            
            pipeline.to(torch.device("cpu")) # Force CPU for now
        except Exception as e:
            logger.error(f"Failed to load pipeline: {e}")
            return [], stats
            
        start_time = time.time()
        logger.info("Running diarization pipeline...")
        try:
            diarization = pipeline(str(clip_path))
        except Exception as e:
            logger.error(f"Diarization failed: {e}")
            return [], stats
            
        stats['segmentation_time'] = time.time() - start_time
        
        # Align words with speakers
        logger.info("Aligning transcription with diarization...")
        
        # Create a list of (start, end, speaker)
        diar_segments = []
        
        # Handle Pyannote 4.0 DiarizeOutput
        if not hasattr(diarization, 'itertracks'):
            if hasattr(diarization, 'annotation'):
                diarization = diarization.annotation
            elif hasattr(diarization, '__getitem__'):
                try:
                    diarization = diarization[0]
                except Exception:
                    pass
            
            if not hasattr(diarization, 'itertracks'):
                try:
                    from pyannote.core import Annotation
                    d_vars = vars(diarization)
                    for k, v in d_vars.items():
                        if isinstance(v, Annotation):
                            diarization = v
                            break
                except Exception:
                    pass

        if not hasattr(diarization, 'itertracks'):
             logger.error("Diarization object does not have itertracks method.")
             return [], stats

        for turn, _, speaker in diarization.itertracks(yield_label=True):
            diar_segments.append((turn.start, turn.end, speaker))
            
        # Flatten words from transcription result
        all_words = []
        for seg in transcription_result.segments:
            all_words.extend(seg.words)
            
        if not all_words:
            logger.warning("No words found in transcription.")
            return [], stats

        # Assign speaker to each word
        word_speakers = []
        for word in all_words:
            midpoint = (word.start + word.end) / 2
            assigned_speaker = "UNKNOWN"
            
            # Simple linear search (can be optimized)
            for start, end, speaker in diar_segments:
                if start <= midpoint <= end:
                    assigned_speaker = speaker
                    break
            word_speakers.append(assigned_speaker)
            
        # Group words into segments
        segments = []
        if all_words:
            current_speaker = word_speakers[0]
            current_words = [all_words[0]]
            
            for i in range(1, len(all_words)):
                speaker = word_speakers[i]
                word = all_words[i]
                
                if speaker != current_speaker:
                    segments.append({
                        "start": current_words[0].start,
                        "end": current_words[-1].end,
                        "text": " ".join([w.word for w in current_words]),
                        "speaker": current_speaker
                    })
                    current_speaker = speaker
                    current_words = [word]
                else:
                    current_words.append(word)
                    
            segments.append({
                "start": current_words[0].start,
                "end": current_words[-1].end,
                "text": " ".join([w.word for w in current_words]),
                "speaker": current_speaker
            })
            
        return segments, stats
