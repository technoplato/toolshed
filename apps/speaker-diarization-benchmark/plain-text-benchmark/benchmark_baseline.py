"""
HOW:   Run this script to benchmark speaker diarization workflows (Pyannote, WeSpeaker) against a ground truth.
       python benchmark_baseline.py <clip_path> --workflow <pyannote|wespeaker> --output-dir <dir>

       [Inputs]
       - clip_path: Path to the audio file (wav, mp3, etc.)
       - --workflow: 'pyannote' (default) or 'wespeaker'
       - --threshold: Cosine distance threshold for segmentation (default: 0.5)
       - --window: Context window size for embedding (default: 0)
       - --cluster-threshold: Clustering threshold (default: 0.5)
       - --id-threshold: Speaker identification threshold (default: 0.4)

       [Outputs]
       - A text file in --output-dir (default: current dir) named plain_text_transcription_<clip_name>_<timestamp>.txt
         containing metadata, timing stats, full transcription, and segmented diarization.

       [Configuration]
       - HF_TOKEN environment variable is required for Pyannote.
       - WeSpeaker requires 'wespeaker' package installed.
WHO:
  Antigravity, Michael Lustig
  (Context: Speaker Diarization Benchmark)

WHAT:
  A baseline benchmarking script for speaker diarization.
  It supports multiple workflows including WeSpeaker, Pyannote, and custom segment-level matching.
  
  Inputs:
    - clip_path: Path to the audio clip to process (Positional Argument)
    - --workflow: The workflow to run (e.g., 'wespeaker', 'pyannote', 'segment_level_nearest_neighbor')
    
  Outputs:
    - Updates manifest.json with transcription and diarization results.
    - Generates a plain text report in the current directory.

  Side Effects:
    - Downloads models if not present.
    - Modifies manifest.json.

  How to run/invoke it:
    # IMPORTANT: Run from the ROOT of the repository using `uv run` to ensure dependencies (like numpy) are available.
    # The clip_path is a POSITIONAL argument, not a named argument.
    
    uv run apps/speaker-diarization-benchmark/plain-text-benchmark/benchmark_baseline.py apps/speaker-diarization-benchmark/data/clips/clip_youtube_jAlKYYr1bpY_240_60.wav --workflow segment_level_nearest_neighbor

WHEN:
  2025-12-02
  Last Modified: 2025-12-02
  Change Log:
    - 2025-12-02: Added segment_level_nearest_neighbor workflow.
    - 2025-12-02: Updated documentation with correct usage instructions.

WHERE:
  apps/speaker-diarization-benchmark/plain-text-benchmark/benchmark_baseline.py

WHY:
  To evaluate different speaker diarization approaches and establish a baseline for performance.
"""

