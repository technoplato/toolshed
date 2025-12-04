import argparse
import json
import logging
import time
import os
from pathlib import Path
import numpy as np
import torch
from scipy.spatial.distance import cosine
from sklearn.cluster import AgglomerativeClustering
from pyannote.audio import Model, Inference
from pyannote.audio.core.io import Audio
from pyannote.core import Segment as PyannoteSegment

# Add current directory to sys.path to import transcribe
import sys
sys.path.append(str(Path(__file__).parent))
from transcribe import transcribe

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HF_TOKEN = os.getenv("HF_TOKEN")

def main():
    parser = argparse.ArgumentParser(description="Benchmark word-level speaker diarization.")
    parser.add_argument("clip_path", type=str, help="Path to the audio clip.")
    parser.add_argument("--threshold", type=float, default=0.5, help="Cosine distance threshold for segmentation.")
    parser.add_argument("--window", type=int, default=0, help="Number of context words on each side (0 = no window).")
    parser.add_argument("--save", action="store_true", help="Save results to manifest.json")
    parser.add_argument("--cluster-threshold", type=float, default=0.5, help="Clustering distance threshold.")
    parser.add_argument("--id-threshold", type=float, default=0.4, help="Identification distance threshold.")
    args = parser.parse_args()

    clip_path = Path(args.clip_path)
    if not clip_path.exists():
        logger.error(f"Clip not found: {clip_path}")
        return

    # 1. Transcription
    logger.info("Starting transcription...")
    
    # Cache setup
    cache_dir = Path("data/cache/transcriptions")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a safe filename for the model
    model_safe_name = "mlx-community_whisper-large-v3-turbo"
    cache_file = cache_dir / f"{clip_path.name}.{model_safe_name}.json"
    
    transcription_result = None
    
    if cache_file.exists():
        logger.info(f"Loading cached transcription from {cache_file}")
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                # Reconstruct objects
                from transcribe import TranscriptionResult, Segment, Word
                
                # We need to manually reconstruct because Pydantic's model_validate might need dicts
                # Assuming the JSON is the result of model_dump()
                
                # Helper to reconstruct words
                def dict_to_word(d):
                    return Word(**d)
                
                segments = []
                for s in data['segments']:
                    s_words = [dict_to_word(w) for w in s.get('words', [])]
                    segments.append(Segment(
                        start=s['start'],
                        end=s['end'],
                        text=s['text'],
                        words=s_words,
                        speaker=s.get('speaker', "UNKNOWN")
                    ))
                    
                transcription_result = TranscriptionResult(
                    text=data['text'],
                    segments=segments,
                    language=data.get('language', 'en')
                )
                transcription_time = 0 # Cached
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}. Re-running transcription.")
    
    if transcription_result is None:
        start_time = time.time()
        try:
            transcription_result = transcribe(str(clip_path))
            
            # Save to cache
            with open(cache_file, 'w') as f:
                json.dump(transcription_result.model_dump(), f, indent=2)
                
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return
        transcription_time = time.time() - start_time
        logger.info(f"Transcription complete in {transcription_time:.2f}s")
    else:
        logger.info("Transcription loaded from cache.")

    # Flatten words
    all_words = []
    for seg in transcription_result.segments:
        all_words.extend(seg.words)
    
    logger.info(f"Found {len(all_words)} words.")

    if not all_words:
        logger.warning("No words found in transcription.")
        return

    # 2. Embedding
    logger.info("Loading embedding model...")
    try:
        # Imports for safe globals
        import omegaconf
        import pytorch_lightning
        import typing
        import collections
        from pyannote.audio.core.task import Specifications, Problem, Resolution
        import pyannote.audio.core.model

        # Use pyannote/embedding
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
        model.to(torch.device("cpu")) # Force CPU to avoid MPS issues if any
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        return

    audio_io = Audio(sample_rate=16000, mono="downmix")
    
    logger.info(f"Embedding each word with window={args.window}...")
    start_time = time.time()
    
    word_embeddings = []
    valid_words = []

    for i, word in enumerate(all_words):
        duration = word.end - word.start
        if duration < 0.02: # Skip extremely short words
            continue
            
        try:
            # Determine window start/end
            w_start_idx = max(0, i - args.window)
            w_end_idx = min(len(all_words) - 1, i + args.window)
            
            start_time_sec = all_words[w_start_idx].start
            end_time_sec = all_words[w_end_idx].end
            
            # Crop audio for the window
            waveform, sr = audio_io.crop(clip_path, PyannoteSegment(start_time_sec, end_time_sec))
            
            # Embed
            emb = inference({"waveform": waveform, "sample_rate": sr})
            word_embeddings.append(emb)
            valid_words.append(word)
        except Exception as e:
            # logger.warning(f"Failed to embed word '{word.word}' ({word.start}-{word.end}): {e}")
            pass
            
    embedding_time = time.time() - start_time
    logger.info(f"Embedding complete in {embedding_time:.2f}s for {len(word_embeddings)} words.")

    # 3. Segmentation (Grouping)
    logger.info(f"Segmenting with threshold {args.threshold}...")
    start_time = time.time()
    
    segments = []
    if valid_words:
        current_segment_words = [valid_words[0]]
        # We'll keep track of the current segment's embeddings to calculate local average
        current_segment_embeddings = [word_embeddings[0]]
        current_segment_indices = [0]
        
        for i in range(1, len(valid_words)):
            word = valid_words[i]
            emb = word_embeddings[i]
            
            # Calculate average of LAST 3 words (or fewer)
            context_embeddings = current_segment_embeddings[-3:]
            context_avg = np.mean(context_embeddings, axis=0)
            
            # Calculate distance
            dist = cosine(context_avg, emb)
            
            # Debug print for first few
            if i < 10:
                logger.info(f"Word: {word.word}, Dist: {dist:.4f}")

            if dist > args.threshold:
                # New segment
                segments.append({
                    "start": current_segment_words[0].start,
                    "end": current_segment_words[-1].end,
                    "text": " ".join([w.word for w in current_segment_words]),
                    "word_count": len(current_segment_words),
                    "word_indices": current_segment_indices
                })
                
                # Reset
                current_segment_words = [word]
                current_segment_embeddings = [emb]
                current_segment_indices = [i]
            else:
                # Add to current
                current_segment_words.append(word)
                current_segment_embeddings.append(emb)
                current_segment_indices.append(i)
                
        # Add last segment
        segments.append({
            "start": current_segment_words[0].start,
            "end": current_segment_words[-1].end,
            "text": " ".join([w.word for w in current_segment_words]),
            "word_count": len(current_segment_words),
            "word_indices": current_segment_indices
        })

    segmentation_time = time.time() - start_time
    logger.info(f"Segmentation complete in {segmentation_time:.2f}s. Found {len(segments)} segments.")

    # 4. Clustering & Identification
    logger.info("Clustering and identifying speakers...")
    start_time = time.time()
    
    if segments:
        # Compute segment embeddings (average of word embeddings)
        X = []
        
        for seg in segments:
            indices = seg['word_indices']
            if indices:
                # Retrieve embeddings directly
                seg_embs = [word_embeddings[i] for i in indices]
                avg_emb = np.mean(seg_embs, axis=0)
                X.append(avg_emb)
            else:
                # Should not happen if logic is correct
                logger.warning(f"Segment with no words found: {seg}")
                X.append(np.zeros(512)) # Placeholder
        
        X = np.array(X)
        
        # Check for zero vectors
        norms = np.linalg.norm(X, axis=1)
        if np.any(norms == 0):
            logger.warning("Found zero vectors in segment embeddings. Removing them from clustering.")
            # We can't easily remove them without messing up indices, so let's add a tiny noise
            X[norms == 0] += 1e-9
        
        # Cluster
        logger.info(f"Clustering with threshold {args.cluster_threshold}...")
        from sklearn.cluster import AgglomerativeClustering
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=args.cluster_threshold,
            metric='cosine',
            linkage='average'
        )
        labels = clustering.fit_predict(X)
        
        # Identification
        # Load known speakers
        db_path = Path("data/speaker_embeddings.json")
        known_speakers = {}
        if db_path.exists():
            with open(db_path, 'r') as f:
                known_speakers = json.load(f)
        else:
            logger.warning(f"Speaker database not found at {db_path}")
        
        # Calculate centroids for each cluster
        cluster_centroids = {}
        for i in range(len(segments)):
            label = labels[i]
            if label not in cluster_centroids:
                cluster_centroids[label] = []
            cluster_centroids[label].append(X[i])
            
        final_labels = {}
        for label, embs in cluster_centroids.items():
            centroid = np.mean(embs, axis=0)
            
            # Compare to known
            min_dist = 2.0 # Cosine distance max is 2.0
            identity = f"SPEAKER_{label:02d}"
            
            for name, known_embs in known_speakers.items():
                # Compare to all known embeddings for this speaker and take min or avg?
                # Let's take avg of known embeddings to get a prototype
                if not known_embs: continue
                # known_embs is a list of lists (embeddings)
                known_proto = np.mean(known_embs, axis=0)
                
                d = cosine(centroid, known_proto)
                if d < min_dist:
                    min_dist = d
                    identity = name
            
            logger.info(f"Cluster {label} closest to {identity} (dist: {min_dist:.4f})")
            
            if min_dist < args.id_threshold: # Identification threshold
                final_labels[label] = identity
            else:
                final_labels[label] = f"SPEAKER_{label:02d}" # Keep anonymous if not close enough
        
        # Assign to segments
        for i in range(len(segments)):
            segments[i]['speaker'] = final_labels[labels[i]]

    clustering_time = time.time() - start_time
    logger.info(f"Clustering complete in {clustering_time:.2f}s")

    # 5. Report
    print("\n--- Benchmark Results ---")
    print(f"Clip: {clip_path.name}")
    print(f"Threshold: {args.threshold}")
    print(f"Window: {args.window}")
    print(f"Duration: {transcription_result.segments[-1].end if transcription_result.segments else 0:.2f}s")
    print(f"Transcription Time: {transcription_time:.2f}s")
    print(f"Embedding Time: {embedding_time:.2f}s")
    print(f"Segmentation Time: {segmentation_time:.2f}s")
    print(f"Clustering Time: {clustering_time:.2f}s")
    print(f"Total Time: {transcription_time + embedding_time + segmentation_time + clustering_time:.2f}s")
    print(f"Segments Found: {len(segments)}")
    
    print("\n--- Segments ---")
    for i, seg in enumerate(segments):
        print(f"[{seg['start']:.2f} - {seg['end']:.2f}] {seg.get('speaker', 'UNKNOWN')}: {seg['text']}")

    # 5. Save to Manifest
    if args.save:
        manifest_path = Path("data/clips/manifest.json")
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Find clip entry
            clip_entry = next((c for c in manifest if c['id'] == clip_path.name), None)
            if clip_entry:
                # Prepare segments for manifest
                manifest_segments = []
                for seg in segments:
                    manifest_segments.append({
                        "start": seg['start'],
                        "end": seg['end'],
                        "text": seg['text'],
                        "speaker": seg.get('speaker', "UNKNOWN")
                    })
                
                # Save under a specific key
                key = f"benchmark_tuned_t{args.threshold}_w{args.window}"
                clip_entry['transcriptions'][key] = manifest_segments
                
                # Add metadata
                from utils import get_git_info
                git_info = get_git_info()
                
                if 'transcription_metadata' not in clip_entry:
                    clip_entry['transcription_metadata'] = {}
                
                clip_entry['transcription_metadata'][key] = {
                    "pipeline": "benchmark_word_level.py",
                    "commit_hash": git_info['commit_hash'],
                    "is_dirty": git_info['is_dirty'],
                    "threshold": args.threshold,
                    "window": args.window,
                    "cluster_threshold": args.cluster_threshold,
                    "id_threshold": args.id_threshold,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                with open(manifest_path, 'w') as f:
                    json.dump(manifest, f, indent=4)
                print(f"\nSaved results to manifest under key '{key}'")
            else:
                logger.warning(f"Clip {clip_path.name} not found in manifest, cannot save.")
        else:
            logger.warning("Manifest not found, cannot save.")

if __name__ == "__main__":
    main()





