import json
import logging
import argparse
from pathlib import Path
import torch
import numpy as np
from pyannote.audio import Model, Inference
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_distances

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
CLIPS_DIR = DATA_DIR / "clips"
MANIFEST_FILE = CLIPS_DIR / "manifest.json"
import os

HF_TOKEN = os.getenv("HF_TOKEN")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--clip-id", type=str, required=True, help="Clip ID to process")
    args = parser.parse_args()

    if not MANIFEST_FILE.exists():
        logger.error("Manifest not found.")
        return
       # Load manifest
    with open(MANIFEST_FILE, 'r') as f:
        manifest = json.load(f)
        
    clip_data = next((c for c in manifest if c['id'] == args.clip_id), None)
    if not clip_data:
        logger.error(f"Clip {args.clip_id} not found in manifest.")
        # Debug: print all IDs
        logger.info(f"Available IDs: {[c['id'] for c in manifest]}")
        return

    transcriptions = clip_data.get('transcriptions', {})
    logger.info(f"Found transcriptions keys: {list(transcriptions.keys())}")
    
    if 'mlx_whisper_turbo' not in transcriptions and 'mlx_whisper_turbo_seg_level' not in transcriptions:
        logger.error(f"No mlx_whisper_turbo segments found. Available models: {list(transcriptions.keys())}")
        return
        
    if 'mlx_whisper_turbo' in transcriptions:
        segments = transcriptions['mlx_whisper_turbo']
    elif 'mlx_whisper_turbo_seg_level' in transcriptions:
        logger.warning("Using existing 'mlx_whisper_turbo_seg_level' as source segments.")
        segments = transcriptions['mlx_whisper_turbo_seg_level']
    else:
        logger.error("No suitable segments found.")
        return
    clip_path = Path(clip_data['clip_path'])
    if not clip_path.exists():
        clip_path = Path(__file__).parent / clip_data['clip_path']

    logger.info("Loading embedding model...")
    try:
        # Using pyannote/embedding (access granted)
        import omegaconf
        import pytorch_lightning
        import typing
        import collections
        from pyannote.audio.core.task import Specifications, Problem, Resolution
        import pyannote.audio.core.model
        with torch.serialization.safe_globals([
            torch.torch_version.TorchVersion,
            omegaconf.listconfig.ListConfig,
            omegaconf.dictconfig.DictConfig,
            Specifications,
            Problem,
            Resolution,
            pyannote.audio.core.model.Introspection,
            pytorch_lightning.callbacks.early_stopping.EarlyStopping,
            pytorch_lightning.callbacks.model_checkpoint.ModelCheckpoint,
            omegaconf.base.ContainerMetadata,
            omegaconf.base.Metadata,
            omegaconf.nodes.AnyNode,
            omegaconf.nodes.StringNode,
            omegaconf.nodes.IntegerNode,
            omegaconf.nodes.FloatNode,
            omegaconf.nodes.BooleanNode,
            typing.Any,
            list,
            dict,
            collections.defaultdict,
            int,
            float,
            str,
            tuple,
            set,
        ]):
            model = Model.from_pretrained("pyannote/embedding", use_auth_token=HF_TOKEN)
        inference = Inference(model, window="whole")
        
        # Force CPU to avoid MPS errors
        model.to(torch.device("cpu"))
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return

    logger.info(f"Extracting embeddings for {len(segments)} segments...")
    embeddings = []
    valid_indices = []
    new_segments = []

    from pyannote.audio.core.io import Audio
    from pyannote.core import Segment
    audio_io = Audio(sample_rate=16000, mono="downmix")

    for i, seg in enumerate(segments):
        start = seg['start']
        end = seg['end']
        duration = end - start
        
        logger.info(f"Processing segment {i}: {duration:.2f}s ({start}-{end})")
        
        if duration < 0.01 or not seg['text'].strip():
            logger.warning(f"Discarding empty/zero-length segment {i}: {duration:.2f}s (Start: {start}, End: {end})")
            continue
            
        if duration < 0.2: # Label very short segments but keep them if they have text
            logger.warning(f"Labeling short segment {i} as UNKNOWN_SHORT: {duration:.2f}s")
            seg_copy = seg.copy()
            seg_copy['speaker'] = "UNKNOWN_SHORT"
            new_segments.append(seg_copy)
            continue

        try:
            # Extract crop
            waveform, sr = audio_io.crop(clip_path, Segment(start, end))
            # Inference expects (channel, time) but usually handles it. 
            # Inference with window="whole" expects a file path or a waveform?
            # It expects path or {"waveform": ..., "sample_rate": ...}
            
            # Force CPU to avoid MPS errors
            model.to(torch.device("cpu"))
            
            emb = inference({"waveform": waveform, "sample_rate": sr})
            embeddings.append(emb)
            
            # Add to new_segments and track its index
            new_segments.append(seg)
            valid_indices.append(len(new_segments) - 1)
            
            logger.info(f"Segment {i} success. Emb shape: {emb.data.shape if hasattr(emb, 'data') else 'unknown'}")
        except Exception as e:
            logger.error(f"Error processing segment {i}: {e}")
            # If failed, we still keep it but label as error? Or discard?
            # Let's keep it as UNKNOWN_ERROR so we don't lose text.
            seg_copy = seg.copy()
            seg_copy['speaker'] = "UNKNOWN_ERROR"
            new_segments.append(seg_copy)

    if not embeddings:
        logger.error("No embeddings generated.")
        return

    logger.info("Clustering embeddings...")
    X = np.vstack(embeddings)
    
    # Filter out NaNs
    # Create a boolean mask for valid (non-NaN) embeddings
    valid_embedding_mask = ~np.isnan(X).any(axis=1)
    X_clean = X[valid_embedding_mask]
    
    # Update the mapping to new_segments for only the clean embeddings
    # This list will contain the indices in `new_segments` corresponding to `X_clean`
    clean_embedding_to_new_segment_map = [
        valid_indices[i] for i, is_valid in enumerate(valid_embedding_mask) if is_valid
    ]
    
    if len(X_clean) == 0:
        logger.warning("No valid embeddings for clustering.")
        # If no valid embeddings, we still want to save the new_segments with UNKNOWN labels
        clip_entry['transcriptions']['mlx_whisper_turbo_seg_level'] = new_segments
        with open(MANIFEST_FILE, 'w') as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Saved segment-level diarization (with UNKNOWNs) to 'mlx_whisper_turbo_seg_level' in manifest.")
        return

    # Agglomerative Clustering
    # distance_threshold=0.5 is a good starting point for cosine distance
    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=0.5, 
        metric='cosine',
        linkage='average'
    )
    labels = clustering.fit_predict(X_clean)
    n_clusters = len(set(labels))
    logger.info(f"Found {n_clusters} clusters.")
    
    # Assign labels back to segments
    # Create a mapping from cluster_label -> display_label
    cluster_map = {}
    
    # Load known embeddings for identification
    DB_FILE = DATA_DIR / "speaker_embeddings.json"
    known_speakers = {}
    if DB_FILE.exists():
        try:
            with open(DB_FILE) as f:
                known_speakers = json.load(f)
            logger.info(f"Loaded {len(known_speakers)} known speakers for identification.")
        except Exception as e:
            logger.error(f"Failed to load speaker DB: {e}")

    from scipy.spatial.distance import cdist

    for label_id in range(n_clusters if n_clusters else max(labels) + 1):
        cluster_label = label_id
        
        # Get embeddings for this cluster
        cluster_indices = [i for i, x in enumerate(labels) if x == cluster_label]
        if not cluster_indices:
            continue
            
        cluster_embeddings = X[cluster_indices]
        centroid = np.mean(cluster_embeddings, axis=0).reshape(1, -1)
        
        # Identify
        best_name = f"SEG_SPK_{cluster_label:02d}"
        best_dist = 0.5 # Threshold
        
        if known_speakers:
            for name, stored_vectors in known_speakers.items():
                if not stored_vectors: continue
                # Compare with centroid of stored vectors
                # stored_vectors is list of lists
                stored_centroid = np.mean(stored_vectors, axis=0).reshape(1, -1)
                
                try:
                    dist = cdist(centroid, stored_centroid, metric='cosine')[0][0]
                except ValueError as e:
                    logger.warning(f"Dimension mismatch for {name}: {e}. Skipping.")
                    continue
                
                if dist < best_dist:
                    best_dist = dist
                    best_name = name
                    logger.info(f"Cluster {cluster_label} identified as {name} (dist: {dist:.4f})")
        
        cluster_map[cluster_label] = best_name

    for i, label in enumerate(labels):
        seg_idx = valid_indices[i]
        new_segments[seg_idx]['speaker'] = cluster_map[label]

    clip_data['transcriptions']['mlx_whisper_turbo_seg_level'] = new_segments
    
    with open(MANIFEST_FILE, 'w') as f:
        json.dump(manifest, f, indent=4)
        
    # Save embeddings to cache for manual correction/active learning
    cache_dir = DATA_DIR / "cache" / "embeddings"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    cache_data = {}
    # valid_indices maps from index in X_clean to index in new_segments
    # We want to map segment_index (in new_segments) -> embedding
    
    for i, seg_idx in enumerate(valid_indices):
        # X_clean[i] is the embedding for new_segments[seg_idx]
        cache_data[str(seg_idx)] = X_clean[i].tolist()
        
    cache_file = cache_dir / f"{clip_data['id']}.json"
    with open(cache_file, 'w') as f:
        json.dump(cache_data, f)
    logger.info(f"Cached embeddings for {len(cache_data)} segments to {cache_file}")

    logger.info(f"Saved segment-level diarization to 'mlx_whisper_turbo_seg_level' in manifest.")

if __name__ == "__main__":
    main()