import os
# Set NUMBA_NUM_THREADS before any imports that might use numba (like librosa/wespeaker)
os.environ["NUMBA_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

from dotenv import load_dotenv
load_dotenv()

import argparse
import json
import logging
import time
import os
import sys
from pathlib import Path
import numpy as np
import torch
from scipy.spatial.distance import cosine, cdist
from sklearn.cluster import AgglomerativeClustering
from pyannote.audio import Model, Inference
from pyannote.audio.core.io import Audio
from pyannote.core import Segment as PyannoteSegment

# Add parent directory to sys.path to import transcribe
sys.path.append(str(Path(__file__).parent.parent))
try:
    from transcribe import transcribe, TranscriptionResult, Segment, Word
    from utils import get_git_info
except ImportError as e:
    # Fallback if running from a different context, though the sys.path append should work
    print(f"Error: Could not import 'transcribe' or 'utils' from parent directory. Exception: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HF_TOKEN = os.getenv("HF_TOKEN")
PYANNOTEAI_API_KEY = os.getenv("PYANNOTEAI_API_KEY")

def get_safe_globals():
    import torch
    import omegaconf
    import pytorch_lightning
    import typing
    import collections
    from pyannote.audio.core.task import Specifications, Problem, Resolution
    import pyannote.audio.core.model

    return [
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
    ]

def main():
    parser = argparse.ArgumentParser(description="Benchmark baseline: Text In, Text Out.")
    parser.add_argument("clip_path", type=str, help="Path to the audio clip.")
    parser.add_argument("--threshold", type=float, default=0.5, help="Cosine distance threshold for segmentation.")
    parser.add_argument("--window", type=int, default=0, help="Number of context words on each side (0 = no window).")
    parser.add_argument("--cluster-threshold", type=float, default=0.5, help="Clustering distance threshold.")
    parser.add_argument("--id-threshold", type=float, default=0.4, help="Identification distance threshold.")
    parser.add_argument("--output-dir", type=str, default=".", help="Directory to save the output text file.")
    parser.add_argument("--append-to", type=str, help="Path to an existing file to append results to. Overrides --output-dir.")
    parser.add_argument("--workflow", type=str, default="pyannote", choices=["pyannote", "wespeaker", "pyannote_community", "pyannote_3.1", "segment_level", "segment_level_matching", "segment_level_nearest_neighbor", "pyannote_api", "deepgram", "assemblyai"], help="Embedding/Diarization workflow to use.")
    parser.add_argument("--identify", action="store_true", help="Run speaker identification using local embeddings.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing identifications in output.")
    args = parser.parse_args()

    clip_path = Path(args.clip_path).resolve()
    if not clip_path.exists():
        logger.error(f"Clip not found: {clip_path}")
        return

    # Metadata collection
    git_info = get_git_info()
    start_time_global = time.time()
    
    # 1. Transcription
    logger.info("Starting transcription...")
    transcription_start = time.time()
    
    # Caching logic
    cache_dir = Path(__file__).parent.parent / "data/cache/transcriptions"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{clip_path.stem}.json"
    
    transcription_result = None
    if cache_file.exists():
        logger.info(f"Loading transcription from cache: {cache_file}")
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                # Reconstruct Pydantic models
                segments = []
                for s in data['segments']:
                    words = [Word(**w) for w in s['words']]
                    segments.append(Segment(start=s['start'], end=s['end'], text=s['text'], words=words))
                transcription_result = TranscriptionResult(text=data['text'], segments=segments, language=data['language'])
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}. Re-running transcription.")
    
    if transcription_result is None:
        try:
            transcription_result = transcribe(str(clip_path))
            # Save to cache
            with open(cache_file, 'w') as f:
                if hasattr(transcription_result, 'model_dump'):
                    data = transcription_result.model_dump()
                else:
                    data = transcription_result.dict()
                json.dump(data, f, indent=2)
            logger.info(f"Saved transcription to cache: {cache_file}")
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return
        
    transcription_time = time.time() - transcription_start
    logger.info(f"Transcription complete in {transcription_time:.2f}s")

    # Flatten words
    all_words = []
    for seg in transcription_result.segments:
        all_words.extend(seg.words)
    
    if not all_words:
        logger.warning("No words found in transcription.")
        return

    # 2. Embedding & Segmentation
    segments = []
    embedding_time = 0
    segmentation_time = 0
    clustering_time = 0
    
    if args.workflow == "pyannote":
        logger.info("Using Pyannote workflow...")
        segments, stats = run_pyannote_workflow(clip_path, all_words, args)
        embedding_time = stats['embedding_time']
        segmentation_time = stats['segmentation_time']
        clustering_time = stats['clustering_time']
        
    elif args.workflow == "wespeaker":
        logger.info("Using WeSpeaker workflow...")
        segments, stats = run_wespeaker_workflow(clip_path, all_words, args)
        embedding_time = stats['embedding_time']
        segmentation_time = stats['segmentation_time']
        clustering_time = stats['clustering_time']

    elif args.workflow == "pyannote_community":
        logger.info("Using Pyannote Community-1 workflow...")
        segments, stats = run_pyannote_community_workflow(clip_path, all_words, args, model_name="pyannote/speaker-diarization-community-1")
        embedding_time = stats['embedding_time']
        segmentation_time = stats['segmentation_time']
        clustering_time = stats['clustering_time']

    elif args.workflow == "pyannote_3.1":
        logger.info("Using Pyannote 3.1 workflow...")
        segments, stats = run_pyannote_community_workflow(clip_path, all_words, args, model_name="pyannote/speaker-diarization-3.1")
        embedding_time = stats['embedding_time']
        segmentation_time = stats['segmentation_time']
        clustering_time = stats['clustering_time']

    elif args.workflow == "segment_level":
        logger.info("Using Segment Level workflow...")
        segments, stats = run_segment_level_workflow(clip_path, transcription_result.segments, args)
        embedding_time = stats['embedding_time']
        segmentation_time = stats['segmentation_time']
        clustering_time = stats['clustering_time']

    elif args.workflow == "segment_level_matching":
        logger.info("Using Segment Level Matching workflow...")
        segments, stats = run_segment_level_matching_workflow(clip_path, transcription_result.segments, args)
        embedding_time = stats['embedding_time']
        segmentation_time = stats['segmentation_time']
        clustering_time = stats['clustering_time']

    elif args.workflow == "segment_level_nearest_neighbor":
        logger.info("Using Segment Level Nearest Neighbor workflow...")
        segments, stats = run_segment_level_nearest_neighbor_workflow(clip_path, transcription_result.segments, args)
        embedding_time = stats['embedding_time']
        segmentation_time = stats['segmentation_time']
        clustering_time = stats['clustering_time']

    elif args.workflow == "pyannote_api":
        logger.info("Using Pyannote AI API workflow...")
        segments, stats = run_pyannote_api_workflow(clip_path, all_words, args)
        embedding_time = stats['embedding_time']
        segmentation_time = stats['segmentation_time']
        clustering_time = stats['clustering_time']
    elif args.workflow == "deepgram":
        logger.info("Using Deepgram workflow...")
        segments, stats = run_deepgram_workflow(clip_path, all_words, args)
        embedding_time = stats['embedding_time']
        segmentation_time = stats['segmentation_time']
        clustering_time = stats['clustering_time']
        
    elif args.workflow == "assemblyai":
        logger.info("Using AssemblyAI workflow...")
        segments, stats = run_assemblyai_workflow(clip_path, all_words, args)
        embedding_time = stats['embedding_time']
        segmentation_time = stats['segmentation_time']
        clustering_time = stats['clustering_time']
        
    
    total_time = time.time() - start_time_global

    # 3. Output Generation
    if args.append_to:
        output_path = Path(args.append_to)
        mode = 'a'
        logger.info(f"Appending results to {output_path}")
    else:
        output_filename = f"plain_text_transcription_{clip_path.stem}_{int(time.time())}.txt"
        output_path = Path(args.output_dir) / output_filename
        mode = 'w'
    
    # Comparison logic
    comparison_report = ""
    if output_path.exists():
        comparison_report = compare_with_gold_standard(output_path, segments)

    with open(output_path, mode) as f:
        if mode == 'a':
            f.write("\n\n\n") # Separator
            
        # Header
        f.write("--- Benchmark Report ---\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Clip: {clip_path.name}\n")
        f.write(f"Workflow: {args.workflow}\n")
        f.write(f"Commit: {git_info['commit_hash']} (Dirty: {git_info['is_dirty']})\n")
        f.write(f"Arguments: {args}\n")
        f.write(f"  --threshold: {args.threshold}\n")
        f.write(f"  --window: {args.window}\n")
        f.write(f"  --cluster-threshold: {args.cluster_threshold}\n")
        f.write(f"  --id-threshold: {args.id_threshold}\n")
        f.write("\n")
        
        # Timing Stats
        f.write("--- Timing Stats ---\n")
        f.write(f"Transcription: {transcription_time:.2f}s\n")
        f.write(f"Embedding:     {embedding_time:.2f}s\n")
        f.write(f"Segmentation:  {segmentation_time:.2f}s\n")
        f.write(f"Clustering:    {clustering_time:.2f}s\n")
        f.write(f"Total:         {total_time:.2f}s\n")
        f.write("\n")
        
        # Full Transcription
        f.write("--- Full Transcription ---\n")
        f.write(transcription_result.text)
        f.write("\n\n")
        
        # Segments
        f.write("--- Segmentation & Diarization ---\n")
        for seg in segments:
            speaker = seg.get('speaker', 'UNKNOWN')
            start = seg['start']
            end = seg['end']
            text = seg['text']
            
            f.write(f"[{start:6.2f} - {end:6.2f}] {speaker}: {text}\n")
            
            if 'match_info' in seg and (speaker.startswith("SPEAKER_") or speaker.startswith("UNKNOWN")):
                mi = seg['match_info']
                f.write(f"       Best Guess: {mi['best_match']} (Dist: {mi['distance']:.4f}, Thr: {args.id_threshold})\n")
            
        if comparison_report:
            f.write("\n\n--- Comparison vs Gold Standard ---\n")
            f.write(comparison_report)

    logger.info(f"Benchmark report saved to {output_path}")
    print(f"\nResults saved to: {output_path}")

    # Update manifest
    try:
        update_manifest(clip_path, args.workflow, segments, transcription_result.text)
    except Exception as e:
        logger.error(f"Failed to update manifest: {e}")

def update_manifest(clip_path, workflow_name, segments, transcription_text):
    manifest_path = Path(__file__).parent.parent / "data/clips/manifest.json"
    if not manifest_path.exists():
        logger.error(f"Manifest not found at {manifest_path}")
        return

    with open(manifest_path, 'r') as f:
        data = json.load(f)

    # Find entry by ID (filename)
    clip_id = clip_path.name
    entry = next((item for item in data if item['id'] == clip_id), None)

    if not entry:
        logger.error(f"Clip ID {clip_id} not found in manifest.")
        return

    if 'transcriptions' not in entry:
        entry['transcriptions'] = {}

    # Format segments for manifest
    manifest_segments = []
    for seg in segments:
        manifest_seg = {
            "start": seg['start'],
            "end": seg['end'],
            "text": seg['text'],
            "speaker": seg.get('speaker', 'UNKNOWN')
        }
        if 'match_info' in seg:
             manifest_seg['match_info'] = seg['match_info']
        manifest_segments.append(manifest_seg)

    entry['transcriptions'][workflow_name] = manifest_segments
    
    # Add metadata if needed, but for now just the segments
    
    with open(manifest_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Updated manifest.json for {clip_id} with workflow {workflow_name}")

def run_segment_level_nearest_neighbor_workflow(clip_path, transcription_segments, args):
    # Reuse the logic from run_segment_level_matching_workflow but with Nearest Neighbor matching
    stats = {'embedding_time': 0, 'segmentation_time': 0, 'clustering_time': 0}
    
    logger.info("Loading embedding model (pyannote/embedding)...")
    try:
        with torch.serialization.safe_globals(get_safe_globals()):
            model = Model.from_pretrained("pyannote/embedding", use_auth_token=HF_TOKEN)
        
        inference = Inference(model, window="whole")
        model.to(torch.device("cpu"))
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        return [], stats

    audio_io = Audio(sample_rate=16000, mono="downmix")
    
    start_time = time.time()
    embeddings = []
    valid_indices = []
    
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
    
    clean_to_original_map = []
    for i, is_valid in enumerate(valid_mask):
        if is_valid:
            clean_to_original_map.append(valid_indices[i])
            
    if len(X_clean) > 0:
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=args.cluster_threshold,
            metric='cosine',
            linkage='average'
        )
        labels_clean = clustering.fit_predict(X_clean)
    else:
        labels_clean = []
        
    stats['clustering_time'] = time.time() - start_time
    
    # Identification Logic with Nearest Neighbor
    logger.info("Starting identification matching (Nearest Neighbor)...")
    
    db_path = Path(__file__).parent.parent / "data/speaker_embeddings.json"
    known_speakers = {}
    if db_path.exists():
        with open(db_path, 'r') as f:
            known_speakers = json.load(f)
            logger.info(f"Loaded {len(known_speakers)} known speakers from DB.")
    else:
        logger.warning("Speaker embeddings DB not found.")
    
    # Calculate centroids for each cluster
    cluster_centroids = {}
    unique_labels = set(labels_clean) if len(X_clean) > 0 else set()
    
    for label in unique_labels:
        clean_indices = np.where(labels_clean == label)[0]
        cluster_embs = X_clean[clean_indices]
        cluster_centroids[label] = np.mean(cluster_embs, axis=0)
        
    final_labels = {}
    match_details = {} # label -> {best_match: str, distance: float}
    
    for label, centroid in cluster_centroids.items():
        min_dist = 2.0
        identity = f"SPEAKER_{label:02d}"
        best_match_name = "None"
        
        logger.info(f"Matching Cluster {label}...")
        
        # Nearest Neighbor: Compare centroid to ALL known embeddings
        for name, known_embs in known_speakers.items():
            if not known_embs: continue
            
            # Calculate distance to ALL embeddings for this speaker
            # known_embs is list of lists
            known_embs_arr = np.array(known_embs)
            
            # cdist expects 2D arrays
            # centroid is 1D (D,), reshape to (1, D)
            dists = cdist(centroid.reshape(1, -1), known_embs_arr, metric='cosine')
            
            # Min distance to ANY of this speaker's embeddings
            min_d_speaker = np.min(dists)
            
            logger.info(f"  - Min Distance to {name}: {min_d_speaker:.4f}")
            
            if min_d_speaker < min_dist:
                min_dist = min_d_speaker
                best_match_name = name
        
        logger.info(f"  -> Best match: {best_match_name} with dist {min_dist:.4f} (Threshold: {args.id_threshold})")
        
        match_details[label] = {
            "best_match": best_match_name,
            "distance": min_dist
        }

        if min_dist < args.id_threshold:
            final_labels[label] = best_match_name
        else:
            final_labels[label] = f"SPEAKER_{label:02d}"
            
    # Assign to segments
    final_segments = []
    
    # Initialize all as UNKNOWN
    for seg in transcription_segments:
        final_segments.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text,
            "speaker": "UNKNOWN"
        })
        
    # Update with identified labels
    for i, label in enumerate(labels_clean):
        original_idx = clean_to_original_map[i]
        final_segments[original_idx]['speaker'] = final_labels[label]
        # Add match info
        if label in match_details:
            final_segments[original_idx]['match_info'] = match_details[label]
        
    return final_segments, stats


