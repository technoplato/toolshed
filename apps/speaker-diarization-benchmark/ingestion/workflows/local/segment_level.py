"""
WHO:
  Antigravity
  (Context: Audio Ingestion System)

WHAT:
  Segment Level Diarization Workflows (Legacy).
  Includes:
  - SegmentLevelWorkflow: Basic segmentation using Pyannote embedding and clustering.
  - SegmentLevelMatchingWorkflow: Adds speaker identification by matching cluster centroids to known speakers.
  - SegmentLevelNearestNeighborWorkflow: Adds speaker identification by matching cluster centroids to nearest neighbor embeddings.

WHEN:
  2025-12-04

WHERE:
  apps/speaker-diarization-benchmark/ingestion/workflows/local/segment_level.py

WHY:
  To support legacy workflows from benchmark_baseline.py in the new modular system.
"""

import os
import time
import logging
import torch
import numpy as np
import json
from typing import List, Dict, Any, Tuple
from pathlib import Path
from scipy.spatial.distance import cosine, cdist
from sklearn.cluster import AgglomerativeClustering
from pyannote.audio import Model, Inference
from pyannote.audio.core.io import Audio
from pyannote.core import Segment as PyannoteSegment
from ingestion.workflows.base import Workflow
from ingestion.safe_globals import get_safe_globals

logger = logging.getLogger(__name__)

class SegmentLevelWorkflow(Workflow):
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.threshold = self.config.get("threshold", 0.5)
        self.cluster_threshold = self.config.get("cluster_threshold", 0.5)
        self.hf_token = os.getenv("HF_TOKEN")

    def _load_model(self):
        logger.info("Loading embedding model (pyannote/embedding)...")
        try:
            with torch.serialization.safe_globals(get_safe_globals()):
                model = Model.from_pretrained("pyannote/embedding", use_auth_token=self.hf_token)
            
            inference = Inference(model, window="whole")
            model.to(torch.device("cpu"))
            return inference
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            return None

    def run(self, clip_path: Path, transcription_result: Any) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        stats = {'embedding_time': 0, 'segmentation_time': 0, 'clustering_time': 0}
        
        inference = self._load_model()
        if not inference:
            return [], stats

        audio_io = Audio(sample_rate=16000, mono="downmix")
        
        start_time = time.time()
        embeddings = []
        valid_indices = []
        
        # transcription_result.segments contains the segments from transcription
        transcription_segments = transcription_result.segments
        
        for i, seg in enumerate(transcription_segments):
            duration = seg.end - seg.start
            if duration < 0.02:
                continue
                
            try:
                waveform, sr = audio_io.crop(clip_path, PyannoteSegment(seg.start, seg.end))
                emb = inference({"waveform": waveform, "sample_rate": sr})
                embeddings.append(emb)
                valid_indices.append(i)
            except Exception as e:
                logger.warning(f"Failed to embed segment {i}: {e}")
                pass
                
        stats['embedding_time'] = time.time() - start_time
        
        # Clustering
        start_time = time.time()
        
        if not embeddings:
            return [], stats
            
        X = np.vstack(embeddings)
        
        # Filter NaNs
        valid_mask = ~np.isnan(X).any(axis=1)
        X_clean = X[valid_mask]
        
        # Map clean indices back to original segment indices
        clean_to_original_map = []
        for i, is_valid in enumerate(valid_mask):
            if is_valid:
                clean_to_original_map.append(valid_indices[i])
                
        if len(X_clean) > 0:
            clustering = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=self.cluster_threshold,
                metric='cosine',
                linkage='average'
            )
            labels = clustering.fit_predict(X_clean)
        else:
            labels = []
            
        stats['clustering_time'] = time.time() - start_time
        
        # Assign speakers
        final_segments = []
        
        # Initialize all as UNKNOWN
        for seg in transcription_segments:
            final_segments.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text,
                "speaker": "UNKNOWN"
            })
            
        # Update with clustered labels
        for i, label in enumerate(labels):
            original_idx = clean_to_original_map[i]
            final_segments[original_idx]['speaker'] = f"SPEAKER_{label:02d}"
            
        return final_segments, stats

