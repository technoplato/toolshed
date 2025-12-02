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

WHO:   Antigravity, User
       (Context: Created during "Plain Text Benchmark" task to standardize diarization testing)

WHEN:  December 2nd, 2025 at 12:00 p.m. EST
       [Last Modified Date]
       [Change Log:
        - December 2nd, 2025: Initial creation with Pyannote support
        - December 2nd, 2025: Added WeSpeaker placeholder and documentation]

WHERE: apps/speaker-diarization-benchmark/plain-text-benchmark/benchmark_baseline.py
       Not deployed yet.

WHY:   To provide a "text in, text out" benchmark for comparing different segmentation and diarization strategies
       and to easily view results in a single file.
"""

import os
# Set NUMBA_NUM_THREADS before any imports that might use numba (like librosa/wespeaker)
os.environ["NUMBA_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import argparse
import json
import logging
import time
import os
import sys
from pathlib import Path
import numpy as np
import torch
from scipy.spatial.distance import cosine
from sklearn.cluster import AgglomerativeClustering
from pyannote.audio import Model, Inference
from pyannote.audio.core.io import Audio
from pyannote.core import Segment as PyannoteSegment

# Add parent directory to sys.path to import transcribe
sys.path.append(str(Path(__file__).parent.parent))
try:
    from transcribe import transcribe, TranscriptionResult, Segment, Word
    from utils import get_git_info
except ImportError:
    # Fallback if running from a different context, though the sys.path append should work
    print("Error: Could not import 'transcribe' or 'utils' from parent directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HF_TOKEN = os.getenv("HF_TOKEN")

def main():
    parser = argparse.ArgumentParser(description="Benchmark baseline: Text In, Text Out.")
    parser.add_argument("clip_path", type=str, help="Path to the audio clip.")
    parser.add_argument("--threshold", type=float, default=0.5, help="Cosine distance threshold for segmentation.")
    parser.add_argument("--window", type=int, default=0, help="Number of context words on each side (0 = no window).")
    parser.add_argument("--cluster-threshold", type=float, default=0.5, help="Clustering distance threshold.")
    parser.add_argument("--id-threshold", type=float, default=0.4, help="Identification distance threshold.")
    parser.add_argument("--output-dir", type=str, default=".", help="Directory to save the output text file.")
    parser.add_argument("--append-to", type=str, help="Path to an existing file to append results to. Overrides --output-dir.")
    parser.add_argument("--workflow", type=str, default="pyannote", choices=["pyannote", "wespeaker", "pyannote_community", "pyannote_3.1", "segment_level"], help="Embedding/Diarization workflow to use.")
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
            
        if comparison_report:
            f.write("\n\n--- Comparison vs Gold Standard ---\n")
            f.write(comparison_report)

    logger.info(f"Benchmark report saved to {output_path}")
    print(f"\nResults saved to: {output_path}")


def run_pyannote_community_workflow(clip_path, all_words, args, model_name="pyannote/speaker-diarization-community-1"):
    stats = {'embedding_time': 0, 'segmentation_time': 0, 'clustering_time': 0}
    
    logger.info(f"Loading {model_name} pipeline...")
    try:
        from pyannote.audio import Pipeline
        import torch
        import omegaconf
        import pytorch_lightning
        import typing
        import collections
        from pyannote.audio.core.task import Specifications, Problem, Resolution
        import pyannote.audio.core.model

        # Define safe globals for loading
        safe_globals_list = [
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

        with torch.serialization.safe_globals(safe_globals_list):
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
        # Imports for safe globals (reusing list from pyannote workflow if needed, but here we use Model directly)
        # Actually, Model.from_pretrained also needs safe globals if weights_only=True default
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
        # Imports for safe globals
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
        model.to(torch.device("cpu")) 
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        return [], {'embedding_time': 0, 'segmentation_time': 0, 'clustering_time': 0}

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
            context_avg = np.mean(context_embeddings, axis=0)
            
            dist = cosine(context_avg, emb)
            
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
                avg_emb = np.mean(seg_embs, axis=0)
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

if __name__ == "__main__":
    main()