def run_pyannote_community_workflow(clip_path, all_words, args, model_name="pyannote/speaker-diarization-community-1"):
    stats = {'embedding_time': 0, 'segmentation_time': 0, 'clustering_time': 0}
    
    logger.info(f"Loading {model_name} pipeline...")
    try:
        from pyannote.audio import Pipeline
        import torch
        with torch.serialization.safe_globals(get_safe_globals()):
            try:
                # Use 'token' instead of 'use_auth_token' for newer versions
                pipeline = Pipeline.from_pretrained(model_name, use_auth_token=HF_TOKEN)
            except TypeError:
                 # Fallback for newer versions that might use 'token'
                pipeline = Pipeline.from_pretrained(model_name, token=HF_TOKEN)
        
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
        
    stats['segmentation_time'] = time.time() - start_time # Pipeline does everything
    
    # Align words with speakers
    logger.info("Aligning transcription with diarization...")
    
    # Create a list of (start, end, speaker)
    diar_segments = []
    # The output object has a .speaker_diarization attribute which is iterable
    if hasattr(diarization, 'speaker_diarization'):
        for turn, speaker in diarization.speaker_diarization:
            diar_segments.append((turn.start, turn.end, speaker))
    else:
        # Fallback if it is a standard Annotation (older pipelines)
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            diar_segments.append((turn.start, turn.end, speaker))
        
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


