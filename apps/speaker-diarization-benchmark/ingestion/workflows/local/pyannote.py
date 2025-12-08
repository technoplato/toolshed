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
from ..base import Workflow

logger = logging.getLogger(__name__)

# Import safe globals helper
try:
    from ingestion.safe_globals import get_safe_globals
except ImportError:
    def get_safe_globals():
        return []


class PyannoteWorkflow(Workflow):
    """Pyannote-based speaker diarization workflow."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.model_name = self.config.get("model_name", "pyannote/speaker-diarization-3.1")
        self.use_auth_token = self.config.get("use_auth_token", True)

    def run(self, clip_path: Path, transcription_result: Any) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        stats = {'embedding_time': 0, 'segmentation_time': 0, 'clustering_time': 0, 'load_time': 0}
        
        logger.info(f"🎙️ PyAnnote Diarization: {clip_path}")
        logger.info(f"   Model: {self.model_name}")
        
        hf_token = os.getenv("HF_TOKEN")
        if self.use_auth_token and not hf_token:
            # Check for PYANNOTEAI_API_KEY if using precision model
            if "precision" in self.model_name:
                 hf_token = os.getenv("PYANNOTEAI_API_KEY")
                 if not hf_token:
                     logger.error("❌ PYANNOTEAI_API_KEY not found in environment variables.")
                     return [], stats
            else:
                logger.error("❌ HF_TOKEN not found in environment variables.")
                return [], stats

        load_start = time.time()
        logger.info(f"   ⏳ Loading pipeline (this may take 30-60s on first run)...")
        
        try:
            from pyannote.audio import Pipeline

            with torch.serialization.safe_globals(get_safe_globals()):
                try:
                    pipeline = Pipeline.from_pretrained(self.model_name, use_auth_token=hf_token)
                except TypeError:
                    # Fallback for newer versions that might use 'token' or no argument if logged in
                    pipeline = Pipeline.from_pretrained(self.model_name, token=hf_token)
            
            device = "mps" if torch.backends.mps.is_available() else "cpu"
            pipeline.to(torch.device(device))
            stats['load_time'] = time.time() - load_start
            logger.info(f"   ✅ Pipeline loaded in {stats['load_time']:.1f}s (device: {device})")
        except Exception as e:
            logger.error(f"❌ Failed to load pipeline: {e}")
            return [], stats
            
        diar_start = time.time()
        logger.info(f"   ⏳ Running diarization (this may take 1-2 min for 60s audio)...")
        try:
            diarization = pipeline(str(clip_path))
            stats['segmentation_time'] = time.time() - diar_start
            logger.info(f"   ✅ Diarization complete in {stats['segmentation_time']:.1f}s")
        except Exception as e:
            logger.error(f"❌ Diarization failed: {e}")
            return [], stats
        
        # Align words with speakers
        logger.info("   ⏳ Aligning transcription with diarization...")
        
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
             logger.error("❌ Diarization object does not have itertracks method.")
             return [], stats

        for turn, _, speaker in diarization.itertracks(yield_label=True):
            diar_segments.append((turn.start, turn.end, speaker))
        
        unique_speakers = set(s for _, _, s in diar_segments)
        logger.info(f"   Found {len(diar_segments)} raw segments, {len(unique_speakers)} speakers: {sorted(unique_speakers)}")
            
        # Flatten words from transcription result
        all_words = []
        for seg in transcription_result.segments:
            all_words.extend(seg.words)
            
        if not all_words:
            logger.warning("⚠️ No words found in transcription.")
            return [], stats
        
        logger.info(f"   Aligning {len(all_words)} words with speakers...")

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
        
        total_time = stats.get('load_time', 0) + stats.get('segmentation_time', 0)
        logger.info(f"   ✅ Created {len(segments)} aligned segments in {total_time:.1f}s total")
            
        return segments, stats