class SegmentLevelMatchingWorkflow(SegmentLevelWorkflow):
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.id_threshold = self.config.get("id_threshold", 0.4)

    def run(self, clip_path: Path, transcription_result: Any) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        # Run base implementation to get clusters
        final_segments, stats = super().run(clip_path, transcription_result)
        
        # Extract embeddings again? Or refactor base to return them?
        # Refactoring base is cleaner, but to avoid breaking changes let's just re-implement run 
        # or better, let's modify base to be more extensible if I could.
        # But for now, I will just copy-paste the core logic or call a helper.
        # Actually, I'll just re-implement run to avoid complexity of refactoring base right now.
        # Wait, I can just copy the logic since I have the code.
        
        # Re-run embedding/clustering logic (inefficient but safe)
        # OR: Refactor base to separate steps.
        # Let's refactor base slightly to separate steps? No, I'll just duplicate for now to be safe and fast.
        
        # Actually, let's just copy the full implementation from benchmark_baseline.py for this class
        # to ensure it matches exactly what was there.
        
        inference = self._load_model()
        if not inference:
            return [], stats

        audio_io = Audio(sample_rate=16000, mono="downmix")
        
        start_time = time.time()
        embeddings = []
        valid_indices = []
        
        transcription_segments = transcription_result.segments
        
        for i, seg in enumerate(transcription_segments):
            duration = seg.end - seg.start
            if duration < 0.02:
                continue
            try:
                waveform, sr = audio_io.crop(clip_path, PyannoteSegment(seg.start, seg.end))
                emb = inference({"waveform": waveform, "sample_rate": sr})
                embeddings.append(emb)
                valid_indices.append(i)
            except Exception:
                pass
                
        stats['embedding_time'] = time.time() - start_time
        
        start_time = time.time()
        if not embeddings:
            return [], stats
            
        X = np.vstack(embeddings)
        valid_mask = ~np.isnan(X).any(axis=1)
        X_clean = X[valid_mask]
        
        clean_to_original_map = []
        for i, is_valid in enumerate(valid_mask):
            if is_valid:
                clean_to_original_map.append(valid_indices[i])
                
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
            
        stats['clustering_time'] = time.time() - start_time
        
        # Identification Logic
        logger.info("Starting identification matching...")
        
        # Locate DB relative to this file? No, relative to repo root.
        # Assuming repo root is 4 levels up from here?
        # apps/speaker-diarization-benchmark/ingestion/workflows/local/segment_level.py -> ... -> apps/speaker-diarization-benchmark/
        # DB is in apps/speaker-diarization-benchmark/data/speaker_embeddings.json
        
        # Let's find the DB path dynamically or hardcode relative to known structure
        # current file: .../ingestion/workflows/local/segment_level.py
        # parent: .../ingestion/workflows/local
        # parent.parent: .../ingestion/workflows
        # parent.parent.parent: .../ingestion
        # parent.parent.parent.parent: .../speaker-diarization-benchmark
        
        base_dir = Path(__file__).parent.parent.parent.parent
        db_path = base_dir / "data/speaker_embeddings.json"
        
        known_speakers = {}
        if db_path.exists():
            with open(db_path, 'r') as f:
                known_speakers = json.load(f)
                logger.info(f"Loaded {len(known_speakers)} known speakers from DB.")
        else:
            logger.warning(f"Speaker embeddings DB not found at {db_path}")
            
        cluster_centroids = {}
        unique_labels = set(labels_clean) if len(X_clean) > 0 else set()
        
        for label in unique_labels:
            clean_indices = np.where(labels_clean == label)[0]
            cluster_embs = X_clean[clean_indices]
            cluster_centroids[label] = np.mean(cluster_embs, axis=0)
            
        final_labels = {}
        match_details = {}
        
        for label, centroid in cluster_centroids.items():
            min_dist = 2.0
            best_match_name = "None"
            
            for name, known_embs in known_speakers.items():
                if not known_embs: continue
                known_proto = np.mean(np.array(known_embs), axis=0)
                d = cosine(centroid, known_proto)
                if d < min_dist:
                    min_dist = d
                    best_match_name = name
            
            match_details[label] = {"best_match": best_match_name, "distance": min_dist}
            
            if min_dist < self.id_threshold:
                final_labels[label] = best_match_name
            else:
                final_labels[label] = f"SPEAKER_{label:02d}"
                
        final_segments = []
        for seg in transcription_segments:
            final_segments.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text,
                "speaker": "UNKNOWN"
            })
            
        for i, label in enumerate(labels_clean):
            original_idx = clean_to_original_map[i]
            final_segments[original_idx]['speaker'] = final_labels[label]
            if label in match_details:
                final_segments[original_idx]['match_info'] = match_details[label]
                
        return final_segments, stats