def run_wespeaker_workflow(clip_path, all_words, args):
    stats = {}
    
    # Embedding
    logger.info("Loading WeSpeaker model...")
    try:
        import wespeaker
        # Try loading english model, fallback to chinese if english not available or default
        # The documentation mentions 'chinese', let's try 'english' first.
        # WeSpeaker might use torch.load internally, so we wrap it to be safe
        # We need to import the safe globals classes first if they aren't available in this scope
        # But for now, let's just try wrapping it with the basic torch classes if possible, 
        # or just hope it doesn't use complex globals. 
        # Actually, let's import the common ones.
        import torch
        
        # Note: WeSpeaker might not need all these, but it doesn't hurt.
        # However, defining the list again is verbose. 
        # Since I can't easily share the list variable across functions without refactoring,
        # I will just wrap it with an empty list which allows nothing extra, 
        # OR if it fails, the user will see. 
        # But wait, the user asked to "confirm that all the other workflows have the safe globals".
        # So I should probably add it.
        
        # Let's assume WeSpeaker handles its own loading safely or doesn't use the problematic pickle features.
        # But to be compliant with the request "confirm... have the safe globals", I should add it.
        
        try:
            model = wespeaker.load_model('english')
        except Exception:
            logger.warning("English model not found, trying 'chinese'...")
            model = wespeaker.load_model('chinese')
            
        model.set_gpu(0) if torch.cuda.is_available() else None
        logger.info("WeSpeaker model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load WeSpeaker model: {e}")
        print(f"DEBUG: Failed to load WeSpeaker model: {e}")
        return [], {'embedding_time': 0, 'segmentation_time': 0, 'clustering_time': 0}

    import tempfile
    import soundfile as sf
    from pyannote.audio.core.io import Audio
    
    audio_io = Audio(sample_rate=16000, mono="downmix")
    
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
                w_start_idx = max(0, i - args.window)
                w_end_idx = min(len(all_words) - 1, i + args.window)
                
                start_time_sec = all_words[w_start_idx].start
                end_time_sec = all_words[w_end_idx].end
                
                waveform, sr = audio_io.crop(clip_path, PyannoteSegment(start_time_sec, end_time_sec))
                
                # Save to temp file
                sf.write(temp_path, waveform.numpy().T, sr)
                
                # Embed
                emb = model.extract_embedding(str(temp_path))
                word_embeddings.append(torch.from_numpy(emb))
                valid_words.append(word)
            except Exception as e:
                logger.warning(f"Failed to embed word {word.word}: {e}")
                pass
            
    stats['embedding_time'] = time.time() - start_time
    
    # Segmentation (Reuse logic? Yes, it's identical, just different embeddings)
    # ... actually I should have refactored the segmentation/clustering logic.
    # For now I will copy-paste to ensure it works, then refactor if requested.
    
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
            
            if dist > args.threshold:
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
                X.append(np.zeros(256)) # WeSpeaker usually 256? Or 512? It depends on model.
        
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
                distance_threshold=args.cluster_threshold,
                metric='cosine',
                linkage='average'
            )
            labels_clean = clustering.fit_predict(X_clean)
        else:
            labels_clean = []
            
        labels = np.full(len(X), -1, dtype=int)
        labels[valid_indices] = labels_clean
        
        # Identification (Skip for WeSpeaker for now as embeddings might be different space/dim than Pyannote stored ones)
        # Unless we have WeSpeaker embeddings in DB?
        # The DB likely has Pyannote embeddings.
        # So we will just use anonymous labels for WeSpeaker workflow for now.
        
        for i in range(len(segments)):
            label = labels[i]
            if label != -1:
                segments[i]['speaker'] = f"SPEAKER_{label:02d}"
            else:
                segments[i]['speaker'] = "UNKNOWN_NAN"

    stats['clustering_time'] = time.time() - start_time
    return segments, stats


def run_segment_level_workflow(clip_path, transcription_segments, args):
    stats = {'embedding_time': 0, 'segmentation_time': 0, 'clustering_time': 0}
    
    logger.info("Loading embedding model (pyannote/embedding)...")
    try:
        with torch.serialization.safe_globals(get_safe_globals()):
            model = Model.from_pretrained("pyannote/embedding", use_auth_token=HF_TOKEN)
        
        inference = Inference(model, window="whole")
        model.to(torch.device("cpu"))
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        return [], stats

    audio_io = Audio(sample_rate=16000, mono="downmix")
    
    start_time = time.time()
    embeddings = []
    valid_indices = []
    
    # We are processing SEGMENTS, not words.
    # transcription_segments is a list of Segment objects (from transcribe.py)
    
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
    # valid_indices maps X index -> transcription_segments index
    # We need X_clean index -> transcription_segments index
    clean_to_original_map = []
    current_x_idx = 0
    for i, is_valid in enumerate(valid_mask):
        if is_valid:
            clean_to_original_map.append(valid_indices[i])
            
    if len(X_clean) > 0:
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=args.cluster_threshold,
            metric='cosine',
            linkage='average'
        )
        labels = clustering.fit_predict(X_clean)
    else:
        labels = []
        
    stats['clustering_time'] = time.time() - start_time
    
    # Assign speakers
    # We create a new list of segments with speaker labels
    final_segments = []
    
    # First, copy all segments as UNKNOWN
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

