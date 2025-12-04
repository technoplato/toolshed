"""
WHO:
  Antigravity, Michael Lustig
  (Context: Speaker Diarization Benchmark)

WHAT:
  WeSpeaker workflow implementation.
  [Inputs]
  - Audio file path
  - Transcription segments (for word-level embedding)
  [Outputs]
  - List of segments with speaker labels
  [Side Effects]
  - Loads WeSpeaker model
  - Creates temporary files for cropping

WHEN:
  2025-12-04
  Last Modified: 2025-12-04
  Change Log:
    - 2025-12-04: Initial creation

WHERE:
  apps/speaker-diarization-benchmark/ingestion/workflows/wespeaker.py

WHY:
  To benchmark WeSpeaker's diarization performance.
"""

import os
import logging
import time
import tempfile
import json
import numpy as np
import torch
import soundfile as sf
from typing import List, Dict, Any, Tuple
from pathlib import Path
from scipy.spatial.distance import cosine
from sklearn.cluster import AgglomerativeClustering
from pyannote.audio.core.io import Audio
from pyannote.core import Segment as PyannoteSegment

from ingestion.workflows.base import Workflow
from ingestion.safe_globals import get_safe_globals

logger = logging.getLogger(__name__)

class WeSpeakerWorkflow(Workflow):
    def run(self, audio_path: Path, transcription_result: Any) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        """
        Run WeSpeaker diarization.
        """
        stats = {'embedding_time': 0, 'segmentation_time': 0, 'clustering_time': 0}
        
        logger.info("Loading WeSpeaker model...")
        try:
            import wespeaker
            # Try loading english model, fallback to chinese if english not available or default
            try:
                # We wrap with safe_globals just in case, though WeSpeaker might not strictly need it if updated.
                # But since we are in the same environment as Pyannote which caused issues, it's safer.
                # However, we need to import get_safe_globals or define it.
                # For now, we'll try without, and if it fails, we know why.
                # Actually, let's just load it.
                model = wespeaker.load_model('english')
            except Exception:
                logger.warning("English model not found, trying 'chinese'...")
                model = wespeaker.load_model('chinese')
                
            if torch.cuda.is_available():
                model.set_gpu(0)
            logger.info("WeSpeaker model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load WeSpeaker model: {e}")
            return [], stats

        audio_io = Audio(sample_rate=16000, mono="downmix")
        all_words = []
        for seg in transcription_result.segments:
            all_words.extend(seg.words)

        start_time = time.time()
        word_embeddings = []
        valid_words = []

        # WeSpeaker extract_embedding expects a file path.
        # We will use a temporary file for each word crop.
        # This is inefficient but functional for a baseline.
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "temp_crop.wav"
            
            for i, word in enumerate(all_words):
                duration = word.end - word.start
                if duration < 0.02: 
                    continue
                    
                try:
                    w_start_idx = max(0, i - self.config.window)
                    w_end_idx = min(len(all_words) - 1, i + self.config.window)
                    
                    start_time_sec = all_words[w_start_idx].start
                    end_time_sec = all_words[w_end_idx].end
                    
                    waveform, sr = audio_io.crop(audio_path, PyannoteSegment(start_time_sec, end_time_sec))
                    
                    # Save to temp file
                    sf.write(temp_path, waveform.numpy().T, sr)
                    
                    # Embed
                    emb = model.extract_embedding(str(temp_path))
                    word_embeddings.append(torch.from_numpy(emb))
                    valid_words.append(word)
                except Exception as e:
                    # logger.warning(f"Failed to embed word {word.word}: {e}")
                    pass
                
        stats['embedding_time'] = time.time() - start_time
        
        # Segmentation
        start_time = time.time()
        segments = []
        if valid_words:
            current_segment_words = [valid_words[0]]
            current_segment_embeddings = [word_embeddings[0]]
            current_segment_indices = [0]
            
            for i in range(1, len(valid_words)):
                word = valid_words[i]
                emb = word_embeddings[i]
                
                context_embeddings = current_segment_embeddings[-3:]
                context_avg = np.mean(torch.stack(context_embeddings).numpy(), axis=0)
                
                dist = cosine(context_avg, emb.numpy())
                
                if dist > self.config.threshold:
                    segments.append({
                        "start": current_segment_words[0].start,
                        "end": current_segment_words[-1].end,
                        "text": " ".join([w.word for w in current_segment_words]),
                        "word_count": len(current_segment_words),
                        "word_indices": current_segment_indices
                    })
                    current_segment_words = [word]
                    current_segment_embeddings = [emb]
                    current_segment_indices = [i]
                else:
                    current_segment_words.append(word)
                    current_segment_embeddings.append(emb)
                    current_segment_indices.append(i)
                    
            segments.append({
                "start": current_segment_words[0].start,
                "end": current_segment_words[-1].end,
                "text": " ".join([w.word for w in current_segment_words]),
                "word_count": len(current_segment_words),
                "word_indices": current_segment_indices
            })

        stats['segmentation_time'] = time.time() - start_time

        # Clustering & Identification
        start_time = time.time()
        if segments:
            X = []
            for seg in segments:
                indices = seg['word_indices']
                if indices:
                    seg_embs = [word_embeddings[i] for i in indices]
                    avg_emb = np.mean(torch.stack(seg_embs).numpy(), axis=0)
                    X.append(avg_emb)
                else:
                    X.append(np.zeros(256)) # WeSpeaker usually 256
            
            X = np.array(X)
            
            # Handle NaNs
            nan_mask = np.isnan(X).any(axis=1)
            if nan_mask.any():
                valid_indices = np.where(~nan_mask)[0]
                X_clean = X[valid_indices]
            else:
                valid_indices = np.arange(len(X))
                X_clean = X
                
            norms = np.linalg.norm(X_clean, axis=1)
            if np.any(norms == 0):
                X_clean[norms == 0] += 1e-9
            
            if len(X_clean) > 0:
                clustering = AgglomerativeClustering(
                    n_clusters=None,
                    distance_threshold=self.config.cluster_threshold,
                    metric='cosine',
                    linkage='average'
                )
                labels_clean = clustering.fit_predict(X_clean)
            else:
                labels_clean = []
                
            labels = np.full(len(X), -1, dtype=int)
            labels[valid_indices] = labels_clean
            
            for i in range(len(segments)):
                label = labels[i]
                if label != -1:
                    segments[i]['speaker'] = f"SPEAKER_{label:02d}"
                else:
                    segments[i]['speaker'] = "UNKNOWN_NAN"

        stats['clustering_time'] = time.time() - start_time
        return segments, stats
