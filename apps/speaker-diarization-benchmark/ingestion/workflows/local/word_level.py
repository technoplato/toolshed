"""
WHO:
  Antigravity
  (Context: Audio Ingestion System)

WHAT:
  Word Level Diarization Workflow.
  Performs manual segmentation by embedding individual words (with context window)
  and grouping them based on cosine distance.

WHEN:
  2025-12-04

WHERE:
  apps/speaker-diarization-benchmark/ingestion/workflows/local/word_level.py

WHY:
  To restore the "word-level" workflow from benchmark_baseline.py that allows for
  fine-grained control over segmentation using embedding distances.
"""

import os
import time
import logging
import torch
import numpy as np
import json
from typing import List, Dict, Any, Tuple
from pathlib import Path
from scipy.spatial.distance import cosine
from sklearn.cluster import AgglomerativeClustering
from pyannote.audio import Model, Inference
from pyannote.audio.core.io import Audio
from pyannote.core import Segment as PyannoteSegment
from ingestion.workflows.base import Workflow
from ingestion.safe_globals import get_safe_globals

logger = logging.getLogger(__name__)

class WordLevelWorkflow(Workflow):
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.threshold = self.config.get("threshold", 0.5)
        self.window = self.config.get("window", 0)
        self.cluster_threshold = self.config.get("cluster_threshold", 0.5)
        self.id_threshold = self.config.get("id_threshold", 0.4)
        self.hf_token = os.getenv("HF_TOKEN")

    def run(self, clip_path: Path, transcription_result: Any) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        stats = {'embedding_time': 0, 'segmentation_time': 0, 'clustering_time': 0}
        
        logger.info("Loading embedding model (pyannote/embedding)...")
        try:
            with torch.serialization.safe_globals(get_safe_globals()):
                model = Model.from_pretrained("pyannote/embedding", use_auth_token=self.hf_token)
            
            inference = Inference(model, window="whole")
            model.to(torch.device("cpu"))
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            return [], stats

        audio_io = Audio(sample_rate=16000, mono="downmix")
        
        start_time = time.time()
        word_embeddings = []
        valid_words = []
        
        # Flatten all words from segments
        all_words = []
        for seg in transcription_result.segments:
            all_words.extend(seg.words)

        for i, word in enumerate(all_words):
            # Initial window based on config
            w_start_idx = max(0, i - self.window)
            w_end_idx = min(len(all_words) - 1, i + self.window)
            
            # Dynamic window expansion for short segments
            min_duration = 0.05 # Minimum duration required for stable embedding
            
            current_duration = all_words[w_end_idx].end - all_words[w_start_idx].start
            
            # Expand window until duration is sufficient
            while current_duration < min_duration:
                can_expand_right = w_end_idx < len(all_words) - 1
                can_expand_left = w_start_idx > 0
                
                if not can_expand_right and not can_expand_left:
                    break
                    
                if can_expand_right:
                    w_end_idx += 1
                elif can_expand_left:
                    w_start_idx -= 1
                    
                current_duration = all_words[w_end_idx].end - all_words[w_start_idx].start

            try:
                start_time_sec = all_words[w_start_idx].start
                end_time_sec = all_words[w_end_idx].end
                
                waveform, sr = audio_io.crop(clip_path, PyannoteSegment(start_time_sec, end_time_sec))
                emb = inference({"waveform": waveform, "sample_rate": sr})
                
                # Check for NaNs
                if np.isnan(emb).any():
                    # Fallback to previous embedding if available (continuity)
                    if word_embeddings:
                        emb = word_embeddings[-1]
                    else:
                        # If first word is NaN, use zeros (will likely be UNKNOWN)
                        emb = np.zeros(512)
                
                word_embeddings.append(emb)
                valid_words.append(word)
            except Exception as e:
                # logger.warning(f"Failed to embed word '{word.text}': {e}")
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
                # context_embeddings are numpy arrays (from inference output)
                # We can just stack them with numpy
                context_avg = np.mean(np.stack(context_embeddings), axis=0)
                
                dist = cosine(context_avg, emb)
                
                if dist > self.threshold:
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
                    avg_emb = np.mean(np.stack(seg_embs), axis=0)
                    X.append(avg_emb)
                else:
                    X.append(np.zeros(512))
            
            X = np.array(X)
            
            # Handle NaNs
            nan_mask = np.isnan(X).any(axis=1)
            if nan_mask.any():
                logger.warning(f"Found {nan_mask.sum()} segments with NaN embeddings. Assigning UNKNOWN_NAN.")
                valid_indices = np.where(~nan_mask)[0]
                X_clean = X[valid_indices]
            else:
                valid_indices = np.arange(len(X))
                X_clean = X
                
            # Check for zero vectors
            norms = np.linalg.norm(X_clean, axis=1)
            if np.any(norms == 0):
                X_clean[norms == 0] += 1e-9
            
            if len(X_clean) > 0:
                clustering = AgglomerativeClustering(
                    n_clusters=None,
                    distance_threshold=self.cluster_threshold,
                    metric='cosine',
                    linkage='average'
                )
                labels_clean = clustering.fit_predict(X_clean)
            else:
                labels_clean = []
                
            # Map back to original indices
            labels = np.full(len(X), -1, dtype=int)
            labels[valid_indices] = labels_clean
            
            # Identification
            base_dir = Path(__file__).parent.parent.parent.parent
            db_path = base_dir / "data/speaker_embeddings.json"
            known_speakers = {}
            if db_path.exists():
                with open(db_path, 'r') as f:
                    known_speakers = json.load(f)
            
            cluster_centroids = {}
            unique_labels = set(labels_clean) if len(X_clean) > 0 else set()
            
            for label in unique_labels:
                clean_indices = np.where(labels_clean == label)[0]
                cluster_embs = X_clean[clean_indices]
                cluster_centroids[label] = cluster_embs
                
            final_labels = {}
            for label, embs in cluster_centroids.items():
                centroid = np.mean(embs, axis=0)
                min_dist = 2.0
                identity = f"SPEAKER_{label:02d}"
                
                for name, known_embs in known_speakers.items():
                    if not known_embs: continue
                    known_proto = np.mean(known_embs, axis=0)
                    d = cosine(centroid, known_proto)
                    if d < min_dist:
                        min_dist = d
                        identity = name
                
                if min_dist < self.id_threshold:
                    final_labels[label] = identity
                else:
                    final_labels[label] = f"SPEAKER_{label:02d}"
            
            for i in range(len(segments)):
                label = labels[i]
                if label != -1:
                    segments[i]['speaker'] = final_labels[label]
                else:
                    segments[i]['speaker'] = "UNKNOWN_NAN"

        stats['clustering_time'] = time.time() - start_time
        return segments, stats