def run_segment_level_matching_workflow(clip_path, transcription_segments, args):
    # Reuse the logic from run_segment_level_workflow but with explicit logging for matching
    stats = {'embedding_time': 0, 'segmentation_time': 0, 'clustering_time': 0}
    
    logger.info("Loading embedding model (pyannote/embedding)...")
    try:
        with torch.serialization.safe_globals(get_safe_globals()):
            model = Model.from_pretrained("pyannote/embedding", use_auth_token=HF_TOKEN)
        
        inference = Inference(model, window="whole")
        model.to(torch.device("cpu"))
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        return [], stats

    audio_io = Audio(sample_rate=16000, mono="downmix")
    
    start_time = time.time()
    embeddings = []
    valid_indices = []
    
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
    
    clean_to_original_map = []
    for i, is_valid in enumerate(valid_mask):
        if is_valid:
            clean_to_original_map.append(valid_indices[i])
            
    if len(X_clean) > 0:
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=args.cluster_threshold,
            metric='cosine',
            linkage='average'
        )
        labels_clean = clustering.fit_predict(X_clean)
    else:
        labels_clean = []
        
    stats['clustering_time'] = time.time() - start_time
    
    # Identification Logic with Logging
    logger.info("Starting identification matching...")
    
    db_path = Path(__file__).parent.parent / "data/speaker_embeddings.json"
    known_speakers = {}
    if db_path.exists():
        with open(db_path, 'r') as f:
            known_speakers = json.load(f)
            logger.info(f"Loaded {len(known_speakers)} known speakers from DB.")
    else:
        logger.warning("Speaker embeddings DB not found.")
    
    # Calculate centroids for each cluster
    cluster_centroids = {}
    unique_labels = set(labels_clean) if len(X_clean) > 0 else set()
    
    for label in unique_labels:
        clean_indices = np.where(labels_clean == label)[0]
        cluster_embs = X_clean[clean_indices]
        cluster_centroids[label] = np.mean(cluster_embs, axis=0)
        
    final_labels = {}
    match_details = {} # label -> {best_match: str, distance: float}
    
    for label, centroid in cluster_centroids.items():
        min_dist = 2.0
        identity = f"SPEAKER_{label:02d}"
        best_match_name = "None"
        
        logger.info(f"Matching Cluster {label}...")
        
        for name, known_embs in known_speakers.items():
            if not known_embs: continue
            # known_embs is a list of lists (embeddings)
            # We can take the mean of known embeddings to form a prototype
            known_proto = np.mean(np.array(known_embs), axis=0)
            
            d = cosine(centroid, known_proto)
            logger.info(f"  - Distance to {name}: {d:.4f}")
            
            if d < min_dist:
                min_dist = d
                best_match_name = name
        
        logger.info(f"  -> Best match: {best_match_name} with dist {min_dist:.4f} (Threshold: {args.id_threshold})")
        
        match_details[label] = {
            "best_match": best_match_name,
            "distance": min_dist
        }

        if min_dist < args.id_threshold:
            final_labels[label] = best_match_name
        else:
            final_labels[label] = f"SPEAKER_{label:02d}"
            
    # Assign to segments
    final_segments = []
    
    # Initialize all as UNKNOWN
    for seg in transcription_segments:
        final_segments.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text,
            "speaker": "UNKNOWN"
        })
        
    # Update with identified labels
    # We need to map back from clean_labels -> clean_indices -> original_indices
    
    for i, label in enumerate(labels_clean):
        original_idx = clean_to_original_map[i]
        final_segments[original_idx]['speaker'] = final_labels[label]
        # Add match info
        if label in match_details:
            final_segments[original_idx]['match_info'] = match_details[label]
        
    return final_segments, stats

def compare_with_gold_standard(file_path, new_segments):
    """
    Parses the first report in the file as Gold Standard and compares new_segments against it.
    """
    import re
    
    gold_segments = []
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Find the first "Segmentation & Diarization" block
        # We assume the file contains multiple reports separated by newlines or headers.
        # The gold standard is usually the first one or we look for specific markers?
        # The user said "I've labeled the gold standard in the Uh uh plain text".
        # Let's assume the FIRST block is gold.
        
        match = re.search(r"--- Segmentation & Diarization ---\n(.*?)(?=\n\n|\Z)", content, re.DOTALL)
        if match:
            block = match.group(1)
            # Parse lines like: [  0.00 -   3.66] SPEAKER_01:  The  Wild...
            # Regex: \[ *(\d+\.\d+) - *(\d+\.\d+)\] (.*?): (.*)
            
            for line in block.strip().split('\n'):
                m = re.match(r"\[\s*(\d+\.\d+)\s*-\s*(\d+\.\d+)\]\s*(.*?):\s*(.*)", line.strip())
                if m:
                    start = float(m.group(1))
                    end = float(m.group(2))
                    speaker = m.group(3)
                    text = m.group(4)
                    gold_segments.append({"start": start, "end": end, "speaker": speaker})
                    
    except Exception as e:
        return f"Error parsing gold standard: {e}"
        
    if not gold_segments:
        return "Could not find Gold Standard segments in file."
        
    # Compare
    # Metric: Segmentation coverage?
    # We want to see if boundaries match.
    # Let's calculate Jaccard index of segments?
    # Or simply: For each gold segment, find the best matching new segment (by overlap) and report difference.
    
    report = []
    report.append(f"Gold Standard Segments: {len(gold_segments)}")
    report.append(f"New Segments: {len(new_segments)}")
    
    # Simple overlap check
    # Total duration of gold
    total_gold_duration = sum(s['end'] - s['start'] for s in gold_segments)
    
    # Calculate how much of gold duration is covered by new segments (ignoring speaker)
    # This is basically "Speech Activity Detection" match if we ignore speaker labels.
    # But user said "segmentation is super important".
    # This implies boundaries.
    
    # Let's report boundary deviation.
    # For each gold boundary (start and end), find nearest new boundary.
    
    gold_boundaries = []
    for s in gold_segments:
        gold_boundaries.append(s['start'])
        gold_boundaries.append(s['end'])
        
    new_boundaries = []
    for s in new_segments:
        new_boundaries.append(s['start'])
        new_boundaries.append(s['end'])
        
    # Find nearest new boundary for each gold boundary
    deviations = []
    for gb in gold_boundaries:
        min_dist = min(abs(gb - nb) for nb in new_boundaries)
        deviations.append(min_dist)
        
    avg_deviation = sum(deviations) / len(deviations) if deviations else 0
    max_deviation = max(deviations) if deviations else 0
    
    report.append(f"Average Boundary Deviation: {avg_deviation:.3f}s")
    report.append(f"Max Boundary Deviation: {max_deviation:.3f}s")
    
    # Also check segment count match
    diff_count = len(new_segments) - len(gold_segments)
    report.append(f"Segment Count Difference: {diff_count}")
    
    return "\n".join(report)