class SegmentLevelNearestNeighborWorkflow(SegmentLevelMatchingWorkflow):
    def run(self, clip_path: Path, transcription_result: Any) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        # Almost identical to Matching, but uses Nearest Neighbor logic
        # I'll copy paste and modify the matching loop
        
        inference = self._load_model()
        if not inference:
            return [], {} # Empty stats

        audio_io = Audio(sample_rate=16000, mono="downmix")
        start_time = time.time()
        embeddings = []
        valid_indices = []
        transcription_segments = transcription_result.segments
        
        for i, seg in enumerate(transcription_segments):
            duration = seg.end - seg.start
            if duration < 0.02: continue
            try:
                waveform, sr = audio_io.crop(clip_path, PyannoteSegment(seg.start, seg.end))
                emb = inference({"waveform": waveform, "sample_rate": sr})
                embeddings.append(emb)
                valid_indices.append(i)
            except Exception: pass
            
        stats = {'embedding_time': time.time() - start_time, 'segmentation_time': 0, 'clustering_time': 0}
        
        start_time = time.time()
        if not embeddings: return [], stats
        
        X = np.vstack(embeddings)
        valid_mask = ~np.isnan(X).any(axis=1)
        X_clean = X[valid_mask]
        
        clean_to_original_map = [valid_indices[i] for i, v in enumerate(valid_mask) if v]
        
        if len(X_clean) > 0:
            clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=self.cluster_threshold, metric='cosine', linkage='average')
            labels_clean = clustering.fit_predict(X_clean)
        else:
            labels_clean = []
            
        stats['clustering_time'] = time.time() - start_time
        
        # NN Identification
        base_dir = Path(__file__).parent.parent.parent.parent
        db_path = base_dir / "data/speaker_embeddings.json"
        known_speakers = {}
        if db_path.exists():
            with open(db_path, 'r') as f: known_speakers = json.load(f)
            
        cluster_centroids = {}
        unique_labels = set(labels_clean) if len(X_clean) > 0 else set()
        for label in unique_labels:
            cluster_centroids[label] = np.mean(X_clean[labels_clean == label], axis=0)
            
        final_labels = {}
        match_details = {}
        
        for label, centroid in cluster_centroids.items():
            min_dist = 2.0
            best_match_name = "None"
            
            for name, known_embs in known_speakers.items():
                if not known_embs: continue
                known_embs_arr = np.array(known_embs)
                dists = cdist(centroid.reshape(1, -1), known_embs_arr, metric='cosine')
                min_d_speaker = np.min(dists)
                
                if min_d_speaker < min_dist:
                    min_dist = min_d_speaker
                    best_match_name = name
            
            match_details[label] = {"best_match": best_match_name, "distance": min_dist}
            if min_dist < self.id_threshold:
                final_labels[label] = best_match_name
            else:
                final_labels[label] = f"SPEAKER_{label:02d}"
                
        final_segments = [{"start": s.start, "end": s.end, "text": s.text, "speaker": "UNKNOWN"} for s in transcription_segments]
        
        for i, label in enumerate(labels_clean):
            original_idx = clean_to_original_map[i]
            final_segments[original_idx]['speaker'] = final_labels[label]
            if label in match_details:
                final_segments[original_idx]['match_info'] = match_details[label]
                
        return final_segments, stats