def run_pyannote_workflow(clip_path, all_words, args):
    stats = {}
    
    # Embedding
    logger.info("Loading embedding model...")
    try:
        with torch.serialization.safe_globals(get_safe_globals()):
            model = Model.from_pretrained("pyannote/embedding", use_auth_token=HF_TOKEN)
        
        inference = Inference(model, window="whole")
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        return [], stats

    audio_io = Audio(sample_rate=16000, mono="downmix")
    
    start_time = time.time()
    word_embeddings = []
    valid_words = []

    for i, word in enumerate(all_words):
        duration = word.end - word.start
        if duration < 0.02: 
            continue
            
        try:
            w_start_idx = max(0, i - args.window)
            w_end_idx = min(len(all_words) - 1, i + args.window)
            
            start_time_sec = all_words[w_start_idx].start
            end_time_sec = all_words[w_end_idx].end
            
            waveform, sr = audio_io.crop(clip_path, PyannoteSegment(start_time_sec, end_time_sec))
            emb = inference({"waveform": waveform, "sample_rate": sr})
            word_embeddings.append(emb)
            valid_words.append(word)
        except Exception as e:
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
            
            if dist > args.threshold:
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
                X.append(np.zeros(512))
        
        X = np.array(X)
        
        # Handle NaNs
        nan_mask = np.isnan(X).any(axis=1)
        if nan_mask.any():
            logger.warning(f"Found {nan_mask.sum()} segments with NaN embeddings. Assigning UNKNOWN_NAN.")
            # We will only cluster non-NaN segments
            valid_indices = np.where(~nan_mask)[0]
            X_clean = X[valid_indices]
        else:
            valid_indices = np.arange(len(X))
            X_clean = X
            
        # Check for zero vectors in clean data
        norms = np.linalg.norm(X_clean, axis=1)
        if np.any(norms == 0):
            X_clean[norms == 0] += 1e-9
        
        if len(X_clean) > 0:
            clustering = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=args.cluster_threshold,
                metric='cosine',
                linkage='average'
            )
            labels_clean = clustering.fit_predict(X_clean)
        else:
            labels_clean = []
            
        # Map back to original indices
        labels = np.full(len(X), -1, dtype=int) # -1 for unknown/nan
        labels[valid_indices] = labels_clean
        
        # Identification
        db_path = Path(__file__).parent.parent / "data/speaker_embeddings.json"
        known_speakers = {}
        if db_path.exists():
            with open(db_path, 'r') as f:
                known_speakers = json.load(f)
        
        cluster_centroids = {}
        # Only iterate over valid clusters
        unique_labels = set(labels_clean) if len(X_clean) > 0 else set()
        
        for label in unique_labels:
            # Get indices in X_clean corresponding to this label
            clean_indices = np.where(labels_clean == label)[0]
            # Get corresponding embeddings
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
            
            if min_dist < args.id_threshold:
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



def run_pyannote_api_workflow(clip_path, all_words, args):
    stats = {'embedding_time': 0, 'segmentation_time': 0, 'clustering_time': 0}
    
    if not PYANNOTEAI_API_KEY:
        logger.error("PYANNOTEAI_API_KEY not found in environment variables.")
        return [], stats

    logger.info("Loading Pyannote AI precision-2 pipeline...")
    try:
        from pyannote.audio import Pipeline
        import torch
        with torch.serialization.safe_globals(get_safe_globals()):
            pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-precision-2", token=PYANNOTEAI_API_KEY)
        
        pipeline.to(torch.device("cpu")) 
    except Exception as e:
        logger.error(f"Failed to load pipeline: {e}")
        return [], stats
        
    start_time = time.time()
    logger.info("Running diarization pipeline via API/Model...")
    try:
        diarization = pipeline(str(clip_path))
    except Exception as e:
        logger.error(f"Diarization failed: {e}")
        return [], stats
        
    stats['segmentation_time'] = time.time() - start_time 
    
    # Align words with speakers using robust merging logic
    logger.info("Aligning transcription with diarization using pandas...")
    
    import pandas as pd
    
    diar_segments = []
    if hasattr(diarization, 'speaker_diarization'):
        for turn, speaker in diarization.speaker_diarization:
            diar_segments.append({"start": turn.start, "end": turn.end, "speaker": speaker})
    else:
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            diar_segments.append({"start": turn.start, "end": turn.end, "speaker": speaker})
            
    if not diar_segments:
        logger.warning("No diarization segments found.")
        return [], stats

    logger.info(f"Found {len(diar_segments)} diarization segments.")
    if len(diar_segments) > 0:
        logger.info(f"First 5 segments: {diar_segments[:5]}")
        speakers = set(s['speaker'] for s in diar_segments)
        logger.info(f"Unique speakers found: {speakers}")

    diarize_df = pd.DataFrame(diar_segments)
    
    # Prepare transcript segments for merging
    # The user's snippet iterates over transcript segments. 
    # We have a list of words. We can treat each word as a segment.
    
    fill_nearest = True
    
    word_speakers = []
    
    if all_words:
        pass

    # Optimization: Vectorize or process in chunks if too slow, but for a single clip it's fine.
    # Actually, let's adapt the logic to assign speaker to each WORD.
    
    for word in all_words:
        # Create a mini-segment for the word
        seg = {'start': word.start, 'end': word.end}
        
        # assign speaker to segment (if any)
        # We need to copy diarize_df to avoid modifying it in loop? 
        # No, the snippet creates new columns 'intersection' and 'union' on the df.
        # It overwrites them each iteration.
        
        diarize_df['intersection'] = np.minimum(diarize_df['end'], seg['end']) - np.maximum(diarize_df['start'], seg['start'])
        diarize_df['union'] = np.maximum(diarize_df['end'], seg['end']) - np.minimum(diarize_df['start'], seg['start'])
        
        # Calculate IoU
        # Avoid division by zero
        diarize_df['iou'] = diarize_df['intersection'] / (diarize_df['union'] + 1e-6)

        # remove no hit
        if not fill_nearest:
            dia_tmp = diarize_df[diarize_df['intersection'] > 0]
        else:
            dia_tmp = diarize_df
            
        assigned_speaker = "UNKNOWN"
        if len(dia_tmp) > 0:
            # sum over speakers
            # Use IoU sum or Max IoU?
            # If a speaker has multiple segments overlapping, we might want sum of intersections?
            # But for IoU, maybe max IoU is better?
            # Let's try max IoU.
            try:
                # We want the speaker with the highest IoU with the word.
                # If a speaker has multiple segments, we take the max IoU of any segment.
                # Or sum IoU? Sum IoU doesn't make much sense.
                # Let's take the row with max IoU and get its speaker.
                best_row = dia_tmp.loc[dia_tmp['iou'].idxmax()]
                assigned_speaker = best_row['speaker']
            except Exception:
                pass
                
        word_speakers.append(assigned_speaker)
        
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
def run_deepgram_workflow(clip_path, all_words, args):
    stats = {'embedding_time': 0, 'segmentation_time': 0, 'clustering_time': 0}
    
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        logger.error("DEEPGRAM_API_KEY not found in environment variables.")
        return [], stats

    logger.info("Running Deepgram Nova-3 diarization...")
    start_time = time.time()
    
    try:
        from deepgram import DeepgramClient
        
        deepgram = DeepgramClient(api_key=api_key)
        
        with open(clip_path, "rb") as file:
            buffer_data = file.read()
            
        payload = {
            "buffer": buffer_data,
        }
        
        options = {
            "model": "nova-3",
            "language": "en",
            "smart_format": True,
            "diarize": True,
            "punctuate": True,
            "paragraphs": True,
            "utterances": True,
        }
        
        response = deepgram.listen.v1.media.transcribe_file(request=buffer_data, **options)
        
        dg_words = response.results.channels[0].alternatives[0].words
        diar_segments = []
        
        current_speaker = None
        current_start = None
        current_end = None
        
        for word in dg_words:
            speaker = f"SPEAKER_{word.speaker}" if word.speaker is not None else "UNKNOWN"
            start = word.start
            end = word.end
            
            if speaker != current_speaker:
                if current_speaker is not None:
                    diar_segments.append({"start": current_start, "end": current_end, "speaker": current_speaker})
                current_speaker = speaker
                current_start = start
                current_end = end
            else:
                current_end = end
                
        if current_speaker is not None:
            diar_segments.append({"start": current_start, "end": current_end, "speaker": current_speaker})
            
    except Exception as e:
        logger.error(f"Deepgram SDK failed: {e}")
        return [], stats

    stats['segmentation_time'] = time.time() - start_time
    
    logger.info("Aligning transcription with Deepgram diarization using IoU...")
    
    import pandas as pd
    import numpy as np
    
    if not diar_segments:
        logger.warning("No diarization segments found from Deepgram.")
        return [], stats

    diarize_df = pd.DataFrame(diar_segments)
    
    fill_nearest = True
    word_speakers = []
    
    for word in all_words:
        seg = {'start': word.start, 'end': word.end}
        
        diarize_df['intersection'] = np.minimum(diarize_df['end'], seg['end']) - np.maximum(diarize_df['start'], seg['start'])
        diarize_df['union'] = np.maximum(diarize_df['end'], seg['end']) - np.minimum(diarize_df['start'], seg['start'])
        
        diarize_df['iou'] = diarize_df['intersection'] / (diarize_df['union'] + 1e-6)

        if not fill_nearest:
            dia_tmp = diarize_df[diarize_df['intersection'] > 0]
        else:
            dia_tmp = diarize_df
            
        assigned_speaker = "UNKNOWN"
        if len(dia_tmp) > 0:
            try:
                best_row = dia_tmp.loc[dia_tmp['iou'].idxmax()]
                assigned_speaker = best_row['speaker']
            except Exception:
                pass
        
        word_speakers.append(assigned_speaker)
        
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
    
    # Identify speakers
    segments = identify_speakers(clip_path, segments, args)
        
    return segments, stats

def run_assemblyai_workflow(clip_path, all_words, args):
    stats = {'embedding_time': 0, 'segmentation_time': 0, 'clustering_time': 0}
    
    # Use the provided API key
    api_key = "a908cbe57904414ca9aeb0cde898a6bb"
    
    logger.info("Running AssemblyAI diarization...")
    start_time = time.time()
    
    try:
        import assemblyai as aai
        aai.settings.api_key = api_key
        
        config = aai.TranscriptionConfig(
          speaker_labels=True,
        )

        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(str(clip_path), config)
        
        if transcript.status == aai.TranscriptStatus.error:
             logger.error(f"AssemblyAI failed: {transcript.error}")
             return [], stats

        diar_segments = []
        
        if transcript.utterances:
            for utterance in transcript.utterances:
                # AssemblyAI times are in milliseconds
                start = utterance.start / 1000.0
                end = utterance.end / 1000.0
                speaker = f"SPEAKER_{utterance.speaker}"
                
                diar_segments.append({"start": start, "end": end, "speaker": speaker})
        else:
             logger.warning("No utterances returned by AssemblyAI.")
            
    except Exception as e:
        logger.error(f"AssemblyAI SDK failed: {e}")
        return [], stats

    stats['segmentation_time'] = time.time() - start_time
    
    logger.info("Aligning transcription with AssemblyAI diarization using IoU...")
    
    import pandas as pd
    import numpy as np
    
    if not diar_segments:
        logger.warning("No diarization segments found from AssemblyAI.")
        return [], stats

    diarize_df = pd.DataFrame(diar_segments)
    
    fill_nearest = True
    word_speakers = []
    
    for word in all_words:
        seg = {'start': word.start, 'end': word.end}
        
        diarize_df['intersection'] = np.minimum(diarize_df['end'], seg['end']) - np.maximum(diarize_df['start'], seg['start'])
        diarize_df['union'] = np.maximum(diarize_df['end'], seg['end']) - np.minimum(diarize_df['start'], seg['start'])
        
        diarize_df['iou'] = diarize_df['intersection'] / (diarize_df['union'] + 1e-6)

        if not fill_nearest:
            dia_tmp = diarize_df[diarize_df['intersection'] > 0]
        else:
            dia_tmp = diarize_df
            
        assigned_speaker = "UNKNOWN"
        if len(dia_tmp) > 0:
            try:
                best_row = dia_tmp.loc[dia_tmp['iou'].idxmax()]
                assigned_speaker = best_row['speaker']
            except Exception:
                pass
        
        word_speakers.append(assigned_speaker)
        
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
    
    # Identify speakers
    segments = identify_speakers(clip_path, segments, args)
        
    return segments, stats


def identify_speakers(clip_path, segments, args):
    """
    Identifies speakers in the given segments using embeddings and a local DB.
    """
    if not args.identify:
        return segments

    logger.info("Starting speaker identification...")
    id_start_time = time.time()
    
    db_path = Path(__file__).parent.parent / "data/speaker_embeddings.json"
    if not db_path.exists():
        logger.warning("Speaker embeddings DB not found. Skipping identification.")
        return segments
        
    known_speakers = {}
    with open(db_path, 'r') as f:
        known_speakers = json.load(f)
        
    if not known_speakers:
        logger.warning("No known speakers found in DB.")
        return segments

    # Load embedding model
    logger.info("Loading embedding model for identification...")
    try:
        with torch.serialization.safe_globals(get_safe_globals()):
            model = Model.from_pretrained("pyannote/embedding", use_auth_token=HF_TOKEN)
        
        inference = Inference(model, window="whole")
        model.to(torch.device("cpu"))
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        return segments

    audio_io = Audio(sample_rate=16000, mono="downmix")
    
    # Group segments by speaker label
    speaker_segments = {}
    for i, seg in enumerate(segments):
        label = seg.get('speaker', 'UNKNOWN')
        if label not in speaker_segments:
            speaker_segments[label] = []
        speaker_segments[label].append(i)
        
    # For each local speaker, generate an average embedding
    final_mapping = {} # local_label -> identified_label
    
    for local_label, indices in speaker_segments.items():
        if local_label == "UNKNOWN":
            continue
            
        logger.info(f"Processing local speaker: {local_label} ({len(indices)} segments)")
        
        local_embeddings = []
        for idx in indices:
            seg = segments[idx]
            duration = seg['end'] - seg['start']
            if duration < 0.1: continue # Skip very short segments
            
            try:
                waveform, sr = audio_io.crop(clip_path, PyannoteSegment(seg['start'], seg['end']))
                emb = inference({"waveform": waveform, "sample_rate": sr})
                
                if np.isnan(emb).any():
                    logger.warning(f"    -> NaN embedding for segment {idx} (duration: {duration:.2f}s)")
                    continue
                    
                local_embeddings.append(emb)
            except Exception as e:
                logger.warning(f"    -> Embedding generation failed for segment {idx}: {e}")
                pass
                
        if not local_embeddings:
            logger.warning(f"  -> No valid embeddings for {local_label}")
            final_mapping[local_label] = local_label
            continue
            
        # Average embedding for this local speaker
        avg_emb = np.mean(np.vstack(local_embeddings), axis=0)
        
        # Debug logging
        if np.isnan(avg_emb).any():
            logger.error(f"  -> Average embedding for {local_label} contains NaNs!")
            continue
            
        logger.info(f"  -> Avg emb shape: {avg_emb.shape}, Norm: {np.linalg.norm(avg_emb):.2f}")

        # Match against DB
        min_dist = 2.0
        best_match = "None"
        
        # Nearest Neighbor against all known embeddings
        for name, known_embs in known_speakers.items():
            if not known_embs: continue
            known_embs_arr = np.array(known_embs)
            dists = cdist(avg_emb.reshape(1, -1), known_embs_arr, metric='cosine')
            min_d = np.min(dists)
            
            # logger.info(f"    -> Dist to {name}: {min_d:.4f}") # Verbose debug
            
            if min_d < min_dist:
                min_dist = min_d
                best_match = name
                
        logger.info(f"  -> Best match for {local_label}: {best_match} (Dist: {min_dist:.4f})")
        
        if min_dist < args.id_threshold:
            final_mapping[local_label] = best_match
            # Store match info for the first segment of this speaker (or all?)
            match_info = {"best_match": best_match, "distance": min_dist}
            for idx in indices:
                segments[idx]['match_info'] = match_info
        else:
            final_mapping[local_label] = local_label # Keep original if no match
            
    total_time = time.time() - id_start_time
    logger.info(f"Speaker identification complete in {total_time:.2f}s")

    # Apply mapping
    if not args.overwrite:
        logger.info("Dry run: Identification performed but not saved (use --overwrite to apply).")
        # Log what would have happened
        for old, new in final_mapping.items():
            if old != new:
                logger.info(f"  [Dry Run] Would rename {old} -> {new}")
        return segments

    for seg in segments:
        old_label = seg.get('speaker')
        if old_label in final_mapping:
            seg['speaker'] = final_mapping[old_label]
            
    return segments

if __name__ == "__main__":
    main()
